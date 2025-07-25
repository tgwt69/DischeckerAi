
"""
Discord AI Selfbot - 2025 Edition
Enhanced with latest Groq API, improved security, and modern Python practices
"""

import os
import asyncio
import discord
import shutil
import re
import random
import sys
import time
import requests
import logging
import threading
import signal
from datetime import datetime, timedelta
from collections import deque, defaultdict
from asyncio import Lock
from typing import Dict, Set, List, Optional, Tuple

from utils.helpers import (
    clear_console,
    resource_path,
    get_env_path,
    load_instructions,
    load_config,
)
from utils.db import init_db, get_channels, get_ignored_users
from utils.error_notifications import webhook_log
from colorama import init, Fore, Style

# Initialize colorama for cross-platform colored terminal output
init()

# Configure logging for better monitoring
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('selfbot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Version and update checking
CURRENT_VERSION = "v3.0.0"
GITHUB_REPO = "Najmul190/Discord-AI-Selfbot"

def check_config():
    """Check if configuration files exist, create them if not"""
    env_path = resource_path("config/.env")
    config_path = resource_path("config/config.yaml")
    
    if not os.path.exists(env_path) or not os.path.exists(config_path):
        print("Config files are not setup! Running automatic setup...")
        # For automated environments like Replit, Render, etc., use non-interactive setup
        if (os.getenv('REPLIT_ENVIRONMENT') or 
            os.getenv('CODESPACE_NAME') or 
            os.getenv('RENDER') or 
            os.getenv('PORT') or 
            not sys.stdin.isatty()):
            print("Detected cloud environment, using default configuration...")
            import subprocess
            result = subprocess.run([sys.executable, "setup_auto.py"], capture_output=True, text=True)
            if result.returncode != 0:
                print("Failed to run automatic setup!")
                print(result.stderr)
                sys.exit(1)
        else:
            # Interactive setup for local environments
            import utils.setup as setup
            setup.create_config()

def check_for_update() -> Optional[str]:
    """Check for latest version on GitHub"""
    try:
        url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            return response.json()["tag_name"]
        else:
            logger.warning(f"Failed to check for updates: HTTP {response.status_code}")
            return None
    except Exception as e:
        logger.error(f"Error checking for updates: {e}")
        return None

def display_update_notice():
    """Display update notice if available"""
    latest_version = check_for_update()
    if latest_version and latest_version != CURRENT_VERSION:
        print(
            f"{Fore.RED}A new version of the AI Selfbot is available! "
            f"Please update to {latest_version} at:\n"
            f"https://github.com/{GITHUB_REPO}/releases/latest{Style.RESET_ALL}"
        )
        time.sleep(3)
        return True
    return False

# Check configuration and updates
check_config()
update_available = display_update_notice()

# Load configuration
config = load_config()

# Import AI utilities after config is loaded
from utils.ai import init_ai
from dotenv import load_dotenv
from discord.ext import commands
from utils.ai import generate_response, generate_response_image
from utils.split_response import split_response
from utils.auth import get_auth_manager
from web_server import start_health_server, stop_health_server

# Load environment variables
env_path = get_env_path()
load_dotenv(dotenv_path=env_path, override=True)

# Initialize database and AI
init_db()
init_ai()

# Bot configuration from config file
TOKEN = os.getenv("DISCORD_TOKEN")
PREFIX = config["bot"]["prefix"]
OWNER_ID = config["bot"]["owner_id"]
TRIGGER = [t.strip().lower() for t in config["bot"]["trigger"].split(",")]
DISABLE_MENTIONS = config["bot"]["disable_mentions"]

# Anti-detection: Add startup delay to avoid rapid reconnections
STARTUP_DELAY = random.uniform(3.0, 8.0)
logger.info(f"Starting in {STARTUP_DELAY:.1f}s to avoid detection...")
time.sleep(STARTUP_DELAY)

# Enhanced bot setup with discord.py-self compatible configuration
bot = commands.Bot(
    command_prefix=PREFIX,
    help_command=None,
    case_insensitive=True,
    self_bot=True,
    # Anti-detection: Reduce connection frequency
    heartbeat_timeout=60.0,
    guild_ready_timeout=10.0
)

# Initialize selfbot_id attribute early to prevent AttributeError
bot.selfbot_id = None

# Global keep-alive state
class KeepAliveState:
    def __init__(self):
        self.running = True
        self.last_activity = time.time()
        self.ping_count = 0
        self.error_count = 0
        self.threads = []
        self.restart_requested = False

keep_alive_state = KeepAliveState()

# Bot state management
class BotState:
    def __init__(self):
        self.owner_id = OWNER_ID
        self.active_channels: Set[int] = set(get_channels())
        self.ignore_users: Set[int] = set(get_ignored_users())
        self.message_history: Dict[int, List[str]] = defaultdict(list)
        self.paused = False
        self.maintenance_mode = False
        self.allow_dm = config["bot"]["allow_dm"]
        self.allow_gc = config["bot"]["allow_gc"]
        self.help_command_enabled = config["bot"]["help_command_enabled"]
        self.realistic_typing = config["bot"]["realistic_typing"]
        self.anti_age_ban = config["bot"]["anti_age_ban"]
        self.batch_messages = config["bot"]["batch_messages"]
        self.batch_wait_time = float(config["bot"]["batch_wait_time"])
        self.hold_conversation = config["bot"]["hold_conversation"]
        
        # Enhanced anti-spam and rate limiting
        self.user_message_counts: Dict[int, List[float]] = defaultdict(list)
        self.user_cooldowns: Dict[int, float] = {}
        self.message_queues: Dict[int, deque] = defaultdict(deque)
        self.processing_locks: Dict[int, Lock] = defaultdict(Lock)
        self.user_message_batches: Dict[str, Dict] = {}
        self.active_conversations: Dict[str, float] = {}
        
        # Enhanced security features
        self.failed_attempts: Dict[int, int] = defaultdict(int)
        self.last_activity: Dict[int, float] = {}
        self.typing_delays: Dict[int, float] = {}
        

    @property
    def instructions(self) -> str:
        return load_instructions()

# Initialize bot state
bot.state = BotState()

# Constants for spam detection and conversation management
SPAM_MESSAGE_THRESHOLD = 5
SPAM_TIME_WINDOW = 10.0
COOLDOWN_DURATION = 60.0
CONVERSATION_TIMEOUT = 300.0  # Extended to 5 minutes
MAX_HISTORY = 20  # Increased history limit
MAX_FAILED_ATTEMPTS = 3

def get_terminal_size() -> int:
    """Get terminal width for formatting"""
    try:
        columns, _ = shutil.get_terminal_size()
        return columns
    except:
        return 80  # Fallback width

def create_border(char="═") -> str:
    """Create a border for terminal output"""
    width = get_terminal_size()
    return char * (width - 2)

def print_header():
    """Print formatted header"""
    width = get_terminal_size()
    border = create_border()
    title = f"Discord AI Selfbot {CURRENT_VERSION} - 2025 Edition"
    padding = " " * ((width - len(title) - 2) // 2)

    print(f"{Fore.CYAN}╔{border}╗")
    print(f"║{padding}{Style.BRIGHT}{title}{Style.NORMAL}{padding}║")
    print(f"╚{border}╝{Style.RESET_ALL}")

def print_separator():
    """Print a separator line"""
    print(f"{Fore.CYAN}{create_border('─')}{Style.RESET_ALL}")

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    logger.info(f"Received signal {signum}, shutting down gracefully...")
    keep_alive_state.running = False
    try:
        if bot.is_ready():
            asyncio.create_task(bot.close())
    except:
        pass
    sys.exit(0)

# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def ultra_robust_health_server():
    """Ultra-robust health server that never dies"""
    import socket
    import json
    from http.server import HTTPServer, BaseHTTPRequestHandler
    import traceback
    
    class UltraHealthHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            try:
                keep_alive_state.last_activity = time.time()
                keep_alive_state.ping_count += 1
                
                if self.path == '/health':
                    response = {
                        "status": "ultra_healthy",
                        "service": "Discord AI Selfbot",
                        "version": "3.0.0",
                        "uptime": time.time(),
                        "ping_count": keep_alive_state.ping_count,
                        "last_activity": keep_alive_state.last_activity,
                        "bot_ready": getattr(bot, 'is_ready', lambda: False)(),
                        "ultra_mode": True
                    }
                elif self.path == '/activity':
                    # Intensive computation to show high activity
                    import random
                    _ = sum(i * random.randint(1, 100) for i in range(1000))
                    
                    response = {
                        "activity": "ultra_high_simulation",
                        "timestamp": time.time(),
                        "computation_cycles": random.randint(10000, 99999),
                        "memory_active": True,
                        "cpu_intensive": True,
                        "status": "extremely_active"
                    }
                elif self.path == '/ping':
                    response = {"pong": time.time(), "ultra": True}
                elif self.path == '/stats':
                    response = {
                        "uptime": time.time(),
                        "total_pings": keep_alive_state.ping_count,
                        "error_count": keep_alive_state.error_count,
                        "status": "running_24_7",
                        "ultra_robust": True
                    }
                else:
                    response = {"status": "ultra_healthy", "endpoint": "unknown"}
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Cache-Control', 'no-cache')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode())
                
            except Exception as e:
                keep_alive_state.error_count += 1
                logger.error(f"Health server error: {e}")
                try:
                    self.send_response(500)
                    self.end_headers()
                    self.wfile.write(b'{"error": "internal_error"}')
                except:
                    pass
        
        def do_POST(self):
            self.do_GET()
        
        def log_message(self, format, *args):
            pass  # Suppress default logging
    
    max_retries = 100
    retry_count = 0
    
    while keep_alive_state.running and retry_count < max_retries:
        try:
            server = HTTPServer(('0.0.0.0', 5000), UltraHealthHandler)
            server.timeout = 1
            logger.info(f"Ultra-robust health server started on port 5000 (attempt {retry_count + 1})")
            
            while keep_alive_state.running:
                try:
                    server.handle_request()
                    time.sleep(0.01)  # Prevent 100% CPU usage
                except socket.timeout:
                    continue
                except Exception as e:
                    logger.warning(f"Health server request error: {e}")
                    continue
                    
        except Exception as e:
            retry_count += 1
            keep_alive_state.error_count += 1
            logger.error(f"Health server startup failed (attempt {retry_count}): {e}")
            time.sleep(min(retry_count * 2, 30))  # Exponential backoff
    
    logger.error("Health server failed to start after maximum retries")

def continuous_self_ping():
    """Continuous self-pinging system"""
    import requests
    
    while keep_alive_state.running:
        try:
            endpoints = ['/health', '/activity', '/stats', '/ping']
            for endpoint in endpoints:
                if not keep_alive_state.running:
                    break
                
                try:
                    response = requests.get(f'http://127.0.0.1:5000{endpoint}', timeout=5)
                    if response.status_code == 200:
                        logger.debug(f"Self-ping to {endpoint} successful")
                    time.sleep(15)  # 15 seconds between each endpoint
                except Exception as e:
                    logger.debug(f"Self-ping to {endpoint} failed: {e}")
                    time.sleep(5)
            
        except Exception as e:
            logger.error(f"Error in continuous self-ping: {e}")
            time.sleep(30)

def memory_thrashing_loop():
    """Keep memory and CPU active with intensive operations"""
    active_data = {}
    
    while keep_alive_state.running:
        try:
            # Intensive memory operations
            current_time = time.time()
            
            # Create and manipulate large data structures
            import random
            big_list = [random.randint(1, 10000) for _ in range(1000)]
            big_dict = {str(i): random.random() * i for i in range(500)}
            
            # Intensive computations
            result = sum(x * y for x, y in zip(big_list[:500], range(500)))
            
            # Keep data in memory
            active_data[current_time] = {
                'list': big_list,
                'dict': big_dict,
                'result': result,
                'timestamp': current_time
            }
            
            # Clean old data to prevent memory leaks
            if len(active_data) > 10:
                oldest_key = min(active_data.keys())
                del active_data[oldest_key]
            
            # Log activity every 5 minutes
            if int(current_time) % 300 == 0:
                logger.info(f"Memory thrashing active - processed {len(active_data)} cycles")
            
            time.sleep(10)  # 10 seconds between cycles
            
        except Exception as e:
            logger.error(f"Error in memory thrashing loop: {e}")
            time.sleep(30)

def file_system_activity():
    """Create file system activity to prevent hibernation"""
    temp_dir = "temp_keepalive"
    
    # Create temp directory
    try:
        os.makedirs(temp_dir, exist_ok=True)
    except:
        pass
    
    while keep_alive_state.running:
        try:
            current_time = time.time()
            filename = f"{temp_dir}/keepalive_{int(current_time)}.tmp"
            
            # Write data to file
            with open(filename, 'w') as f:
                import random
                data = {
                    'timestamp': current_time,
                    'random_data': [random.randint(1, 1000) for _ in range(100)],
                    'keep_alive': True
                }
                f.write(str(data))
            
            # Read it back
            try:
                with open(filename, 'r') as f:
                    content = f.read()
            except:
                pass
            
            # Delete old files
            try:
                for old_file in os.listdir(temp_dir):
                    file_path = os.path.join(temp_dir, old_file)
                    if os.path.getctime(file_path) < current_time - 300:  # 5 minutes old
                        os.remove(file_path)
            except:
                pass
            
            time.sleep(20)  # Every 20 seconds
            
        except Exception as e:
            logger.error(f"Error in file system activity: {e}")
            time.sleep(60)

def network_activity_loop():
    """Generate network activity to external services"""
    import requests
    
    # List of reliable endpoints to ping
    endpoints = [
        'https://httpbin.org/get',
        'https://api.github.com/zen',
        'https://jsonplaceholder.typicode.com/posts/1',
        'https://httpstat.us/200'
    ]
    
    while keep_alive_state.running:
        try:
            for endpoint in endpoints:
                if not keep_alive_state.running:
                    break
                
                try:
                    response = requests.get(endpoint, timeout=10)
                    logger.debug(f"External ping to {endpoint}: {response.status_code}")
                    time.sleep(30)  # 30 seconds between external pings
                except Exception as e:
                    logger.debug(f"External ping failed: {e}")
                    time.sleep(10)
            
        except Exception as e:
            logger.error(f"Error in network activity loop: {e}")
            time.sleep(60)

def start_all_keep_alive_systems():
    """Start all keep-alive systems in separate threads"""
    systems = [
        ("Ultra Health Server", ultra_robust_health_server),
        ("Self Ping", continuous_self_ping),
        ("Memory Thrashing", memory_thrashing_loop),
        ("File System Activity", file_system_activity),
        ("Network Activity", network_activity_loop)
    ]
    
    for name, func in systems:
        try:
            thread = threading.Thread(target=func, daemon=True, name=name)
            thread.start()
            keep_alive_state.threads.append(thread)
            logger.info(f"Started {name} system")
            time.sleep(1)  # Stagger startup
        except Exception as e:
            logger.error(f"Failed to start {name}: {e}")

@bot.event
async def on_ready():
    """Event triggered when bot is ready"""    
    # Validate configuration
    if config["bot"]["owner_id"] == 123456789012345678:
        logger.error("Please set a valid owner_id in config.yaml")
        await bot.close()
        sys.exit(1)

    # For selfbots, owner_id should be the same as bot user ID
    if config["bot"]["owner_id"] != bot.user.id:
        logger.warning(f"Note: owner_id ({config['bot']['owner_id']}) differs from bot user ID ({bot.user.id})")
        logger.warning("For selfbots, these should typically be the same")

    bot.selfbot_id = bot.user.id
    clear_console()
    print_header()
    
    # Initialize and check authorization
    auth_manager = get_auth_manager()
    auth_stats = auth_manager.get_stats()
    
    logger.info(f"AI Selfbot successfully logged in as {bot.user.name} ({bot.selfbot_id})")
    logger.info(f"Authorization: {auth_stats['total_authorized']} users, Owner: {auth_stats['owner_id']}")
    print(f"AI Selfbot successfully logged in as {Fore.CYAN}{bot.user.name} ({bot.selfbot_id}){Style.RESET_ALL}.\n")
    print(f"Authorization: {auth_stats['total_authorized']} authorized users, Owner: {auth_stats['owner_id']}\n")

    if update_available:
        print(f"{Fore.RED}Update available! Please check the latest release.{Style.RESET_ALL}\n")

    # Display active channels
    if len(bot.state.active_channels) > 0:
        print("Active in the following channels:")
        for channel_id in bot.state.active_channels:
            channel = bot.get_channel(channel_id)
            if channel:
                try:
                    print(f"- #{channel.name} in {channel.guild.name}")
                except Exception:
                    logger.warning(f"Could not access channel {channel_id}")
    else:
        print(f"Bot is currently not active in any channel. Use {PREFIX}toggleactive to activate.")

    print(f"\n{Fore.LIGHTBLACK_EX}Join the Discord server for support: https://discord.gg/yUWmzQBV4P{Style.RESET_ALL}")
    print(f"\n{Fore.GREEN}🔥 ULTRA-ROBUST 24/7 MODE ACTIVATED 🔥{Style.RESET_ALL}")
    print_separator()

@bot.event
async def setup_hook():
    """Setup hook for loading extensions"""
    await load_extensions()
    # Start background tasks
    bot.loop.create_task(auto_conversation_loop())
    bot.loop.create_task(async_keep_alive_monitor())
    bot.loop.create_task(async_activity_generator())
    bot.loop.create_task(async_health_checker())

async def load_extensions():
    """Load bot extensions/cogs"""
    extensions = ['cogs.commands', 'cogs.admin']
    
    for extension in extensions:
        try:
            await bot.load_extension(extension)
            logger.info(f"Loaded extension: {extension}")
        except Exception as e:
            logger.error(f"Failed to load extension {extension}: {e}")

async def async_keep_alive_monitor():
    """Async monitor for all keep-alive systems"""
    await bot.wait_until_ready()
    
    while not bot.is_closed():
        try:
            # Check if keep-alive systems are running
            alive_threads = [t for t in keep_alive_state.threads if t.is_alive()]
            
            if len(alive_threads) < len(keep_alive_state.threads):
                logger.warning(f"Some keep-alive systems died, restarting...")
                start_all_keep_alive_systems()
            
            # Update activity timestamp
            keep_alive_state.last_activity = time.time()
            
            await asyncio.sleep(60)  # Check every minute
            
        except Exception as e:
            logger.error(f"Error in async keep-alive monitor: {e}")
            await asyncio.sleep(30)

async def async_activity_generator():
    """Generate async activity to keep event loop busy"""
    await bot.wait_until_ready()
    counter = 0
    
    while not bot.is_closed():
        try:
            counter += 1
            
            # Intensive async operations
            await asyncio.sleep(0.1)
            
            # Create and destroy tasks regularly
            if counter % 100 == 0:
                dummy_tasks = [asyncio.create_task(asyncio.sleep(0.01)) for _ in range(10)]
                await asyncio.gather(*dummy_tasks, return_exceptions=True)
                logger.info(f"Async activity generator cycle {counter}")
            
            await asyncio.sleep(5)  # Every 5 seconds
            
        except Exception as e:
            logger.error(f"Error in async activity generator: {e}")
            await asyncio.sleep(10)

async def async_health_checker():
    """Check bot health and restart if necessary"""
    await bot.wait_until_ready()
    
    while not bot.is_closed():
        try:
            # Check bot connection health
            if bot.is_closed():
                logger.error("Bot connection closed, attempting restart...")
                keep_alive_state.restart_requested = True
                break
            
            # Check last activity
            if time.time() - keep_alive_state.last_activity > 600:  # 10 minutes
                logger.warning("No activity detected for 10 minutes, generating activity...")
                keep_alive_state.last_activity = time.time()
            
            await asyncio.sleep(120)  # Check every 2 minutes
            
        except Exception as e:
            logger.error(f"Error in async health checker: {e}")
            await asyncio.sleep(60)

async def auto_conversation_loop():
    """Background task to automatically initiate conversations in active channels"""
    import random
    from utils.ai import generate_auto_conversation_starter
    from utils.db import get_channels, can_send_auto_message, record_auto_message
    
    await bot.wait_until_ready()
    
    while not bot.is_closed():
        try:
            config = load_config()
            
            # Check if auto conversation is enabled
            if not config.get('bot', {}).get('auto_conversation', False):
                await asyncio.sleep(300)  # Wait 5 minutes before checking again
                continue
            
            # Get auto conversation settings
            chance = config.get('bot', {}).get('auto_conversation_chance', 0.15)
            interval = config.get('bot', {}).get('auto_conversation_interval', 300)
            
            # Get active channels
            active_channels = get_channels()
            
            for channel_id in active_channels:
                try:
                    channel = bot.get_channel(channel_id)
                    if not channel:
                        continue
                    
                    # Skip if bot is paused or maintenance mode
                    if bot.state.paused or bot.state.maintenance_mode:
                        continue
                    
                    # Check if we can send auto message (rate limiting)
                    if not can_send_auto_message(channel_id):
                        continue
                    
                    # Random chance to start conversation
                    if random.random() > chance:
                        continue
                    
                    # Get recent messages for context
                    recent_messages = []
                    try:
                        async for msg in channel.history(limit=5):
                            if msg.content and not msg.author.bot:
                                recent_messages.append(f"{msg.author.display_name}: {msg.content}")
                    except:
                        pass
                    
                    # Generate conversation starter
                    starter = await generate_auto_conversation_starter(
                        channel_context=f"#{channel.name} in {channel.guild.name if channel.guild else 'DM'}",
                        recent_messages=recent_messages
                    )
                    
                    if starter:
                        # Add natural delay and typing simulation
                        await asyncio.sleep(random.uniform(2, 8))
                        
                        # Send typing indicator
                        async with channel.typing():
                            typing_duration = random.uniform(1.5, 4.0)
                            await asyncio.sleep(typing_duration)
                        
                        # Send the message
                        await channel.send(starter)
                        
                        # Record auto message
                        guild_id = channel.guild.id if channel.guild else None
                        record_auto_message(channel_id, guild_id, starter[:50])
                        
                        logger.info(f"[AUTO] Sent conversation starter in #{channel.name}: {starter}")
                        
                        # Add cooldown between auto messages across channels
                        await asyncio.sleep(random.uniform(30, 120))
                    
                except Exception as e:
                    logger.error(f"Error in auto conversation for channel {channel_id}: {e}")
                    continue
            
            # Wait before next cycle
            await asyncio.sleep(interval + random.uniform(-60, 60))
            
        except Exception as e:
            logger.error(f"Error in auto conversation loop: {e}")
            await asyncio.sleep(300)  # Wait 5 minutes on error

def should_ignore_message(message: discord.Message) -> bool:
    """Check if message should be ignored"""
    return (
        message.author.id in bot.state.ignore_users
        or message.author.id == bot.user.id  # Use bot.user.id instead of bot.selfbot_id
        or message.author.bot
        or message.author == bot.user  # Additional check using the user object
    )

def is_trigger_message(message: discord.Message) -> bool:
    """Enhanced trigger detection with better conversation handling"""
    # Check for mentions (excluding @everyone and @here)
    mentioned = (
        bot.user.mentioned_in(message)
        and "@everyone" not in message.content
        and "@here" not in message.content
    )
    
    # Check if replying to bot
    replied_to = (
        message.reference
        and message.reference.resolved
        and message.reference.resolved.author.id == bot.selfbot_id
    )
    
    # Check for DM and group chat permissions
    is_dm = isinstance(message.channel, discord.DMChannel) and bot.state.allow_dm
    is_group_dm = isinstance(message.channel, discord.GroupChannel) and bot.state.allow_gc
    
    # Enhanced conversation tracking
    conv_key = f"{message.author.id}-{message.channel.id}"
    current_time = time.time()
    in_conversation = (
        conv_key in bot.state.active_conversations
        and current_time - bot.state.active_conversations[conv_key] < CONVERSATION_TIMEOUT
        and bot.state.hold_conversation
    )
    
    # Enhanced trigger word detection with word boundaries
    content_has_trigger = any(
        re.search(rf"\b{re.escape(keyword)}\b", message.content.lower())
        for keyword in TRIGGER
    )
    
    # Update conversation timestamp if triggered
    if any([content_has_trigger, mentioned, replied_to, is_dm, is_group_dm, in_conversation]):
        bot.state.active_conversations[conv_key] = current_time
        bot.state.last_activity[message.author.id] = current_time

    return any([content_has_trigger, mentioned, replied_to, is_dm, is_group_dm, in_conversation])

def analyze_human_style(message_content: str) -> str:
    """Analyze human typing patterns to help AI learn"""
    patterns = []
    
    # Check punctuation usage
    has_punctuation = any(char in message_content for char in '.!?')
    if not has_punctuation:
        patterns.append("no punctuation")
    
    # Check capitalization
    if message_content.islower():
        patterns.append("all lowercase")
    elif message_content.isupper():
        patterns.append("all caps")
    
    # Check length
    if len(message_content) <= 5:
        patterns.append("very short")
    elif len(message_content) <= 15:
        patterns.append("short")
    
    # Check for common casual patterns
    casual_words = ['lol', 'fr', 'nah', 'yeah', 'yep', 'nope', 'idk', 'tbh', 'prolly', 'gonna', 'wanna']
    if any(word in message_content.lower() for word in casual_words):
        patterns.append("casual slang")
    
    return f" [{', '.join(patterns)}]" if patterns else ""

def update_message_history(author_id: int, message_content: str, is_bot_response: bool = False):
    """Update message history for context - includes both user messages and bot responses with style analysis"""
    if author_id not in bot.state.message_history:
        bot.state.message_history[author_id] = []
    
    # Format the message to show who said what
    if is_bot_response:
        formatted_message = f"[BOT]: {message_content}"
    else:
        # Add style analysis for human messages to help AI learn
        style_notes = analyze_human_style(message_content)
        formatted_message = f"[USER{style_notes}]: {message_content}"
    
    bot.state.message_history[author_id].append(formatted_message)
    bot.state.message_history[author_id] = bot.state.message_history[author_id][-MAX_HISTORY:]

async def check_spam_and_cooldown(user_id: int) -> Tuple[bool, Optional[str]]:
    """Enhanced spam detection and cooldown management"""
    current_time = time.time()
    
    # Check existing cooldown
    if user_id in bot.state.user_cooldowns:
        cooldown_end = bot.state.user_cooldowns[user_id]
        if current_time < cooldown_end:
            remaining = int(cooldown_end - current_time)
            return False, f"User is on cooldown for {remaining}s"
        else:
            del bot.state.user_cooldowns[user_id]
    
    # Update message count for spam detection
    if user_id not in bot.state.user_message_counts:
        bot.state.user_message_counts[user_id] = []
    
    # Remove old timestamps outside the spam window
    bot.state.user_message_counts[user_id] = [
        timestamp for timestamp in bot.state.user_message_counts[user_id]
        if current_time - timestamp < SPAM_TIME_WINDOW
    ]
    
    bot.state.user_message_counts[user_id].append(current_time)
    
    # Check for spam
    if len(bot.state.user_message_counts[user_id]) > SPAM_MESSAGE_THRESHOLD:
        bot.state.user_cooldowns[user_id] = current_time + COOLDOWN_DURATION
        bot.state.user_message_counts[user_id] = []
        return False, f"User put on {COOLDOWN_DURATION}s cooldown for spam"
    
    return True, None

async def generate_response_and_reply(message: discord.Message, prompt: str, history: List[str], image_url: Optional[str] = None):
    """Enhanced response generation with better error handling and typing simulation"""
    try:
        # Anti-detection: Enhanced realistic typing simulation
        if bot.state.realistic_typing:
            # Random chance to not type at all (like quick responses)
            if random.random() < 0.3:  # 30% chance of instant response
                typing_delay = random.uniform(0.5, 1.5)
                await asyncio.sleep(typing_delay)
            else:
                # Calculate realistic typing delay based on message length
                base_delay = random.uniform(3.0, 8.0)  # Longer, more human delays
                typing_speed = random.uniform(40, 70)  # More realistic WPM range
                char_delay = len(prompt) / (typing_speed * 5)
                total_delay = base_delay + char_delay
                
                # Anti-detection: Random reading delay before typing
                reading_delay = random.uniform(1.0, 4.0)
                await asyncio.sleep(reading_delay)
                
                async with message.channel.typing():
                    # Anti-detection: Sometimes stop and start typing
                    if random.random() < 0.2:  # 20% chance
                        await asyncio.sleep(total_delay * 0.3)
                        # Brief pause (like rethinking response)
                        await asyncio.sleep(random.uniform(1.0, 2.0))
                    
                    await asyncio.sleep(min(total_delay, 25.0))  # Cap at 25 seconds
        
        # Generate AI response
        if image_url:
            response = await generate_response_image(prompt, bot.state.instructions, image_url, history)
        else:
            response = await generate_response(prompt, bot.state.instructions, history)
        
        if not response:
            logger.warning("Empty response from AI")
            return
        
        # Split response into chunks
        chunks = split_response(response)
        
        # Limit number of chunks to prevent spam
        if len(chunks) > 3:
            chunks = chunks[:3]
            logger.info("Response truncated to prevent spam")
        
        # Send response chunks
        for i, chunk in enumerate(chunks):
            # Apply mention filtering
            if DISABLE_MENTIONS:
                chunk = chunk.replace("@", "@\u200b")
            
            # Apply anti-age-ban filtering
            if bot.state.anti_age_ban:
                chunk = re.sub(
                    r"(?<!\d)([0-9]|1[0-2])(?!\d)|\b(zero|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\b",
                    "\u200b",
                    chunk,
                    flags=re.IGNORECASE,
                )
            
            # Log interaction
            timestamp = datetime.now().strftime("[%H:%M:%S]")
            logger.info(f"{timestamp} {message.author.name}: {prompt}")
            logger.info(f"{timestamp} Responding to {message.author.name}: {chunk}")
            print(f'{timestamp} {message.author.name}: {prompt}')
            print(f'{timestamp} Responding to {message.author.name}: {chunk}')
            print_separator()
            
            try:
                # Anti-detection: Add delay between chunks and random send delays
                if i > 0 and bot.state.realistic_typing:
                    await asyncio.sleep(random.uniform(1.5, 4.0))
                
                # Anti-detection: Random delay before sending (like double-checking response)
                pre_send_delay = random.uniform(0.2, 1.2)
                await asyncio.sleep(pre_send_delay)
                
                # Send message
                if isinstance(message.channel, discord.DMChannel):
                    sent_message = await message.channel.send(chunk)
                else:
                    sent_message = await message.reply(
                        chunk,
                        mention_author=config["bot"].get("reply_ping", True)
                    )
                
                # Record bot response in conversation history (only first chunk to avoid spam)
                if i == 0:
                    update_message_history(message.author.id, chunk, is_bot_response=True)
                
                # Update conversation timestamp
                conv_key = f"{message.author.id}-{message.channel.id}"
                bot.state.active_conversations[conv_key] = time.time()
                
            except discord.errors.HTTPException as e:
                logger.error(f"HTTP error sending message: {e}")
                await webhook_log(message, str(e))
                break
            except discord.errors.Forbidden as e:
                logger.error("Missing permissions to send message")
                await webhook_log(message, "Missing permissions")
                break
            except Exception as e:
                logger.error(f"Unexpected error sending message: {e}")
                await webhook_log(message, str(e))
                break
        
        return response
        
    except Exception as e:
        logger.error(f"Error in generate_response_and_reply: {e}")
        await webhook_log(message, str(e))

@bot.event
async def on_message(message: discord.Message):
    """Enhanced message handling with improved security and batching"""
    try:
        # Basic filtering - always ignore own messages unless they're commands
        if message.author.id == bot.user.id:
            # Only process if it's a command with the prefix
            if message.content.startswith(PREFIX):
                await bot.process_commands(message)
            return
        
        # Check other ignored users (but allow owner)
        if should_ignore_message(message) and message.author.id != bot.state.owner_id:
            return
        
        # Handle commands from other users
        if message.content.startswith(PREFIX):
            await bot.process_commands(message)
            return
        
        # Check if message should trigger response
        if not is_trigger_message(message) or bot.state.paused:
            return
        
        # Enhanced spam and cooldown check
        can_proceed, reason = await check_spam_and_cooldown(message.author.id)
        if not can_proceed:
            logger.info(f"Blocked message from {message.author.name}: {reason}")
            return
        
        # Channel-specific checks
        channel_id = message.channel.id
        if (
            not isinstance(message.channel, (discord.DMChannel, discord.GroupChannel))
            and channel_id not in bot.state.active_channels
        ):
            return
        
        # Add to message queue for processing
        if channel_id not in bot.state.message_queues:
            bot.state.message_queues[channel_id] = deque()
            bot.state.processing_locks[channel_id] = Lock()
        
        bot.state.message_queues[channel_id].append(message)
        
        # Process queue if not already processing
        if not bot.state.processing_locks[channel_id].locked():
            asyncio.create_task(process_message_queue(channel_id))
            
    except Exception as e:
        logger.error(f"Error in on_message: {e}")

async def process_message_queue(channel_id: int):
    """Enhanced message queue processing with batching support"""
    async with bot.state.processing_locks[channel_id]:
        while bot.state.message_queues[channel_id]:
            message = bot.state.message_queues[channel_id].popleft()
            batch_key = f"{message.author.id}-{channel_id}"
            current_time = time.time()
            
            try:
                if bot.state.batch_messages:
                    # Initialize batch if not exists
                    if batch_key not in bot.state.user_message_batches:
                        first_image_url = (
                            message.attachments[0].url if message.attachments else None
                        )
                        bot.state.user_message_batches[batch_key] = {
                            "messages": [],
                            "last_time": current_time,
                            "image_url": first_image_url,
                        }
                    
                    batch = bot.state.user_message_batches[batch_key]
                    batch["messages"].append(message)
                    
                    # Wait for additional messages
                    await asyncio.sleep(bot.state.batch_wait_time)
                    
                    # Collect additional messages from same user
                    while bot.state.message_queues[channel_id]:
                        next_message = bot.state.message_queues[channel_id][0]
                        if (
                            next_message.author.id == message.author.id
                            and not next_message.content.startswith(PREFIX)
                        ):
                            next_message = bot.state.message_queues[channel_id].popleft()
                            # Avoid duplicates
                            if next_message.content not in [m.content for m in batch["messages"]]:
                                batch["messages"].append(next_message)
                            
                            # Update image if not already set
                            if not batch["image_url"] and next_message.attachments:
                                batch["image_url"] = next_message.attachments[0].url
                        else:
                            break
                    
                    # Process batched messages
                    messages_to_process = batch["messages"]
                    combined_content = " | ".join([msg.content for msg in messages_to_process])
                    
                    # Get conversation history
                    history = bot.state.message_history.get(message.author.id, [])
                    
                    # Update history with new content
                    update_message_history(message.author.id, combined_content)
                    
                    # Generate and send response
                    await generate_response_and_reply(
                        message, combined_content, history, batch["image_url"]
                    )
                    
                    # Clean up batch
                    if batch_key in bot.state.user_message_batches:
                        del bot.state.user_message_batches[batch_key]
                
                else:
                    # Process single message
                    history = bot.state.message_history.get(message.author.id, [])
                    update_message_history(message.author.id, message.content)
                    
                    image_url = message.attachments[0].url if message.attachments else None
                    await generate_response_and_reply(message, message.content, history, image_url)
                
            except Exception as e:
                logger.error(f"Error processing message in queue: {e}")
                await webhook_log(message, str(e))

@bot.event
async def on_error(event: str, *args, **kwargs):
    """Enhanced error handling"""
    logger.error(f"Error in event {event}: {args}")

@bot.event
async def on_command_error(ctx, error):
    """Enhanced command error handling"""
    if isinstance(error, commands.CommandNotFound):
        return  # Ignore unknown commands
    
    logger.error(f"Command error in {ctx.command}: {error}")
    
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ You don't have permission to use this command.")
    elif isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"⏰ Command on cooldown. Try again in {error.retry_after:.2f}s")
    else:
        await ctx.send("❌ An error occurred while executing the command.")

def main():
    """Main function to start the bot with ultra-robust keep-alive"""
    try:
        logger.info("🔥 Starting ULTRA-ROBUST 24/7 Discord AI Selfbot...")
        
        # Start all keep-alive systems immediately
        start_all_keep_alive_systems()
        time.sleep(2)  # Give systems time to start
        
        if not TOKEN or TOKEN == "your_discord_token_here":
            logger.error("DISCORD_TOKEN not found or not set in environment variables")
            print(f"{Fore.RED}Error: Discord token not configured properly.{Style.RESET_ALL}")
            print(f"\n{Fore.YELLOW}Current token value: {TOKEN[:20] + '...' if TOKEN and len(TOKEN) > 20 else TOKEN}{Style.RESET_ALL}")
            print(f"\n{Fore.CYAN}📋 To get your Discord token:{Style.RESET_ALL}")
            print("1. Open Discord in your browser (not the app)")
            print("2. Press F12 to open Developer Tools")
            print("3. Go to the Network tab")
            print("4. Send a message or refresh Discord")
            print("5. Look for a request and find 'Authorization' in headers")
            print("6. Copy the token value (without 'Bearer' prefix)")
            print("7. Edit config/.env and replace 'your_discord_token_here' with your token")
            print(f"\n{Fore.YELLOW}Note: User tokens start with 'MTA', 'MTU', 'Nz', 'OD', etc.{Style.RESET_ALL}")
            return
        
        # Additional token validation before connecting
        from utils.helpers import validate_discord_token
        if not validate_discord_token(TOKEN):
            logger.error("Discord token failed validation")
            print(f"{Fore.RED}Error: Token format appears invalid.{Style.RESET_ALL}")
            print(f"Token length: {len(TOKEN)} characters")
            print(f"Token preview: {TOKEN[:10]}{'*' * (len(TOKEN) - 20)}{TOKEN[-10:] if len(TOKEN) > 20 else ''}")
            print(f"\n{Fore.YELLOW}Valid user tokens should:{Style.RESET_ALL}")
            print("- Be 50+ characters long")
            print("- Start with letters like 'MTA', 'MTU', 'Nz', 'OD', etc.")
            print("- Contain only letters, numbers, underscores, and hyphens")
            return
        
        logger.info("Starting Discord AI Selfbot with ULTRA-ROBUST keep-alive...")
        print(f"{Fore.GREEN}🚀 Token validation passed, connecting to Discord with 24/7 mode...{Style.RESET_ALL}")
        
        # Main bot loop with auto-restart capability
        max_restarts = 10
        restart_count = 0
        
        while restart_count < max_restarts and keep_alive_state.running:
            try:
                bot.run(TOKEN, log_handler=None)  # Disable discord.py's default logging
                
                # If we get here, bot stopped normally
                if keep_alive_state.restart_requested:
                    restart_count += 1
                    logger.info(f"Bot restart requested ({restart_count}/{max_restarts})")
                    keep_alive_state.restart_requested = False
                    time.sleep(5)  # Brief pause before restart
                    continue
                else:
                    break
                    
            except discord.LoginFailure as e:
                logger.error(f"Discord login failed: {e}")
                print(f"{Fore.RED}Error: Discord login failed.{Style.RESET_ALL}")
                break
            except Exception as e:
                restart_count += 1
                logger.error(f"Bot crashed ({restart_count}/{max_restarts}): {e}")
                if restart_count < max_restarts:
                    time.sleep(10)  # Wait before restart
                    continue
                else:
                    break
        
        if restart_count >= max_restarts:
            logger.error("Maximum restart attempts reached")
        
    except KeyboardInterrupt:
        logger.info("Bot shutdown requested by user")
        print(f"\n{Fore.YELLOW}Bot shutdown requested. Cleaning up...{Style.RESET_ALL}")
    except Exception as e:
        logger.error(f"Critical error: {e}")
        print(f"{Fore.RED}Critical error: {e}{Style.RESET_ALL}")
    finally:
        # Cleanup
        keep_alive_state.running = False
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            if not loop.is_closed():
                loop.run_until_complete(stop_health_server())
        except Exception:
            pass
        
        logger.info("🔥 ULTRA-ROBUST 24/7 system shutdown complete")

if __name__ == "__main__":
    main()
