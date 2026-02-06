# Eyrie

A modern web-based application for managing 16S and ITS sequencing classification sample results. Built with FastAPI backend, Flask frontend, and MongoDB database.

## Quick Start

### 1. Installation

Clone and start the application using Docker:

```bash
# Clone the repository
git clone https://github.com/SMD-Bioinformatics-Lund/eyrie
cd eyrie

# Start the application
docker-compose -f docker-compose.dev.yml --env-file environment.dev up -d --build
```

### 2. Access the Application

- **Web Interface**: http://localhost:3000
- **Backend API**: http://localhost:8000/api
- **Login**: Username `admin` / Password `admin`

### 3. Upload Sample Data

Install and use the eyrie-popup tool to upload sample data:

```bash
# Install eyrie-popup
cd tools/eyrie-popup
pip install -e .
cd ../..

# Upload sample data
popup upload --sample data/test/barcode01_config.yaml --api http://localhost:8000/api --username admin --password admin

# Upload sequencing run data
popup upload --sequencing-run-metadata report.md --sequencing-run-id RUN123 --api http://localhost:8000/api --username admin --password admin
```

**For detailed eyrie-popup usage, configuration, and examples**, see [tools/eyrie-popup/README.md](tools/eyrie-popup/README.md)

### 4. Stop the Application

```bash
docker-compose -f docker-compose.dev.yml down
```

## Key Features

- **Sample Management**: View, search, and manage sequencing samples with comprehensive metadata
- **Sequencing Run Management**: Aggregated statistics and pipeline data for sequencing runs
- **Quality Control**: Interactive QC status updates with comment tracking
- **Contamination Flagging**: Automated detection and manual flagging of contaminant species
- **Trends Analysis**: Time-based visualization of sample metrics and quality trends
- **Negative Controls**: Automatic display of negative controls from the same sequencing run
- **Multi-view Sample Analysis**: Overview, Classification, and Quality Control views
- **Role-based Access**: Admin, uploader, and user roles with appropriate permissions
- **Data Upload Tool**: CLI tool (eyrie-popup) for processing and uploading analysis results

## Production Deployment

### Apache Reverse Proxy

For production deployment behind Apache:

```bash
# Enable required modules
sudo a2enmod proxy proxy_http headers

# Include proxy configuration in virtual host
Include /path/to/eyrie/apache-proxy.conf

# Start production containers
docker-compose -f docker-compose.yml --env-file environment.prod up -d
```

Application will be available at `/eyrie` on your domain.

## Architecture

- **Frontend** (Flask): Web interface with server-side rendering
- **Backend** (FastAPI): REST API for data operations
- **Database** (MongoDB): Sample data and user management
- **Upload Tool** (eyrie-popup): CLI tool for data processing and upload

## Data Structure

### Analysis Files

Mount your pipeline output files in `analysis-files/`:

```
analysis-files/results/trana/
├── fastqc/              # Quality control reports  
├── krona/               # Taxonomic classification plots
├── nanoplot_processed/  # Quality plots (processed reads)
├── nanoplot_unprocessed/# Quality plots (raw reads)
├── results/             # Abundance data (TSV files)
└── pipeline_info/       # Pipeline execution data
```

### Sample Upload Workflow

1. **Generate Config**: Create YAML configuration for sample
2. **Upload Sample Data**: Process and upload analysis results
3. **Upload Metadata**: Add sample metadata (TSV/CSV)
4. **Upload Pipeline Data**: Add sequencing run pipeline information

See [tools/eyrie-popup/README.md](tools/eyrie-popup/README.md) for detailed documentation.

## Project Structure

```
eyrie/
├── backend/                     # FastAPI backend
│   ├── eyrie_api/
│   │   ├── auth/               # Authentication middleware
│   │   ├── database/           # Database operations
│   │   ├── models/             # Pydantic data models
│   │   ├── routes/             # API endpoints
│   │   └── main.py             # FastAPI application
├── frontend/                   # Flask frontend
│   ├── eyrie_app/
│   │   ├── blueprints/         # Page components
│   │   ├── shared/             # Templates and assets
│   │   └── app.py              # Flask application
├── tools/                      # Processing tools
│   └── eyrie-popup/            # Sample upload CLI tool
├── docker-compose.yml          # Production deployment
├── docker-compose.dev.yml      # Development deployment
├── environment.prod            # Production environment
├── environment.dev             # Development environment
└── apache-proxy.conf           # Apache configuration
```

## API Documentation

### Authentication Endpoints
- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout
- `GET /api/auth/current-user` - Get current user info

### Sample Endpoints (Authentication required)
- `GET /api/samples` - List all samples
- `GET /api/samples/{sample_id}` - Get sample details
- `GET /api/sample/{sample_id}/negative-controls` - Get negative control samples
- `POST /api/samples` - Create new sample (admin/uploader only)
- `PUT /api/samples/{sample_id}` - Create or update sample (admin/uploader only)
- `PATCH /api/samples/{sample_id}` - Partially update sample (admin/uploader only)
- `PUT /api/samples/{sample_id}/qc` - Update QC status
- `PUT /api/samples/{sample_id}/comment` - Update comments
- `PUT /api/samples/{sample_id}/species-flags` - Update species flags

### Seqrun Endpoints (Authentication required)
- `GET /api/seqruns` - List all sequencing runs with statistics
- `GET /api/seqruns/{seqrun_id}` - Get sequencing run details with samples and pipeline data
- `PUT /api/seqruns/{seqrun_id}` - Create or update sequencing run data (admin/uploader only)

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

### Authentication
- **Application-level authentication**: Users stored in MongoDB collections, not MongoDB root users
- **JWT-based session management**: Secure token-based sessions
- **Role-based access control**: Three user roles (admin, uploader, user)
- **Protected API endpoints**: Authentication required for most operations
- **Session timeout management**: Configurable token expiration
- **Pre-configured users**: Default users created via init-mongo.js (admin/admin, uploader/uploader, user/user)

### Data Protection
- Input validation and sanitization
- SQL injection protection via MongoDB
- File upload restrictions
- CORS configuration

### Best Practices
- **Change default credentials immediately**: Default users (admin/admin, uploader/uploader, user/user) should be changed or removed in production
- **Use environment variables for sensitive configuration**: Store secrets in environment files, not code
- **Enable HTTPS in production**: Configure Apache proxy with SSL/TLS
- **Regular security updates**: Keep Docker images and dependencies current
- **Monitor application logs**: Watch for failed authentication attempts and suspicious activity
- **Network isolation**: MongoDB runs on Docker internal network, not exposed externally

## Configuration

### Environment Variables

Key configuration options:

**Database:**
- `MONGO_INITDB_DATABASE`: Initial database name (default: eyrie)
- `MONGO_URI`: MongoDB connection string (default: mongodb://mongodb:27017/eyrie)

**Authentication:**
- `SECRET_KEY`: Flask session signing key (frontend)
- `JWT_SECRET`: JWT signing key for token authentication (backend)
- `JWT_EXPIRATION_HOURS`: Token expiration time in hours (default: 24)
- `JWT_COOKIE_SECURE`: Set to `true` for HTTPS (production), `false` for HTTP (development)

**Application:**
- `BACKEND_HOST`: Backend server host
- `FRONTEND_HOST`: Frontend server host
- `API_URL`: Backend API base URL

Edit values as needed for your deployment.

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make changes and test thoroughly
4. Submit a pull request with clear description

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
