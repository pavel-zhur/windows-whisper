#!/usr/bin/env python3
import os
import logging
import shutil
from dotenv import load_dotenv, set_key, find_dotenv

logger = logging.getLogger("whisper_app")

class ConfigManager:
    """Manages configuration including .env file operations"""
    
    def __init__(self):
        self.env_file = find_dotenv() or ".env"
        self.env_example_file = ".env.example"
        
    def ensure_env_file_exists(self):
        """Ensure .env file exists, create from .env.example if needed"""
        if not os.path.exists(self.env_file):
            if os.path.exists(self.env_example_file):
                try:
                    shutil.copy2(self.env_example_file, self.env_file)
                    logger.info(f"Created {self.env_file} from {self.env_example_file}")
                except Exception as e:
                    logger.error(f"Failed to create .env file: {e}")
                    # Create empty .env file
                    with open(self.env_file, 'w') as f:
                        f.write("# Windows Whisper Configuration\n")
            else:
                # Create empty .env file
                with open(self.env_file, 'w') as f:
                    f.write("# Windows Whisper Configuration\n")
                logger.info(f"Created empty {self.env_file}")
                
    def get_api_key(self):
        """Get the current API key from environment"""
        load_dotenv(self.env_file)
        return os.getenv("OPENAI_API_KEY", "").strip()
        
    def save_api_key(self, api_key):
        """Save API key to .env file safely"""
        try:
            self.ensure_env_file_exists()
            
            # Create backup
            backup_file = f"{self.env_file}.backup"
            if os.path.exists(self.env_file):
                shutil.copy2(self.env_file, backup_file)
                
            # Update the key
            success = set_key(self.env_file, "OPENAI_API_KEY", api_key)
            
            if success:
                # Reload environment variables
                load_dotenv(self.env_file, override=True)
                logger.info("API key saved successfully")
                
                # Remove backup on success
                if os.path.exists(backup_file):
                    os.remove(backup_file)
                    
                return True
            else:
                logger.error("Failed to save API key")
                # Restore backup
                if os.path.exists(backup_file):
                    shutil.move(backup_file, self.env_file)
                return False
                
        except Exception as e:
            logger.error(f"Error saving API key: {e}")
            # Restore backup
            backup_file = f"{self.env_file}.backup"
            if os.path.exists(backup_file):
                try:
                    shutil.move(backup_file, self.env_file)
                except:
                    pass
            return False
            
    def validate_api_key_format(self, api_key):
        """Basic validation of API key format"""
        if not api_key or not isinstance(api_key, str):
            return False, "API key cannot be empty"
            
        api_key = api_key.strip()
        
        if len(api_key) < 10:
            return False, "API key is too short"
            
        # OpenAI keys typically start with sk-
        if not api_key.startswith("sk-"):
            return False, "API key should start with 'sk-'"
            
        # Basic length check for OpenAI keys
        if len(api_key) < 40:
            return False, "API key appears to be too short"
            
        return True, "API key format looks valid"
        
    def get_env_file_path(self):
        """Get the path to the .env file"""
        return os.path.abspath(self.env_file)