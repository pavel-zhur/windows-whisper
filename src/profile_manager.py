import yaml
import os
import logging

logger = logging.getLogger("whisper_app")

class ProfileManager:
    """Manages transformation profiles loaded from profiles.yaml"""
    
    def __init__(self, profiles_file="profiles.yaml"):
        """Initialize the profile manager"""
        self.profiles_file = profiles_file
        self.profiles = {}
        self.load_profiles()
    
    def load_profiles(self):
        """Load profiles from YAML file"""
        try:
            if not os.path.exists(self.profiles_file):
                logger.error(f"Profiles file not found: {self.profiles_file}")
                raise FileNotFoundError(f"Profiles file not found: {self.profiles_file}")
            
            with open(self.profiles_file, 'r', encoding='utf-8') as file:
                data = yaml.safe_load(file)
                
            if not data or 'profiles' not in data:
                logger.error("Invalid profiles.yaml format - missing 'profiles' section")
                raise ValueError("Invalid profiles.yaml format")
                
            self.profiles = data['profiles']
            logger.info(f"Loaded {len(self.profiles)} profiles from {self.profiles_file}")
            
            # Log loaded profiles
            for profile_num, profile in self.profiles.items():
                name = profile.get('name', f'Profile {profile_num}')
                logger.debug(f"Profile {profile_num}: {name}")
                
        except Exception as e:
            logger.error(f"Failed to load profiles: {e}")
            raise
    
    def get_profile(self, profile_number):
        """Get a specific profile by number"""
        return self.profiles.get(profile_number, {})
    
    def has_profile(self, profile_number):
        """Check if a profile exists"""
        return profile_number in self.profiles
    
    def get_all_profiles(self):
        """Get all profiles"""
        return self.profiles
    
    def get_profile_name(self, profile_number):
        """Get the name of a profile"""
        profile = self.get_profile(profile_number)
        return profile.get('name', f'Profile {profile_number}')