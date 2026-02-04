"""
Configuration settings for Eyrie application
"""
import os
from typing import List, Dict
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

        # Analysis Results Paths for different pipeline software
        self.analysis_results_paths: Dict[str, str] = {
            "trana": os.getenv('TRANA_ANALYSIS_RESULTS', '/app/analysis-files/results/trana'),
            "metaval": os.getenv('METAVAL_ANALYSIS_RESULTS', '/app/analysis-files/results/metaval'),
        }

    @property
    def is_development(self) -> bool:
        """Check if running in development mode"""
        return self.environment.lower() in ['development', 'dev']

    @property
    def is_production(self) -> bool:
        """Check if running in production mode"""
        return self.environment.lower() in ['production', 'prod']

    @property
    def trends_config(self):
        """Trends analysis configuration"""
        return {
            'group_by_options': [
                {'value': 'sequencing_run_id', 'label': 'Sequencing Run ID', 'selected': True},
                {'value': 'library_prep_kit', 'label': 'Library Prep Kit'},
                {'value': 'library_prep_kit_lot_number', 'label': 'Library Prep Kit Lot Number'},
                {'value': 'extraction_kit', 'label': 'Extraction Kit'},
                {'value': 'extraction_kit_lot_number', 'label': 'Extraction Kit Lot Number'},
                {'value': 'tissue', 'label': 'Tissue'},
            ],
            'metrics': [
                {'value': 'number_of_reads', 'label': 'Number of Reads', 'selected': True},
                {'value': 'mean_read_quality', 'label': 'Mean Read Quality'},
                {'value': 'mean_read_length', 'label': 'Mean Read Length'},
                {'value': 'read_length_n50', 'label': 'Read Length N50'},
                {'value': 'total_contaminants_abundance', 'label': 'Total Contaminants Abundance per Sample'},
                {'value': 'library_concentration', 'label': 'Library Concentration'},
            ],
            'read_quality_filtering': [
                {'value': 'all', 'label': 'All Data', 'selected': True},
                {'value': 'processed', 'label': 'Processed Reads Only'},
                {'value': 'unprocessed', 'label': 'Unprocessed Reads Only'}
            ],
            'predefined_filters': {
                'classifications': [
                    {'value': '16S', 'label': '16S'},
                    {'value': 'ITS', 'label': 'ITS'}
                ],
                'qc': [
                    {'value': 'passed', 'label': 'Passed'},
                    {'value': 'failed', 'label': 'Failed'},
                    {'value': 'unprocessed', 'label': 'Unprocessed'}
                ],
                'sample_types': [
                    {'value': 'validation', 'label': 'Validation'},
                    {'value': 'patient', 'label': 'Patient'},
                    {'value': 'negative control', 'label': 'Negative Control'},
                    {'value': 'positive control', 'label': 'Positive Control'}
                ]
            }
        }


# Global settings instance
settings = Settings()
