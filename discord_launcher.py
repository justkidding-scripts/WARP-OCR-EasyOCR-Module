#!/usr/bin/env python3
"""
Discord Auto-Launch Module for WARP OCR
Automatically launches Discord when starting WARP OCR framework
"""

import subprocess
import time
import logging
import os
import signal
import psutil
from typing import Optional, List, Dict

class DiscordLauncher:
    """Discord application launcher and manager"""
    
    def __init__(self):
        self.discord_process = None
        self.discord_pid = None
        self.launch_timeout = 30  # seconds
        self.discord_paths = [
            '/usr/bin/discord',
            '/opt/discord/Discord',
            '/opt/Discord/Discord',
            '/snap/discord/current/usr/share/discord/Discord',
            '/var/lib/flatpak/exports/bin/com.discordapp.Discord',
            '~/.local/bin/discord',
            '/usr/local/bin/discord'
        ]
        
    def find_discord_executable(self) -> Optional[str]:
        """Find Discord executable on the system"""
        # Check common installation paths
        for path in self.discord_paths:
            expanded_path = os.path.expanduser(path)
            if os.path.isfile(expanded_path) and os.access(expanded_path, os.X_OK):
                logging.info(f"Found Discord executable: {expanded_path}")
                return expanded_path
        
        # Check if discord is in PATH
        try:
            result = subprocess.run(['which', 'discord'], capture_output=True, text=True)
            if result.returncode == 0 and result.stdout.strip():
                path = result.stdout.strip()
                logging.info(f"Found Discord in PATH: {path}")
                return path
        except Exception as e:
            logging.debug(f"Error checking PATH for discord: {e}")
        
        # Check for Snap installation
        try:
            result = subprocess.run(['snap', 'list', 'discord'], capture_output=True, text=True)
            if result.returncode == 0:
                logging.info("Found Discord via Snap")
                return 'snap run discord'
        except Exception:
            pass
            
        # Check for Flatpak installation
        try:
            result = subprocess.run(['flatpak', 'list', '--app'], capture_output=True, text=True)
            if 'com.discordapp.Discord' in result.stdout:
                logging.info("Found Discord via Flatpak")
                return 'flatpak run com.discordapp.Discord'
        except Exception:
            pass
            
        logging.warning("Discord executable not found")
        return None
    
    def is_discord_running(self) -> bool:
        """Check if Discord is already running"""
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    proc_info = proc.info
                    if proc_info['name'] and 'discord' in proc_info['name'].lower():
                        logging.info(f"Discord is already running (PID: {proc_info['pid']})")
                        self.discord_pid = proc_info['pid']
                        return True
                    
                    # Check command line for Discord
                    if proc_info['cmdline']:
                        cmdline = ' '.join(proc_info['cmdline']).lower()
                        if 'discord' in cmdline and 'electron' not in cmdline:
                            logging.info(f"Discord is already running (PID: {proc_info['pid']})")
                            self.discord_pid = proc_info['pid']
                            return True
                            
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception as e:
            logging.error(f"Error checking if Discord is running: {e}")
        
        return False
    
    def launch_discord(self, headless: bool = False) -> bool:
        """Launch Discord application"""
        if self.is_discord_running():
            logging.info("Discord is already running, skipping launch")
            return True
        
        discord_path = self.find_discord_executable()
        if not discord_path:
            logging.error("Discord executable not found. Please install Discord.")
            return False
        
        try:
            logging.info(f"Launching Discord from: {discord_path}")
            
            # Prepare launch command
            if discord_path.startswith('snap run'):
                cmd = discord_path.split()
            elif discord_path.startswith('flatpak run'):
                cmd = discord_path.split()
            else:
                cmd = [discord_path]
            
            # Add Discord launch options
            discord_args = []
            if headless:
                discord_args.extend(['--no-sandbox', '--disable-gpu'])
            
            # Set environment variables for better Discord behavior
            env = os.environ.copy()
            env['DISCORD_NO_UPDATE_CHECK'] = '1'
            env['DISCORD_DISABLE_HARDWARE_ACCELERATION'] = '1' if headless else '0'
            
            # Launch Discord
            self.discord_process = subprocess.Popen(
                cmd + discord_args,
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                preexec_fn=os.setsid  # Create new process group
            )
            
            # Wait for Discord to start
            logging.info("Waiting for Discord to start...")
            start_time = time.time()
            
            while time.time() - start_time < self.launch_timeout:
                if self.is_discord_running():
                    logging.info("✅ Discord launched successfully")
                    return True
                time.sleep(1)
            
            logging.error("❌ Discord launch timeout")
            return False
            
        except Exception as e:
            logging.error(f"Failed to launch Discord: {e}")
            return False
    
    def wait_for_discord_window(self, timeout: int = 30) -> bool:
        """Wait for Discord window to appear"""
        logging.info("Waiting for Discord window to appear...")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                # Check for Discord window using xdotool
                result = subprocess.run(
                    ['xdotool', 'search', '--name', 'Discord'],
                    capture_output=True, text=True, timeout=5
                )
                
                if result.returncode == 0 and result.stdout.strip():
                    window_ids = result.stdout.strip().split('\n')
                    logging.info(f"✅ Discord window found (Window IDs: {window_ids})")
                    return True
                    
            except subprocess.TimeoutExpired:
                logging.warning("xdotool search timed out")
            except FileNotFoundError:
                logging.warning("xdotool not available, skipping window detection")
                return True  # Assume Discord is ready if xdotool not available
            except Exception as e:
                logging.debug(f"Error checking for Discord window: {e}")
            
            time.sleep(1)
        
        logging.warning("Discord window detection timeout")
        return False
    
    def stop_discord(self) -> bool:
        """Stop Discord if launched by this launcher"""
        if not self.discord_pid:
            logging.info("No Discord process to stop")
            return True
        
        try:
            logging.info(f"Stopping Discord (PID: {self.discord_pid})")
            
            # Try graceful shutdown first
            os.kill(self.discord_pid, signal.SIGTERM)
            time.sleep(3)
            
            # Check if still running
            if psutil.pid_exists(self.discord_pid):
                logging.warning("Discord didn't respond to SIGTERM, sending SIGKILL")
                os.kill(self.discord_pid, signal.SIGKILL)
                time.sleep(1)
            
            if not psutil.pid_exists(self.discord_pid):
                logging.info("✅ Discord stopped successfully")
                self.discord_pid = None
                return True
            else:
                logging.error("❌ Failed to stop Discord")
                return False
                
        except ProcessLookupError:
            logging.info("Discord process already terminated")
            self.discord_pid = None
            return True
        except Exception as e:
            logging.error(f"Error stopping Discord: {e}")
            return False
    
    def get_discord_status(self) -> Dict:
        """Get Discord status information"""
        status = {
            'running': self.is_discord_running(),
            'pid': self.discord_pid,
            'executable_found': self.find_discord_executable() is not None,
            'window_available': False
        }
        
        if status['running']:
            try:
                result = subprocess.run(
                    ['xdotool', 'search', '--name', 'Discord'],
                    capture_output=True, text=True, timeout=3
                )
                status['window_available'] = result.returncode == 0 and bool(result.stdout.strip())
            except:
                pass
        
        return status

def install_discord_if_missing():
    """Install Discord if not found on the system"""
    launcher = DiscordLauncher()
    
    if launcher.find_discord_executable():
        print("✅ Discord is already installed")
        return True
    
    print("⚠️  Discord not found. Would you like to install it?")
    
    # Try different installation methods
    installation_methods = [
        {
            'name': 'Snap',
            'check': ['snap', '--version'],
            'install': ['sudo', 'snap', 'install', 'discord']
        },
        {
            'name': 'Flatpak', 
            'check': ['flatpak', '--version'],
            'install': ['sudo', 'flatpak', 'install', '-y', 'flathub', 'com.discordapp.Discord']
        },
        {
            'name': 'APT (Debian/Ubuntu)',
            'check': ['apt', '--version'],
            'install': ['sudo', 'apt', 'update', '&&', 'sudo', 'apt', 'install', '-y', 'discord']
        }
    ]
    
    for method in installation_methods:
        try:
            # Check if package manager is available
            result = subprocess.run(method['check'], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"📦 Attempting to install Discord via {method['name']}")
                install_result = subprocess.run(method['install'], timeout=300)
                
                if install_result.returncode == 0:
                    print(f"✅ Discord installed successfully via {method['name']}")
                    return True
                else:
                    print(f"❌ Installation failed via {method['name']}")
                    
        except subprocess.TimeoutExpired:
            print(f"⏰ Installation timeout for {method['name']}")
        except FileNotFoundError:
            print(f"⚠️  {method['name']} not available")
        except Exception as e:
            print(f"❌ Installation error for {method['name']}: {e}")
    
    print("❌ Failed to install Discord automatically")
    print("💡 Please install Discord manually from https://discord.com/download")
    return False

if __name__ == "__main__":
    # Test the Discord launcher
    import sys
    
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    launcher = DiscordLauncher()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == 'install':
            install_discord_if_missing()
        elif sys.argv[1] == 'launch':
            success = launcher.launch_discord()
            if success:
                launcher.wait_for_discord_window()
        elif sys.argv[1] == 'stop':
            launcher.stop_discord()
        elif sys.argv[1] == 'status':
            status = launcher.get_discord_status()
            print(f"Discord Status: {status}")
    else:
        # Default: launch Discord
        print("🚀 Testing Discord Launcher")
        
        status = launcher.get_discord_status()
        print(f"Initial status: {status}")
        
        if not status['running']:
            print("Launching Discord...")
            if launcher.launch_discord():
                launcher.wait_for_discord_window()
                print("Discord is ready!")
            else:
                print("Failed to launch Discord")
        else:
            print("Discord is already running")