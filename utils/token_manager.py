"""
Token management utilities for secure storage and retrieval of GitLab access tokens
"""

import os
import json
from pathlib import Path

class TokenManager:
    def __init__(self, app_dir=None):
        """Initialize token manager
        
        Args:
            app_dir (str): Directory to store token file. If None, uses current directory.
        """
        if app_dir is None:
            app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        self.app_dir = Path(app_dir)
        self.token_file = self.app_dir / "token.json"
        self.llm_token_file = self.app_dir / "llm_token.json"
        
    def save_token(self, token, gitlab_url="https://gitlab.com"):
        """Save GitLab access token to local file
        
        Args:
            token (str): GitLab Personal Access Token
            gitlab_url (str): GitLab instance URL
            
        Returns:
            bool: True if saved successfully, False otherwise
        """
        try:
            token_data = {
                "token": token,
                "gitlab_url": gitlab_url
            }
            
            with open(self.token_file, 'w') as f:
                json.dump(token_data, f, indent=2)
            
            # Set file permissions to be readable only by owner (on Unix-like systems)
            if hasattr(os, 'chmod'):
                os.chmod(self.token_file, 0o600)
                
            return True
            
        except Exception as e:
            print(f"Error saving token: {e}")
            return False
    
    def load_token(self):
        """Load GitLab access token from local file
        
        Returns:
            tuple: (token: str or None, gitlab_url: str or None, success: bool)
        """
        try:
            if not self.token_file.exists():
                return None, None, False
                
            with open(self.token_file, 'r') as f:
                token_data = json.load(f)
            
            token = token_data.get("token")
            gitlab_url = token_data.get("gitlab_url", "https://gitlab.com")
            
            if token:
                return token, gitlab_url, True
            else:
                return None, None, False
                
        except Exception as e:
            print(f"Error loading token: {e}")
            return None, None, False
    
    def delete_token(self):
        """Delete the stored token file
        
        Returns:
            bool: True if deleted successfully, False otherwise
        """
        try:
            if self.token_file.exists():
                self.token_file.unlink()
            return True
        except Exception as e:
            print(f"Error deleting token: {e}")
            return False
    
    def token_exists(self):
        """Check if token file exists
        
        Returns:
            bool: True if token file exists, False otherwise
        """
        return self.token_file.exists()
    
    def save_llm_token(self, token, provider="vertafore"):
        """Save LLM API token to local file
        
        Args:
            token (str): LLM API Token
            provider (str): LLM provider (openai, anthropic, etc.)
            
        Returns:
            bool: True if saved successfully, False otherwise
        """
        try:
            token_data = {
                "token": token,
                "provider": provider
            }
            
            with open(self.llm_token_file, 'w') as f:
                json.dump(token_data, f, indent=2)
            
            # Set file permissions to be readable only by owner (on Unix-like systems)
            if hasattr(os, 'chmod'):
                os.chmod(self.llm_token_file, 0o600)
                
            return True
            
        except Exception as e:
            print(f"Error saving LLM token: {e}")
            return False
    
    def load_llm_token(self):
        """Load LLM API token from local file
        
        Returns:
            str or None: LLM token if found, None otherwise
        """
        try:
            if not self.llm_token_file.exists():
                return None
                
            with open(self.llm_token_file, 'r') as f:
                token_data = json.load(f)
            
            return token_data.get("token")
                
        except Exception as e:
            print(f"Error loading LLM token: {e}")
            return None
    
    def delete_llm_token(self):
        """Delete the stored LLM token file
        
        Returns:
            bool: True if deleted successfully, False otherwise
        """
        try:
            if self.llm_token_file.exists():
                self.llm_token_file.unlink()
            return True
        except Exception as e:
            print(f"Error deleting LLM token: {e}")
            return False