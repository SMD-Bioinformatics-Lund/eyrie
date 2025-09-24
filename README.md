# Sequencing Sample Manager

A web-based visualization tool for displaying 16S and ITS sequencing classification sample results with MongoDB backend, Flask API, and Bootstrap frontend.

## Features

- **Sample Table**: Display samples with open button, sample info, QC status, and comments
- **Sample Detail View**: Interactive Krona plots, QC management, read quality plots, and pipeline file links
- **QC Management**: Pass/fail buttons with comment functionality
- **Sharp Edge Design**: Clean, modern Bootstrap-based UI with no rounded corners
- **Dockerized**: Full-stack deployment with Docker Compose

## Project Structure

```
eyrie/
├── backend/                 # Flask API server
│   ├── app.py              # Main Flask application
│   ├── requirements.txt    # Python dependencies
│   └── Dockerfile          # Backend container
├── frontend/               # Static web files
│   ├── index.html          # Main sample table page
│   ├── sample.html         # Sample detail page
│   ├── script.js           # Main page JavaScript
│   ├── sample.js           # Sample detail JavaScript
│   └── styles.css          # Sharp edge styling
├── data/                   # Sample data files
│   ├── krona/              # Krona plot HTML files
│   ├── quality/            # Quality plot HTML files
│   └── pipeline/           # Pipeline report files
├── docker-compose.yml      # Full stack deployment
├── apache.conf             # Apache configuration
└── init-mongo.js           # MongoDB initialization
```

## Quick Start

### Option 1: Docker (Recommended)

1. **Start the application**:
   ```bash
   docker-compose up -d
   ```

2. **Access the application**:
   - Frontend: http://localhost
   - API: http://localhost/api/samples

3. **Stop the application**:
   ```bash
   docker-compose down
   ```

### Option 2: Local Development (if Docker issues)

1. **Install MongoDB locally** or use MongoDB Atlas

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements-local.txt
   ```

3. **Run the application**:
   ```bash
   python run-local.py
   ```

4. **Access the application**:
   - Frontend: http://localhost:8000
   - API: http://localhost:8000/api/samples

## Database Schema

The MongoDB `samples` collection contains:
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

## API Endpoints

- `GET /api/samples` - List all samples
- `GET /api/samples/{id}` - Get sample details
- `PUT /api/samples/{id}/qc` - Update QC status
- `PUT /api/samples/{id}/comment` - Update comments
- `GET /data/{type}/{file}` - Serve data files

## Data Files

Place your pipeline output files in the `data/` directory:
- `data/krona/` - Krona taxonomic plots (HTML)
- `data/quality/` - Read quality vs length plots (HTML)
- `data/pipeline/` - Pipeline reports and statistics (HTML)

## Customization

- **Styling**: Modify `frontend/shared/static/css/styles.css` for visual changes
- **Database**: Update `init-mongo.js` to add your samples
- **API**: Extend `backend/app.py` for additional endpoints
- **Frontend**: Modify HTML/JS files for new features
