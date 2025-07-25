#!/usr/bin/env python3
"""
Render-compatible startup script for Discord AI Selfbot
Handles cloud deployment requirements and environment setup
"""

import os
import sys
import asyncio
import logging
from pathlib import Path

# Configure logging for cloud deployment
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def setup_cloud_environment():
    """Setup environment for cloud deployment"""
    logger.info("Setting up cloud environment...")
    
    # Create necessary directories
    dirs_to_create = ['config', 'data', 'temp_keepalive']
    for dir_name in dirs_to_create:
        Path(dir_name).mkdir(exist_ok=True)
        logger.info(f"Created directory: {dir_name}")
    
    # Check for required environment variables
    required_vars = ['DISCORD_TOKEN']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {missing_vars}")
        logger.info("Please set these environment variables in your Render dashboard:")
        for var in missing_vars:
            logger.info(f"  - {var}")
        sys.exit(1)
    
    # Optional environment variables
    optional_vars = {
        'GROQ_API_KEY': 'AI functionality will be limited without this',
        'OPENAI_API_KEY': 'Fallback AI provider, recommended',
        'ERROR_WEBHOOK_URL': 'Error notifications will be disabled'
    }
    
    for var, warning in optional_vars.items():
        if not os.getenv(var):
            logger.warning(f"Optional environment variable {var} not set: {warning}")
    
    logger.info("Environment setup complete")

def main():
    """Main startup function for Render deployment"""
    try:
        logger.info("Starting Discord AI Selfbot on Render...")
        
        # Setup cloud environment
        setup_cloud_environment()
        
        # Import and run the main bot
        from main import main as bot_main
        bot_main()
        
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()