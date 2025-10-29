"""
Configuration settings for Eyrie application
"""
import os
from typing import List
from enum import Enum


class DeploymentMode(str, Enum):
    DEVELOPMENT = "dev"
    PRODUCTION = "prod"
    STAGING = "staging"


class Settings:
    """Configuration settings for Eyrie application"""

    def __init__(self):
        # Core API Configuration
        self.internal_backend_url: str = os.getenv('INTERNAL_BACKEND_URL', 'http://eyrie_backend:5000')
        self.external_base_path: str = os.getenv('EXTERNAL_BASE_PATH', '').rstrip('/')

        # Security Configuration
        self.secret_key: str = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

        # Database Configuration
        self.mongo_uri: str = os.getenv('MONGO_URI', 'mongodb://localhost:27017')
        self.mongo_db: str = os.getenv('MONGO_DB', 'eyrie_dev')

        # Environment Configuration
        self.environment: str = os.getenv('ENVIRONMENT', 'development')
        self.debug: bool = os.getenv('DEBUG', 'False').lower() == 'true'

        # CORS Configuration
        self.cors_origins: List[str] = ["*"]  # TODO: Make configurable

        # Backend fallback URLs for connectivity testing
        self.backend_fallback_urls: List[str] = [
            self.internal_backend_url,
            'http://eyrie-backend:5000',  # Different naming convention
            'http://localhost:8000',      # Local fallback
            'http://127.0.0.1:8000',      # IP fallback
        ]

        # Flask Configuration
        self.session_cookie_path: str = self.external_base_path or '/'
        self.application_root: str = self.external_base_path

    @property
    def is_development(self) -> bool:
        """Check if running in development mode"""
        return self.environment.lower() in ['development', 'dev']

    @property
    def is_production(self) -> bool:
        """Check if running in production mode"""
        return self.environment.lower() in ['production', 'prod']


# Global settings instance
settings = Settings()
