import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Configuration class for Chainlit service"""
    
    # OpenAI settings
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    OPENAI_MODEL = os.environ.get('OPENAI_MODEL', 'gpt-3.5-turbo')
    
    # Redis settings
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379')
    
    # Flask app integration
    FLASK_SERVICE_URL = os.environ.get('FLASK_SERVICE_URL', 'http://localhost:5000')
    
    # Chainlit settings
    CHAINLIT_HOST = os.environ.get('CHAINLIT_HOST', '0.0.0.0')
    CHAINLIT_PORT = int(os.environ.get('CHAINLIT_PORT', 8000))
    
    # Agent settings
    MAX_CONVERSATION_HISTORY = int(os.environ.get('MAX_CONVERSATION_HISTORY', 50))
    DEFAULT_AGENT = os.environ.get('DEFAULT_AGENT', 'general')
    
    # Rate limiting
    RATE_LIMIT_FREE = int(os.environ.get('RATE_LIMIT_FREE', 10))  # messages per hour
    RATE_LIMIT_PREMIUM = int(os.environ.get('RATE_LIMIT_PREMIUM', 100))  # messages per hour
    
    # Credit costs
    CREDIT_COST_PER_MESSAGE = int(os.environ.get('CREDIT_COST_PER_MESSAGE', 1))
    
    # Demo mode (for when OpenAI API is not available)
    DEMO_MODE = os.environ.get('DEMO_MODE', 'false').lower() == 'true'
    
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        if not cls.DEMO_MODE and not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY environment variable is required (or set DEMO_MODE=true)")
        return True

# Global config instance
config = Config() 