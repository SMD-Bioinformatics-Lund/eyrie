# Eyrie Sample Manager

A modern web-based application for managing 16S and ITS sequencing classification sample results. Built with FastAPI backend, Flask frontend, and MongoDB database.

## Features

- **Sample Management**: View, search, and manage sequencing samples with detailed metadata
- **Authentication**: JWT-based authentication with role-based access control (admin, uploader, user)
- **Contamination Flagging**: Interactive flagging system for taxonomic species with persistent storage
- **Three-Tab Sample View**: Overview, Classification, and Nanoplot views for comprehensive sample analysis
- **NanoStats Integration**: Display all 8 processed NanoStats from sequencing quality analysis
- **QC Management**: Update sample QC status (passed/failed/unprocessed) with comments
- **Modern UI**: Clean Bootstrap-based interface with responsive design and tabbed navigation
- **Admin Dashboard**: User management and administrative functions
- **Sample Processing Tool**: eyrie-popup CLI tool for processing and uploading sample data
- **Docker Deployment**: Full containerized deployment with Docker Compose
- **Multi-architecture Support**: Built for both AMD64 and ARM64 platforms

## Architecture

The application consists of three main components:

- **Frontend** (Flask): Web interface and static file serving
- **Backend** (FastAPI): REST API for data operations
- **Database** (MongoDB): Sample data and user management

## Quick Start

### Using Docker (Recommended)

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd eyrie
   ```

2. **Start the application**:
   ```bash
   docker-compose up -d
   ```

3. **Access the application**:
   - Web Interface: http://localhost:3000
   - Backend API: http://localhost:8000
   - MongoDB: localhost:27017

4. **Login with default credentials**:
   - Username: `admin`
   - Password: `admin`

5. **Stop the application**:
   ```bash
   docker-compose down
   ```

### Using Docker Hub Images

You can also use the pre-built images from Docker Hub:

```bash
# Pull the images
docker pull clinicalgenomicslund/eyrie-frontend:latest
docker pull clinicalgenomicslund/eyrie-backend:latest
docker pull clinicalgenomicslund/eyrie-popup:latest

# Or use specific version
docker pull clinicalgenomicslund/eyrie-frontend:0.2.1
docker pull clinicalgenomicslund/eyrie-backend:0.2.1
docker pull clinicalgenomicslund/eyrie-popup:0.2.1
```

## Project Structure

```
eyrie/
├── backend/                     # FastAPI backend
│   ├── eyrie_api/
│   │   ├── auth/               # Authentication middleware
│   │   ├── config/             # Configuration settings
│   │   ├── database/           # Database operations
│   │   ├── models/             # Pydantic data models
│   │   ├── routes/             # API route handlers
│   │   ├── utils/              # Utility functions
│   │   └── main.py             # FastAPI application
│   ├── Dockerfile              # Backend container
│   └── pyproject.toml          # Python dependencies
├── frontend/                   # Flask frontend
│   ├── eyrie_app/
│   │   ├── blueprints/         # Flask blueprints for pages
│   │   │   ├── admin/          # Admin dashboard
│   │   │   ├── login/          # Login page
│   │   │   ├── sample/         # Sample detail view
│   │   │   └── samples/        # Sample list view
│   │   ├── shared/             # Shared templates and assets
│   │   │   ├── static/css/     # Stylesheets
│   │   │   └── templates/      # Base templates
│   │   └── app.py              # Flask application
│   ├── Dockerfile              # Frontend container
│   └── pyproject.toml          # Python dependencies
├── tools/                      # Processing tools
│   └── eyrie-popup/            # Sample processing CLI tool
│       ├── popup/              # Tool source code
│       ├── Dockerfile          # Tool container
│       ├── setup.py            # Tool installation
│       └── requirements.txt    # Tool dependencies
├── data/                       # Sample data files
├── docker-compose.yml          # Multi-container deployment
├── init-mongo.js               # MongoDB initialization
└── .github/workflows/          # CI/CD workflows
```

## API Documentation

### Authentication Endpoints
- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout
- `GET /api/auth/current-user` - Get current user info

### Sample Endpoints
- `GET /api/samples` - List all samples
- `GET /api/samples/{sample_id}` - Get sample details
- `POST /api/samples` - Create new sample (admin/uploader only)
- `PUT /api/samples/{sample_id}` - Create or update sample (admin/uploader only)
- `PATCH /api/samples/{sample_id}` - Partially update sample (admin/uploader only)
- `PUT /api/samples/{sample_id}/qc` - Update QC status (admin/uploader only)
- `PUT /api/samples/{sample_id}/comment` - Update comments (admin/uploader only)
- `PUT /api/samples/{sample_id}/species-flags` - Update species flags (contaminants and/or top hits)

### Admin Endpoints (Admin access required)
- `GET /api/admin/users` - List all users
- `POST /api/admin/users` - Create new user
- `PUT /api/admin/users/{user_id}` - Update user
- `DELETE /api/admin/users/{user_id}` - Delete user

### Health Check
- `GET /health` - Application health status

## Database Schema

### Users Collection
- `username`: Unique username
- `email`: User email address
- `password_hash`: Hashed password
- `role`: User role (admin, user, uploader)
- `is_active`: Account status
- `created_date`: Account creation date

### Samples Collection
- `sample_name`: Human-readable sample name
- `sample_id`: Unique sample identifier
- `sequencing_run_id`: Sequencing run identifier
- `lims_id`: LIMS system identifier
- `classification`: "16S" or "ITS"
- `qc`: "passed", "failed", or "unprocessed"
- `comments`: User comments
- `created_date`: Sample creation date
- `updated_date`: Last modification date
- `krona_file`: Krona plot HTML filename
- `quality_plot`: Quality plot HTML filename
- `pipeline_files`: Array of pipeline output filenames
- `statistics`: Read statistics and quality metrics
- `flagged_contaminants`: Array of flagged contamination species
- `taxonomic_data`: Taxonomic classification results with species abundance
- `nano_stats_processed`: Processed NanoStats quality metrics
- `nano_stats_unprocessed`: Unprocessed NanoStats quality metrics

## Development

### Local Development Setup

1. **Backend Development**:
   ```bash
   cd backend
   pip install -e .[development]
   uvicorn eyrie_api.main:app --reload --host 0.0.0.0 --port 5000
   ```

2. **Frontend Development**:
   ```bash
   cd frontend
   pip install -e .[development]
   python -m eyrie_app.wsgi
   ```

3. **MongoDB**:
   Use Docker or local MongoDB instance on port 27017

4. **Eyrie-popup Tool**:
   ```bash
   cd tools/eyrie-popup
   pip install -e .
   eyrie-popup --help
   ```

### Environment Variables

- `MONGO_URI`: MongoDB connection string
- `ENVIRONMENT`: Application environment (development/production)
- `BACKEND_URL`: Backend API URL for frontend

## Data Files

Place your pipeline output files in the `data/` directory:
- `data/test/krona/` - Krona taxonomic plots (HTML)
- `data/test/fastqc/` - FastQC quality reports (HTML)
- `data/test/nanoplot_processed/` - Processed NanoPlot quality plots (HTML)
- `data/test/nanoplot_unprocessed/` - Unprocessed NanoPlot quality plots (HTML)
- `data/test/results/` - Pipeline results and TSV abundance files

## Sample Processing with eyrie-popup

The eyrie-popup tool processes sample data and uploads it to the Eyrie system:

```bash
# Using conda environment
conda run -n eyrie-popup eyrie-popup upload --sample sample_config.yaml --api-url http://localhost:3000/api --username admin --pasword admin #Once you have created other admin users - REMOVE admin/admin

# Using Docker
docker run -v $(pwd):/data clinicalgenomicslund/eyrie-popup:latest upload --config /data/sample_config.yaml --api-url http://host.docker.internal:3000

# Test connection
eyrie-popup test-connection --api-url http://localhost:3000
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test your changes with the provided sample data
5. Submit a pull request

## License

No license as of yet

## Support

Ryan Kennedy (ryan.kennedy@skane.se)

## Version

Current version: 0.2.1

## Docker Hub

Official images are available on Docker Hub:
- [Frontend](https://hub.docker.com/r/clinicalgenomicslund/eyrie-frontend)
- [Backend](https://hub.docker.com/r/clinicalgenomicslund/eyrie-backend)
- [Eyrie-popup Tool](https://hub.docker.com/r/clinicalgenomicslund/eyrie-popup)
