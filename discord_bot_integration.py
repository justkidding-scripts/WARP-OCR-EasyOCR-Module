#!/usr/bin/env python3
"""
Discord Bot Integration for Real-time OCR Feedback
Provides multiple ways to send OCR results back to Discord during screenshare sessions

Features:
- Discord bot with commands
- Webhook integration
- WebSocket for real-time communication
- Rate limiting and spam protection
- Rich embed formatting
"""

import discord
from discord.ext import commands, tasks
import aiohttp
import asyncio
import json
import time
import logging
from datetime import datetime, timedelta
import re
from collections import deque
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO)

class DiscordOCRBot:
    """Discord bot for OCR feedback integration"""
    
    def __init__(self, token=None, webhook_url=None):
        self.token = token
        self.webhook_url = webhook_url
        
        # Bot configuration
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        
        self.bot = commands.Bot(command_prefix='!ocr ', intents=intents)
        self.setup_bot_commands()
        
        # Rate limiting and spam protection
        self.message_history = deque(maxlen=100)
        self.last_message_hash = None
        self.rate_limit_window = 60  # seconds
        self.max_messages_per_window = 10
        
        # Active channels for OCR feedback
        self.active_channels = set()
        self.ocr_sessions = {}  # channel_id -> session_info
        
    def setup_bot_commands(self):
        """Setup Discord bot commands"""
        
        @self.bot.event
        async def on_ready():
            logging.info(f'OCR Bot logged in as {self.bot.user}')
            await self.bot.change_presence(
                activity=discord.Activity(
                    type=discord.ActivityType.watching,
                    name="for screenshare OCR requests"
                )
            )
        
        @self.bot.command(name='start')
        async def start_ocr(ctx):
            """Start OCR monitoring for this channel"""
            channel_id = ctx.channel.id
            self.active_channels.add(channel_id)
            
            self.ocr_sessions[channel_id] = {
                'start_time': datetime.now(),
                'message_count': 0,
                'user_id': ctx.author.id,
                'username': ctx.author.display_name
            }
            
            embed = discord.Embed(
                title="🔍 OCR Monitoring Started",
                description="I'll now monitor screenshare OCR and provide real-time feedback in this channel.",
                color=0x00ff00,
                timestamp=datetime.now()
            )
            embed.add_field(name="Commands", value="`!ocr stop` - Stop monitoring\n`!ocr status` - Check status", inline=False)
            
            await ctx.send(embed=embed)
        
        @self.bot.command(name='stop')
        async def stop_ocr(ctx):
            """Stop OCR monitoring for this channel"""
            channel_id = ctx.channel.id
            
            if channel_id in self.active_channels:
                self.active_channels.remove(channel_id)
                
                session_info = self.ocr_sessions.get(channel_id, {})
                duration = datetime.now() - session_info.get('start_time', datetime.now())
                message_count = session_info.get('message_count', 0)
                
                embed = discord.Embed(
                    title="🛑 OCR Monitoring Stopped",
                    description=f"Session lasted {duration.total_seconds():.0f} seconds",
                    color=0xff0000,
                    timestamp=datetime.now()
                )
                embed.add_field(name="Messages Sent", value=str(message_count), inline=True)
                
                del self.ocr_sessions[channel_id]
                await ctx.send(embed=embed)
            else:
                await ctx.send("❌ OCR monitoring is not active in this channel.")
        
        @self.bot.command(name='status')
        async def ocr_status(ctx):
            """Show OCR monitoring status"""
            channel_id = ctx.channel.id
            
            if channel_id in self.active_channels:
                session_info = self.ocr_sessions.get(channel_id, {})
                start_time = session_info.get('start_time', datetime.now())
                duration = datetime.now() - start_time
                message_count = session_info.get('message_count', 0)
                
                embed = discord.Embed(
                    title="📊 OCR Status",
                    description="OCR monitoring is active",
                    color=0x00aaff,
                    timestamp=datetime.now()
                )
                embed.add_field(name="Duration", value=f"{duration.total_seconds():.0f}s", inline=True)
                embed.add_field(name="Messages", value=str(message_count), inline=True)
                embed.add_field(name="Started by", value=session_info.get('username', 'Unknown'), inline=True)
                
                await ctx.send(embed=embed)
            else:
                await ctx.send("❌ OCR monitoring is not active in this channel.")
        
        @self.bot.command(name='clear')
        async def clear_history(ctx):
            """Clear OCR message history"""
            self.message_history.clear()
            await ctx.send("🧹 OCR message history cleared.")

    def create_ocr_embed(self, text, metadata=None):
        """Create rich embed for OCR results"""
        if not metadata:
            metadata = {}
        
        # Truncate long text
        display_text = text[:1000] + "..." if len(text) > 1000 else text
        
        embed = discord.Embed(
            title="🔍 OCR Results",
            description=f"```\n{display_text}\n```",
            color=0x00ff7f,
            timestamp=datetime.now()
        )
        
        # Add metadata fields
        if metadata.get('processing_time'):
            embed.add_field(
                name="Processing Time", 
                value=f"{metadata['processing_time']:.2f}s", 
                inline=True
            )
        
        if metadata.get('confidence'):
            embed.add_field(
                name="Confidence", 
                value=f"{metadata['confidence']:.1f}%", 
                inline=True
            )
        
        if metadata.get('word_count'):
            embed.add_field(
                name="Words", 
                value=str(metadata['word_count']), 
                inline=True
            )
        
        embed.set_footer(text="Live OCR • Discord Screenshare Integration")
        return embed

    def is_rate_limited(self):
        """Check if we're rate limited"""
        now = time.time()
        # Remove old messages outside the window
        cutoff = now - self.rate_limit_window
        while self.message_history and self.message_history[0] < cutoff:
            self.message_history.popleft()
        
        return len(self.message_history) >= self.max_messages_per_window

    def is_duplicate_message(self, text):
        """Check if this is a duplicate of the last message"""
        text_hash = hashlib.md5(text.encode()).hexdigest()
        if text_hash == self.last_message_hash:
            return True
        self.last_message_hash = text_hash
        return False

    async def send_ocr_to_discord(self, text, metadata=None):
        """Send OCR results to active Discord channels"""
        if not text.strip() or len(text.strip()) < 3:
            return False
        
        # Rate limiting
        if self.is_rate_limited():
            logging.warning("Rate limited - skipping OCR message")
            return False
        
        # Duplicate detection
        if self.is_duplicate_message(text):
            return False
        
        # Record message time
        self.message_history.append(time.time())
        
        # Send to active channels
        sent_count = 0
        for channel_id in list(self.active_channels):
            try:
                channel = self.bot.get_channel(channel_id)
                if channel:
                    embed = self.create_ocr_embed(text, metadata)
                    await channel.send(embed=embed)
                    
                    # Update session stats
                    if channel_id in self.ocr_sessions:
                        self.ocr_sessions[channel_id]['message_count'] += 1
                    
                    sent_count += 1
            except Exception as e:
                logging.error(f"Error sending OCR to channel {channel_id}: {e}")
                # Remove invalid channels
                self.active_channels.discard(channel_id)
        
        return sent_count > 0

    async def send_webhook_message(self, text, metadata=None):
        """Send OCR results via webhook"""
        if not self.webhook_url or not text.strip():
            return False
        
        try:
            # Rate limiting
            if self.is_rate_limited():
                return False
            
            # Duplicate detection
            if self.is_duplicate_message(text):
                return False
            
            # Prepare payload
            embed_data = {
                "title": "🔍 OCR Results",
                "description": f"```\n{text[:1000]}\n```",
                "color": 0x00ff7f,
                "timestamp": datetime.now().isoformat(),
                "footer": {
                    "text": "Live OCR • Discord Screenshare Integration"
                }
            }
            
            if metadata:
                embed_data["fields"] = []
                if metadata.get('processing_time'):
                    embed_data["fields"].append({
                        "name": "Processing Time",
                        "value": f"{metadata['processing_time']:.2f}s",
                        "inline": True
                    })
            
            payload = {
                "username": "OCR Bot",
                "avatar_url": "https://cdn.discordapp.com/emojis/853065845368012860.png",
                "embeds": [embed_data]
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(self.webhook_url, json=payload) as response:
                    if response.status == 204:
                        self.message_history.append(time.time())
                        return True
                    else:
                        logging.warning(f"Webhook response: {response.status}")
                        return False
                        
        except Exception as e:
            logging.error(f"Webhook error: {e}")
            return False

    def start_bot(self):
        """Start the Discord bot"""
        if self.token:
            logging.info("Starting Discord bot...")
            return self.bot.run(self.token)
        else:
            logging.warning("No bot token provided")
            return False


class WebSocketOCRIntegration:
    """WebSocket server for real-time OCR communication"""
    
    def __init__(self, port=8765):
        self.port = port
        self.connected_clients = set()
        self.server = None
        
    async def register_client(self, websocket, path):
        """Register new WebSocket client"""
        logging.info(f"Client connected: {websocket.remote_address}")
        self.connected_clients.add(websocket)
        
        try:
            await websocket.wait_closed()
        finally:
            self.connected_clients.remove(websocket)
            logging.info(f"Client disconnected: {websocket.remote_address}")
    
    async def broadcast_ocr_result(self, text, metadata=None):
        """Broadcast OCR results to all connected clients"""
        if not self.connected_clients:
            return
        
        message = {
            "type": "ocr_result",
            "text": text,
            "metadata": metadata or {},
            "timestamp": datetime.now().isoformat()
        }
        
        # Send to all connected clients
        disconnected = []
        for websocket in self.connected_clients:
            try:
                await websocket.send(json.dumps(message))
            except Exception as e:
                logging.error(f"WebSocket send error: {e}")
                disconnected.append(websocket)
        
        # Remove disconnected clients
        for ws in disconnected:
            self.connected_clients.discard(ws)
    
    async def start_server(self):
        """Start the WebSocket server"""
        import websockets
        
        logging.info(f"Starting WebSocket server on port {self.port}")
        self.server = await websockets.serve(self.register_client, "localhost", self.port)
        return self.server


class UnifiedDiscordOCRIntegration:
    """Unified integration combining bot, webhook, and WebSocket"""
    
    def __init__(self, bot_token=None, webhook_url=None, websocket_port=8765):
        self.discord_bot = DiscordOCRBot(bot_token, webhook_url)
        self.websocket_integration = WebSocketOCRIntegration(websocket_port)
        self.running = False
        
    async def send_ocr_result(self, text, metadata=None):
        """Send OCR result through all available channels"""
        if not text or not text.strip():
            return
        
        results = []
        
        # Send via Discord bot
        try:
            bot_result = await self.discord_bot.send_ocr_to_discord(text, metadata)
            results.append(("bot", bot_result))
        except Exception as e:
            logging.error(f"Bot send error: {e}")
            results.append(("bot", False))
        
        # Send via webhook
        try:
            webhook_result = await self.discord_bot.send_webhook_message(text, metadata)
            results.append(("webhook", webhook_result))
        except Exception as e:
            logging.error(f"Webhook send error: {e}")
            results.append(("webhook", False))
        
        # Send via WebSocket
        try:
            await self.websocket_integration.broadcast_ocr_result(text, metadata)
            results.append(("websocket", True))
        except Exception as e:
            logging.error(f"WebSocket send error: {e}")
            results.append(("websocket", False))
        
        return results
    
    def start_all_services(self):
        """Start all integration services"""
        logging.info("Starting unified Discord OCR integration...")
        
        async def run_services():
            # Start WebSocket server
            websocket_server = await self.websocket_integration.start_server()
            
            # Keep running
            self.running = True
            while self.running:
                await asyncio.sleep(1)
        
        # Run async services
        asyncio.create_task(run_services())
        
        # Start Discord bot (blocking)
        if self.discord_bot.token:
            self.discord_bot.start_bot()


# Example usage and testing
async def test_integration():
    """Test the Discord integration"""
    # Initialize integration (you'll need to provide actual tokens/URLs)
    integration = UnifiedDiscordOCRIntegration(
        bot_token=None,  # Your bot token
        webhook_url=None,  # Your webhook URL
        websocket_port=8765
    )
    
    # Test sending OCR result
    test_metadata = {
        'processing_time': 1.23,
        'confidence': 95.5,
        'word_count': 15
    }
    
    await integration.send_ocr_result("This is a test OCR result from screenshare", test_metadata)

if __name__ == "__main__":
    # Example configuration - replace with your actual values
    BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"
    WEBHOOK_URL = "YOUR_WEBHOOK_URL_HERE"
    
    if BOT_TOKEN != "YOUR_BOT_TOKEN_HERE":
        integration = UnifiedDiscordOCRIntegration(
            bot_token=BOT_TOKEN,
            webhook_url=WEBHOOK_URL,
            websocket_port=8765
        )
        integration.start_all_services()
    else:
        print("Please configure your Discord bot token and webhook URL")
        print("Then run: python discord_bot_integration.py")