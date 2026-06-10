"""
Application configuration
"""
import os


class Config:
    """Application configuration class"""
    
    # API Configuration
    API_HOST = os.getenv("API_HOST", "0.0.0.0")
    API_PORT = int(os.getenv("API_PORT", 8000))
    
    # Google TV Configuration
    TV_IP = os.getenv("TV_IP", "")
    TV_PORT = int(os.getenv("TV_PORT", 5555))
    
    # Timezone
    TIMEZONE = os.getenv("TIMEZONE", "UTC")
