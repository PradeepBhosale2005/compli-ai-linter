# Goal: Create a centralized configuration file using Pydantic for robust settings management.

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Centralized configuration management using Pydantic BaseSettings.
    
    This class automatically loads configuration from environment variables
    and .env files, providing type validation and IDE support.
    """
    
    # OpenAI Configuration
    OPENAI_API_KEY: str
    
    # Azure OpenAI Configuration
    AZURE_OPENAI_ENDPOINT: str
    AZURE_OPENAI_API_VERSION: str = "2024-02-01"
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT: str
    AZURE_OPENAI_CHAT_DEPLOYMENT: str
    
    class Config:
        """Pydantic configuration to load variables from .env file."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Create a single instance that can be imported throughout the application
settings = Settings()