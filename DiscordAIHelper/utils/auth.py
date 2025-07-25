
"""
User authorization utilities for Discord AI Selfbot
Manages authorized users and permission checking
"""

import yaml
import logging
from typing import List, Set, Optional
from .helpers import resource_path

logger = logging.getLogger(__name__)

class AuthManager:
    """Manages authorized users and permissions"""
    
    def __init__(self):
        self.authorized_users: Set[int] = set()
        self.owner_id: Optional[int] = None
        self.allowed_commands: List[str] = []
        self.owner_only_commands: List[str] = []
        self.load_authorized_users()
    
    def load_authorized_users(self) -> bool:
        """Load authorized users from configuration file"""
        try:
            auth_file = resource_path("config/authorized_users.yaml")
            
            with open(auth_file, 'r', encoding='utf-8') as f:
                auth_config = yaml.safe_load(f)
            
            # Load authorized user IDs
            user_ids = auth_config.get('authorized_users', [])
            self.authorized_users = {int(uid) for uid in user_ids if uid}
            
            # Load owner ID (first user in list is typically owner)
            if user_ids:
                self.owner_id = int(user_ids[0])
            
            # Load permission settings
            permissions = auth_config.get('permissions', {})
            self.allowed_commands = permissions.get('allowed_commands', [])
            self.owner_only_commands = permissions.get('owner_only_commands', [])
            
            logger.info(f"Loaded {len(self.authorized_users)} authorized users: {list(self.authorized_users)}")
            logger.info(f"Owner ID set to: {self.owner_id}")
            logger.info(f"Allowed commands: {len(self.allowed_commands)}")
            return True
            
        except FileNotFoundError:
            logger.warning("Authorized users file not found, creating default")
            self.create_default_auth_file()
            return self.load_authorized_users()  # Try loading again after creation
        except Exception as e:
            logger.error(f"Error loading authorized users: {e}")
            return False
    
    def create_default_auth_file(self) -> bool:
        """Create default authorized users file"""
        try:
            auth_file = resource_path("config/authorized_users.yaml")
            
            default_config = {
                'authorized_users': [1007652090925043753],  # Your owner ID
                'permissions': {
                    'allowed_commands': [
                        'help', 'stats', 'channels', 'toggleactive', 
                        'ignore', 'unignore', 'toggledm', 'togglegc',
                        'pause', 'resume', 'cleanup', 'system'
                    ],
                    'owner_only_commands': [
                        'reload', 'restart', 'shutdown', 'maintenance',
                        'config', 'prompt', 'testwh', 'logs'
                    ]
                }
            }
            
            with open(auth_file, 'w', encoding='utf-8') as f:
                yaml.dump(default_config, f, default_flow_style=False, indent=2)
            
            logger.info("Created default authorized users file")
            return True
            
        except Exception as e:
            logger.error(f"Error creating default auth file: {e}")
            return False
    
    def is_authorized(self, user_id: int) -> bool:
        """Check if user is authorized to use bot commands"""
        return user_id in self.authorized_users
    
    def is_owner(self, user_id: int) -> bool:
        """Check if user is the bot owner"""
        return user_id == self.owner_id
    
    def can_use_command(self, user_id: int, command_name: str) -> bool:
        """Check if user can use a specific command"""
        if self.is_owner(user_id):
            return True
        
        if not self.is_authorized(user_id):
            return False
        
        # Check if command is owner-only
        if command_name in self.owner_only_commands:
            return False
        
        # Check if command is in allowed list
        return command_name in self.allowed_commands
    
    def add_user(self, user_id: int) -> bool:
        """Add user to authorized list"""
        try:
            if user_id in self.authorized_users:
                return False  # Already authorized
            
            self.authorized_users.add(user_id)
            return self.save_authorized_users()
            
        except Exception as e:
            logger.error(f"Error adding user {user_id}: {e}")
            return False
    
    def remove_user(self, user_id: int) -> bool:
        """Remove user from authorized list"""
        try:
            if user_id == self.owner_id:
                return False  # Cannot remove owner
            
            if user_id not in self.authorized_users:
                return False  # Not authorized
            
            self.authorized_users.remove(user_id)
            return self.save_authorized_users()
            
        except Exception as e:
            logger.error(f"Error removing user {user_id}: {e}")
            return False
    
    def save_authorized_users(self) -> bool:
        """Save authorized users to configuration file"""
        try:
            auth_file = resource_path("config/authorized_users.yaml")
            
            config = {
                'authorized_users': list(self.authorized_users),
                'permissions': {
                    'allowed_commands': self.allowed_commands,
                    'owner_only_commands': self.owner_only_commands
                }
            }
            
            with open(auth_file, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, indent=2)
            
            logger.info("Saved authorized users configuration")
            return True
            
        except Exception as e:
            logger.error(f"Error saving authorized users: {e}")
            return False
    
    def get_authorized_users(self) -> List[int]:
        """Get list of authorized user IDs"""
        return list(self.authorized_users)
    
    def get_stats(self) -> dict:
        """Get authorization statistics"""
        return {
            'total_authorized': len(self.authorized_users),
            'owner_id': self.owner_id,
            'allowed_commands': len(self.allowed_commands),
            'owner_only_commands': len(self.owner_only_commands)
        }

# Global auth manager instance
_auth_manager = None

def get_auth_manager() -> AuthManager:
    """Get global auth manager instance"""
    global _auth_manager
    if _auth_manager is None:
        _auth_manager = AuthManager()
    return _auth_manager

def is_authorized(user_id: int) -> bool:
    """Quick check if user is authorized"""
    return get_auth_manager().is_authorized(user_id)

def is_owner(user_id: int) -> bool:
    """Quick check if user is owner"""
    return get_auth_manager().is_owner(user_id)

def can_use_command(user_id: int, command_name: str) -> bool:
    """Quick check if user can use command"""
    return get_auth_manager().can_use_command(user_id, command_name)
