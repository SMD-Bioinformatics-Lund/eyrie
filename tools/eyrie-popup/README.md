# Eyrie POPUP - Pipeline Output Processor and UPloader

A Python tool for processing pipeline outputs and uploading sequencing analysis results to the Eyrie database.

## Features

- **Pipeline Software Abstraction**: Support for multiple analysis pipelines (TRANA, MetaVal, etc.)
- **YAML Configuration**: Flexible configuration format for describing analysis runs
- **Multi-format Support**: Parse FastQC, Krona, MultiQC, NanoPlot, and taxonomic abundance files
- **Sample Metadata Batch Upload**: Upload sample metadata from TSV/CSV files
- **Sequencing Run Metadata**: Upload sequencing run metadata from markdown report files
- **Pipeline Data Upload**: Upload structured pipeline execution data and reports
- **Contamination Detection**: Automatic flagging of potential contaminants
- **API Integration**: Direct upload to Eyrie database via REST API
- **CLI Interface**: Easy-to-use command line tool with dry-run support

## Installation

```bash
cd tools/eyrie-popup
pip install -e .
```

### Python Version Compatibility

eyrie-popup supports Python 3.8 through 3.13. It is **not compatible with Python 3.14+** due to dependencies on Pydantic v1.

## Quick Start

### Test Connection

First, verify you can connect to your Eyrie API:

```bash
popup test-connection --api http://localhost:8000/api --username admin --password admin
```

### Upload a Single Sample

Generate configuration and upload sample data:

```bash
# Generate configuration for a sample
popup generate-config --analysis-output-dirpath /path/to/analysis-files/results/trana --sample-id barcode01

# Upload the sample data
popup upload --sample barcode01_config.yaml --api http://localhost:8000/api --username admin --password admin
```

## Sample Data Operations

### 1. Generate Configuration

**Purpose**: Creates a YAML configuration file that describes where to find analysis files for a specific sample.

**When to use**: Before uploading sample data, or when you need to configure custom file paths.

```bash
# Basic usage with TRANA pipeline
popup generate-config --analysis-output-dirpath /path/to/analysis-files/results/trana --sample-id barcode01

# Specify output file and pipeline software
popup generate-config --analysis-output-dirpath /path/to/analysis-files/results/trana --sample-id barcode01 --output custom_config.yaml --pipeline-software metaval

# With custom sample information
popup generate-config --analysis-output-dirpath /path/to/analysis-files/results/trana --sample-id barcode01 --sample-name "Sample_001" --sequencing-run-id "RUN_20250930"
```

### 2. Upload Sample Data

**Purpose**: Processes analysis files (FastQC, Krona, NanoPlot, taxonomic data) and uploads structured data to Eyrie.

**When to use**: After generating configuration files, to upload individual sample results.

```bash
# Upload sample analysis data
popup upload --sample config.yaml --api http://localhost:8000/api --username admin --password admin

# Upload with dry-run to test without actually uploading
popup upload --sample config.yaml --dry-run --verbose
```

### 3. Upload Sample Metadata

**Purpose**: Uploads sample metadata from TSV/CSV files containing sample information like sample type, material, extraction kit, etc.

**When to use**: When you have batch metadata files with sample information that needs to be added to existing or new samples.

```bash
# Upload sample metadata only, creating missing samples
popup upload --sample-metadata sample_metadata.tsv --create-missing --api http://localhost:8000/api --username admin --password admin

# Upload sample metadata for existing samples only
popup upload --sample-metadata sample_metadata.tsv --api http://localhost:8000/api --username admin --password admin
```

**Sample metadata file format** (TSV/CSV):
```tsv
sample_id	sample_type	material	extraction_kit	library_prep_kit	dilution	spike_concentration
barcode01	validation	saliva	Kit_A	PrepKit_B	1:10	IC3
barcode02	patient	stool	Kit_A	PrepKit_B	1:1	IC4
```

The `--create-missing` flag allows the tool to create new sample entries for samples that don't exist in the database.

### 4. Combined Sample Operations

**Purpose**: Upload both sample analysis data and metadata together in a single command.

**When to use**: When you have both analysis results and metadata to upload simultaneously.

```bash
# Upload both sample data and sample metadata together
popup upload --sample config.yaml --sample-metadata sample_metadata.tsv --api http://localhost:8000/api --username admin --password admin
```

## Sequencing Run Operations

### 1. Upload Sequencing Run Metadata

**Purpose**: Uploads sequencing run metadata (device info, start time, flow cell ID, etc.) from markdown report files containing JSON metadata blocks.

**When to use**: When you have sequencing run report files that contain JSON metadata about the sequencing instrument and run parameters.

```bash
# Upload sequencing run metadata from markdown file
popup upload --sequencing-run-metadata report.md --sequencing-run-id RUN123 --api http://localhost:8000/api --username admin --password admin
```

**Markdown file format**: The tool extracts JSON blocks from markdown files:
````markdown
# Sequencing Run Report

## Metadata
```json
{
  "exp_start_time": "2025-09-30T09:46:56Z",
  "device_id": "MN12345",
  "flow_cell_id": "FC123456",
  "hostname": "sequencer-01"
}
```
````

### 2. Upload Pipeline Files

**Purpose**: Uploads structured pipeline execution data (parameters, execution trace, software versions) and HTML reports for sequencing run-level analysis.

**When to use**: When you want to upload pipeline execution information and reports associated with a sequencing run.

```bash
# Upload pipeline files with specific datetime suffix
popup upload --analysis-output-dirpath /path/to/analysis-files/results/trana --pipeline-datetime-suffix 2025-09-30_09-46-56 --sequencing-run-id RUN123 --api http://localhost:8000/api --username admin --password admin

# Specify different pipeline software
popup upload --analysis-output-dirpath /path/to/analysis-files/results/trana --pipeline-software metaval --pipeline-datetime-suffix 2025-09-30_09-46-56 --sequencing-run-id RUN123 --api http://localhost:8000/api --username admin --password admin
```

**Required arguments for pipeline upload:**
- `--analysis-output-dirpath`: Path to analysis results directory
- `--pipeline-datetime-suffix`: Datetime suffix to identify specific pipeline files (format: YYYY-MM-DD_HH-MM-SS)
- `--sequencing-run-id`: Sequencing run identifier

**Optional arguments:**
- `--pipeline-software`: Pipeline software used (default: 'trana')

**Alternative**: Set `EYRIE_ANALYSIS_OUTPUT_DIRPATH` environment variable instead of using `--analysis-output-dirpath` argument.

## Utility Commands

### Test Connection

**Purpose**: Verifies connectivity to the Eyrie API and tests authentication.

```bash
popup test-connection --api http://localhost:8000/api --username admin --password admin
```

### Dry Run Mode

**Purpose**: Parse and validate data without actually uploading to the database.

**When to use**: To test configuration and data parsing before actual upload.

```bash
# Test sample upload without uploading
popup upload --sample config.yaml --dry-run --verbose

# Test metadata upload without uploading
popup upload --sample-metadata sample_metadata.tsv --dry-run --verbose
```

## Configuration Reference

### YAML Configuration Format

The YAML configuration file describes the analysis run structure:

```yaml
# Sample information
sample:
  sample_id: "barcode01"
  sample_name: "Sample_BC01"
  lims_id: "LIMS_BC01_001"
  barcode: "barcode01"
  sequencing_run_id: "RUN_2025_09_30"
  classification_type: "16S"  # or "ITS"
  pipeline_software: "trana"  # or "metaval", etc.

# Analysis output directory containing pipeline output directories
analysis_output_dirpath: "/path/to/analysis-files/results/trana"

# Quality control files
fastqc:
  enabled: true
  directory: "fastqc"
  file: "barcode01_fastqc.html"

# Taxonomic classification plots
krona:
  enabled: true
  directory: "krona"
  file: "barcode01_krona.html"

# Nanopore-specific plots and statistics
nanoplot:
  unprocessed:
    enabled: true
    directory: "nanoplot_unprocessed"
    stats_file: "barcode01_nanoplot_unprocessed_NanoStats.txt"
    html_files:
      - "barcode01_nanoplot_unprocessed_NanoPlot-report.html"
      - "barcode01_nanoplot_unprocessed_LengthvsQualityScatterPlot_dot.html"
      # ... additional HTML files
  processed:
    enabled: true
    directory: "nanoplot_processed" 
    stats_file: "barcode01_nanoplot_processed_NanoStats.txt"
    html_files:
      - "barcode01_nanoplot_processed_NanoPlot-report.html"
      - "barcode01_nanoplot_processed_LengthvsQualityScatterPlot_dot.html"
      # ... additional HTML files

# Analysis results
results:
  enabled: true
  directory: "results"
  rel_abundance_file: "barcode01_filtered.fastq_rel-abundance.tsv"

# MultiQC aggregated reports (optional)
multiqc:
  enabled: true
  directory: "multiqc"
  report_file: "multiqc_report.html"
```

### Analysis Directory Structure

The tool expects analysis files to be organized as follows:

```
{analysis_output_dirpath}/     # e.g., /path/to/analysis-files/results/trana 
├── pipeline_info/             # Pipeline execution data
│   ├── params_*.json          # Pipeline parameters
│   ├── execution_trace_*.txt  # Task execution trace
│   ├── software_versions.yml  # Software version information
│   ├── execution_report_*.html    # Execution report
│   ├── execution_timeline_*.html  # Timeline visualization
│   └── pipeline_dag_*.html        # Pipeline DAG visualization
├── fastqc/                    # Quality control reports
│   └── {sample_id}_fastqc.html
├── krona/                     # Taxonomic plots
│   └── {sample_id}_krona.html
├── nanoplot_processed/        # Quality plots (processed)
│   ├── {sample_id}_nanoplot_processed_NanoStats.txt
│   └── {sample_id}_nanoplot_processed_*.html
├── nanoplot_unprocessed/      # Quality plots (unprocessed)
│   ├── {sample_id}_nanoplot_unprocessed_NanoStats.txt
│   └── {sample_id}_nanoplot_unprocessed_*.html
├── results/                   # Analysis results
│   └── {sample_id}_filtered.fastq_rel-abundance.tsv
└── multiqc/                   # Aggregated reports (optional)
    └── multiqc_report.html
```

### Environment Variables

eyrie-popup supports configuration through environment variables:

- `EYRIE_ANALYSIS_OUTPUT_DIRPATH`: Analysis results directory path
  - Used for pipeline file discovery during upload
  - Example: `/path/to/analysis-files/results/trana`
  - Can replace `--analysis-output-dirpath` argument

- `EYRIE_USER`: Default username for API authentication
- `EYRIE_PASSWORD`: Default password for API authentication

## File Types & Data Processing

### Supported File Types

- **FastQC**: HTML quality control reports per sample
- **Krona**: Interactive taxonomic classification plots (HTML)
- **MultiQC**: Aggregated quality control reports (HTML)
- **NanoPlot**: Nanopore-specific quality plots and statistics (HTML + TXT)
- **Taxonomic Abundances**: Relative abundance TSV files
- **Pipeline Files**: Execution data (JSON, TXT, YAML) and reports (HTML)

### Data Processing Pipeline

1. **File Discovery**: Locates analysis files based on configuration
2. **Data Parsing**: Extracts structured data from various file formats
3. **Validation**: Validates parsed data against expected schemas
4. **Contamination Detection**: Applies contamination rules to taxonomic data
5. **Format Conversion**: Converts data to Eyrie database format
6. **API Upload**: Uploads structured data via REST API

## Advanced Features

### Contamination Detection

The tool automatically detects potential contaminants based on:

- Species names matching suspected contaminants list
- Abundance thresholds (configurable)
- Custom contamination rules
- Known environmental contaminants

Detected contaminants are flagged in the uploaded data for review.

### API Integration

Sample data uploaded to Eyrie includes:

- **Quality Control Status**: Automatically determined based on contamination
- **Statistical Summaries**: Aggregated metrics from NanoStats
- **File References**: Paths to HTML reports for visualization
- **Taxonomic Classification Data**: Structured taxonomic abundance information
- **Contamination Flags**: Automatically flagged potential contaminants
- **QC Comments**: Structured comments for quality control workflow

### Pipeline Data Integration

Sequencing run data includes:

- **Execution Parameters**: Complete pipeline configuration
- **Performance Metrics**: Task execution times and resource usage  
- **Software Versions**: Complete software environment snapshot
- **HTML Reports**: Interactive execution reports and visualizations
- **Workflow Provenance**: Complete audit trail of analysis steps

## Development

### Installation for Development

```bash
cd tools/eyrie-popup
pip install -e ".[dev]"
```

### Running Tests

```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=popup

# Run specific test file
python -m pytest tests/test_parser.py
```

### Code Style

```bash
# Format code
black popup/

# Type checking
mypy popup/

# Linting
flake8 popup/
```

## Troubleshooting

### Common Issues

**Connection Errors:**
```bash
# Test API connectivity
popup test-connection --api http://localhost:8000/api --username admin --password admin
```

**File Not Found Errors:**
- Verify `analysis_output_dirpath` points to correct directory
- Check file naming conventions match sample IDs
- Use `--dry-run --verbose` to debug file discovery

**Authentication Errors:**
- Verify username/password credentials
- Check user has appropriate permissions (uploader or admin role)
- Verify API URL is correct

**Configuration Errors:**
- Use `popup generate-config --help` to see all options
- Validate YAML syntax in configuration files
- Check required vs optional fields in configuration

### Debug Mode

Use verbose output and dry-run mode for troubleshooting:

```bash
popup upload --sample config.yaml --dry-run --verbose --api http://localhost:8000/api
```