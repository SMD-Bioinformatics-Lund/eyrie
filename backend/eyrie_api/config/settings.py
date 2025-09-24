import os

# MongoDB Configuration
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://admin:admin@mongodb:27017/eyrie?authSource=eyrie')

# CORS Configuration
CORS_ORIGINS = ["*"]
CORS_CREDENTIALS = True
CORS_METHODS = ["*"]
CORS_HEADERS = ["*"]

# Application Configuration
APP_TITLE = "Eyrie Sample Manager"
APP_HOST = "0.0.0.0"
APP_PORT = 5000

# Valid user roles
VALID_ROLES = ['user', 'admin', 'uploader']

# Valid QC statuses
VALID_QC_STATUSES = ['passed', 'failed', 'unprocessed']
