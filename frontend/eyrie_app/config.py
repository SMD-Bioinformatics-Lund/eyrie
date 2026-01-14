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
            'categories': [
                {'value': 'sample_id', 'label': 'Sample ID'},
                {'value': 'dominant_species', 'label': 'Dominant Species'},
                {'value': 'sample_type', 'label': 'Sample Type'},
                {'value': 'tissue', 'label': 'Tissue'},
                {'value': 'spike_concentration', 'label': 'Spike Concentration'},
                {'value': 'dilution', 'label': 'Dilution'},
                {'value': 'read_quality_filtering', 'label': 'Read Quality Filtering'},
                {'value': 'classification_type', 'label': 'Classification Type'},
                {'value': 'extraction_kit', 'label': 'Extraction Kit'},
                {'value': 'library_prep_kit', 'label': 'Library Prep Kit'},
            ],
            'metrics': [
                {'value': 'number_of_reads', 'label': 'Number of Reads'},
                {'value': 'mean_read_quality', 'label': 'Mean Read Quality (Q-score)'},
                {'value': 'mean_read_length', 'label': 'Mean Read Length (bp)'},
                {'value': 'read_length_n50', 'label': 'Read Length N50 (bp)'},
                {'value': 'species_frequency', 'label': 'Species Frequency (%)'},
                {'value': 'abundance_percentage', 'label': 'Abundance Percentage (%)'},
                {'value': 'sample_count', 'label': 'Sample Count'},
                {'value': 'contaminants_count', 'label': 'Contaminants Count'},
                {'value': 'top_hits_count', 'label': 'Top Hits Count'},
                {'value': 'qc_pass_rate', 'label': 'QC Pass Rate (%)'},
                {'value': 'total_bases', 'label': 'Total Bases'},
                {'value': 'library_concentration', 'label': 'Library Concentration (ng/μL)'},
                {'value': 'multiple_finds_rate', 'label': 'Multiple Finds Rate (%)'},
            ],
            'chart_types': [
                {'value': 'line', 'label': 'Line'},
                {'value': 'bar', 'label': 'Bar'},
                {'value': 'stacked_area', 'label': 'Stacked Area'}
            ],
            'time_ranges': [
                {'value': '7', 'label': 'Last 7 Days'},
                {'value': '30', 'label': 'Last 30 Days'},
                {'value': '90', 'label': 'Last 90 Days'},
                {'value': '365', 'label': 'Last Year'},
                {'value': 'all', 'label': 'All Time', 'selected': True}
            ],
            'group_by_options': [
                {'value': 'day', 'label': 'Daily', 'selected': True},
                {'value': 'week', 'label': 'Weekly'},
                {'value': 'month', 'label': 'Monthly'},
                {'value': 'exp_start_time', 'label': 'Sequencing Run Start Time'}
            ],
            'predefined_filters': {
                'sample_types': [
                    {'value': 'validation', 'label': 'Validation'},
                    {'value': 'patient', 'label': 'Patient'},
                    {'value': 'negative control', 'label': 'Negative Control'},
                    {'value': 'positive control', 'label': 'Positive Control'}
                ],
                'dilutions': [
                    {'value': '1:1', 'label': '1:1'},
                    {'value': '1:10', 'label': '1:10'}
                ],
                'classifications': [
                    {'value': '16S', 'label': '16S Only'},
                    {'value': 'ITS', 'label': 'ITS Only'}
                ],
                'spike_concentrations': [
                    {'value': 'IC3', 'label': 'IC3'},
                    {'value': 'IC4', 'label': 'IC4'}
                ],
                'qc': [
                    {'value': 'passed', 'label': 'Passed'},
                    {'value': 'failed', 'label': 'Failed'},
                    {'value': 'unprocessed', 'label': 'Unprocessed'}
                ],
                'read_quality_filtering': [
                    {'value': 'processed', 'label': 'Processed', 'selected': True},
                    {'value': 'unprocessed', 'label': 'Unprocessed'}
                ]
            }
        }


# Global settings instance
settings = Settings()
