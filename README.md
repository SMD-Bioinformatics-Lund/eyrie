# Eyrie Sample Manager

A modern web-based application for managing 16S and ITS sequencing classification sample results. Built with FastAPI backend, Flask frontend, and MongoDB database.

## Features

- **Sample Management**: View, search, and manage sequencing samples with detailed metadata
- **Sample processing tool**: eyrie-popup CLI tool for processing and uploading sample data
- **Sample QC curation**: Update sample QC status (`passed`/`failed`/`unprocessed`) with comments
- **Sample contamination flagging**: Interactive flagging system for flagging contaminant hits
- **Sample top hit flagging**: Interactive flagging system for flagging top hits
- **Multi-tabbed sample view**: Overview, Classification, and Nanoplot views for comprehensive sample analysis
- **Trends analysis**: Interactive data visualization with Plotly charts for sample metrics over time
- **Simple UI**: Clean Bootstrap-based interface with responsive design and server-side rendering
- **Server-side authentication**: Flask decorator-based authentication with role-based access control (admin, uploader, user)
- **Admin dashboard**: User management and administrative functions with role-based visibility
- **Docker deployment**: Full containerized deployment with Docker Compose

## Architecture

The application consists of three main components:

- **Frontend** (Flask): Web interface and static file serving
- **Backend** (FastAPI): REST API for data operations
- **Database** (MongoDB): Sample data and user management

## Quick Start

### Using Docker

1. **Clone the repository**:
   ```bash
   git clone https://github.com/SMD-Bioinformatics-Lund/eyrie
   cd eyrie
   ```

2. **Start the application**:
   ```bash
   docker-compose -f docker-compose.dev.yml --env-file environment.dev up -d --build
   ```

3. **Access the application**:
   - Web Interface: http://localhost:3000
   - Backend API: http://localhost:8000/api
   - MongoDB: localhost:27017

4. **Login with default credentials**:
   - Username: `admin`
   - Password: `admin`

5. **Stop the application**:
   ```bash
   docker-compose -f docker-compose.dev.yml down
   ```

### Production Deployment with Apache Proxy

For production deployment behind an Apache reverse proxy:

1. **Configure Apache**:
   ```bash
   # Enable required modules
   sudo a2enmod proxy proxy_http headers
   
   # Include the proxy configuration in your virtual host
   Include /path/to/eyrie/apache-proxy.conf
   ```

2. **Start the application in production**:
   ```bash
   docker-compose -f docker-compose.yml --env-file environment.prod up -d
   ```

3. **Access the application**:
   - Application: http://your-domain.com/eyrie
   - API: http://your-domain.com/eyrie/api

The application will be available at `/eyrie` on your domain with the backend API at `/eyrie/api`.

## Uploading samples

### Data files

Place/mount your pipeline output files in the `data/` directory:
- `data/test/krona/` - Krona taxonomic plots (HTML)
- `data/test/fastqc/` - FastQC quality reports (HTML)
- `data/test/nanoplot_processed/` - Processed NanoPlot quality plots (HTML)
- `data/test/nanoplot_unprocessed/` - Unprocessed NanoPlot quality plots (HTML)
- `data/test/results/` - Pipeline results and TSV abundance files

### Sample processing & uploading with eyrie-popup

Conda installation of eyrie-popup

```bash
cd tools/eyrie-popup
conda create -n eyrie-popup
conda activate eyrie-popup
pip install -e .
```

The eyrie-popup tool processes sample data and uploads it to the Eyrie system (**replace the api url if in production**):

```bash
# Change directory back to eyrie
cd ../..

# Using conda environment
conda run -n eyrie-popup popup upload --sample data/test/barcode01_config.yaml --api http://localhost:8000/api --username admin --password admin #Once you have created other admin users - REMOVE admin/admin

# Test connection if upload doesn't work
conda run -n eyrie-popup popup test-connection --username admin --password admin --api http://localhost:8000/api
```

Yaml files can be created by running:

```bash
conda run -n eyrie-popup popup generate-config --help
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
│   │   │   ├── auth.py         # Authentication endpoints
│   │   │   ├── admin.py        # Admin endpoints
│   │   │   ├── samples.py      # Sample endpoints
│   │   │   └── trends.py       # Trends analysis endpoints
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
│   │   │   ├── samples/        # Sample list view
│   │   │   └── trends/         # Trends analysis view
│   │   ├── shared/             # Shared templates and assets
│   │   │   ├── static/css/     # Stylesheets
│   │   │   ├── static/js/      # Shared JavaScript functions
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
├── docker-compose.dev.yml      # Multi-container deployment (dev mode)
├── environment.prod            # Production environment template
├── environment.dev             # Dev environment template
├── apache-proxy.conf           # Apache reverse proxy configuration
├── init-mongo.js               # MongoDB initialization
└── .github/workflows/          # CI/CD workflows
```

## API Documentation

### Authentication Endpoints
- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout
- `GET /api/auth/current-user` - Get current user info

### Sample Endpoints (Authentication required)
- `GET /api/samples` - List all samples
- `GET /api/samples/{sample_id}` - Get sample details
- `POST /api/samples` - Create new sample (admin/uploader only)
- `PUT /api/samples/{sample_id}` - Create or update sample (admin/uploader only)
- `PATCH /api/samples/{sample_id}` - Partially update sample (admin/uploader only)
- `PUT /api/samples/{sample_id}/qc` - Update QC status (authentication required)
- `PUT /api/samples/{sample_id}/comment` - Update comments (authentication required)
- `PUT /api/samples/{sample_id}/species-flags` - Update species flags (authentication required)

### Trends Endpoints (Authentication required)
- `GET /api/trends/data` - Get trends analysis data with filtering and grouping options

### Admin Endpoints (Admin access required)
- `GET /api/admin/users` - List all users
- `POST /api/admin/users` - Create new user
- `PUT /api/admin/users/{user_id}` - Update user
- `DELETE /api/admin/users/{user_id}` - Delete user

### Health Check
- `GET /health` - Application health status

## Security

### Authentication Architecture
- **Server-side authentication**: All routes protected with Flask decorators (`@login_required`, `@admin_required_view`)
- **Session-based**: Uses secure HTTP-only cookies for session management
- **API protection**: All API endpoints require valid authentication before processing
- **Role-based access control**: Admin, uploader, and user roles with appropriate permissions

### Security Features
- **Server-side template rendering**: Admin buttons and UI elements conditionally rendered based on user role
- **Cannot be bypassed**: Authentication happens server-side before page load
- **API endpoint protection**: All sample and trends data requires authentication

### View Protection
- **Samples & Trends**: `@login_required` - authenticated users only
- **Admin dashboard**: `@admin_required_view` - admin users only
- **Sample details**: `@login_required` - authenticated users only
- **Login page**: Public access for authentication

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

### Local development setup

1. **Backend development**:
   ```bash
   cd backend
   pip install -e .[development]
   uvicorn eyrie_api.main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Frontend development**:
   ```bash
   cd frontend
   pip install -e .[development]
   python -m eyrie_app.wsgi
   ```

3. **MongoDB**:
   Use Docker or local MongoDB instance on port 27017

4. **Eyrie-popup tool**:
   ```bash
   cd tools/eyrie-popup
   pip install -e .
   popup --help
   ```

### Environment Variables

The application supports environment-based configuration through the `environment.prod` file:

**Version Management:**
- `EYRIE_VERSION`: Application version
- `MONGODB_VERSION`: MongoDB image version

**Host Ports (Apache Proxy):**
- `FRONTEND_HOST_PORT`: Frontend container port
- `BACKEND_HOST_PORT`: Backend container port
- `MONGO_HOST_PORT`: MongoDB container port

**URL Configuration:**
- `EXTERNAL_BASE_PATH`: Base path served by Apache (/eyrie)
- `EXTERNAL_API_URL`: External API URL through Apache proxy
- `INTERNAL_BACKEND_URL`: Internal container-to-container backend URL
- `BACKEND_BASE_PATH`: Backend API base path (/eyrie/api)

**Database:**
- `MONGO_URI`: MongoDB connection string
- `ENVIRONMENT`: Application environment (production)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test your changes with the provided sample data
5. Submit a pull request

## License

This project is licensed under the ![License](https://img.shields.io/github/license/SMD-Bioinformatics-Lund/eyrie) - see the [LICENSE](LICENSE) file for details.

## Support

Ryan Kennedy (ryan.kennedy@skane.se)

## Version

Current version: ![Version](https://img.shields.io/github/v/release/SMD-Bioinformatics-Lund/eyrie)

## Docker Hub

Official images are available on Docker Hub:
- [Frontend](https://hub.docker.com/r/clinicalgenomicslund/eyrie-frontend)
- [Backend](https://hub.docker.com/r/clinicalgenomicslund/eyrie-backend)
- [Eyrie-popup Tool](https://hub.docker.com/r/clinicalgenomicslund/eyrie-popup)
