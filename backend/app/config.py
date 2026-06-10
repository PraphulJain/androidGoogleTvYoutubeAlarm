"""
Application configuration
"""
import os


class Config:
    """Application configuration class"""
    
    # API Configuration
    API_HOST = os.getenv("API_HOST", "0.0.0.0")
    API_PORT = int(os.getenv("API_PORT", 5127))
    
    # Security
    API_PASSWORD = os.getenv("API_PASSWORD", "")
    
    # Google TV Configuration
    TV_IP = os.getenv("TV_IP", "")
    TV_PORT = os.getenv("TV_PORT", "5555")
    
    # Database
    DB_PATH = os.getenv("DB_PATH", "/app/data/alarms.db")
    
    # Logging
    LOGTAIL_TOKEN = os.getenv("LOGTAIL_TOKEN", "MD82ZsA4UX7nf4CSTvadtvfo")
    
    # Timezone
    TIMEZONE = os.getenv("TIMEZONE", "UTC")
