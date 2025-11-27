# Eyrie POPUP - Pipeline Output Processor and UPloader

A Python tool for processing pipeline outputs and uploading sequencing analysis results to the Eyrie database.

## Features

- **Pipeline Software Abstraction**: Support for multiple analysis pipelines (TRANA, MetaVal, etc.)
- **YAML Configuration**: Flexible configuration format for describing analysis runs
- **Multi-format Support**: Parse FastQC, Krona, MultiQC, NanoPlot, and taxonomic abundance files
- **Metadata Batch Upload**: Upload sample metadata from TSV/CSV files
- **Contamination Detection**: Automatic flagging of potential contaminants
- **API Integration**: Direct upload to Eyrie database via REST API
- **CLI Interface**: Easy-to-use command line tool

## Python Version Compatibility

eyrie-popup supports Python 3.8 through 3.13. It is **not compatible with Python 3.14+** due to dependencies on Pydantic v1.

## Installation

```bash
cd tools/eyrie-popup
pip install -e .
```

## Usage

### Generate Configuration

Auto-generate a configuration file for a sample:

```bash
# Basic usage with TRANA pipeline
popup generate-config --analysis-output-dirpath /path/to/analysis/results --sample-id barcode01 --output config.yaml

# Specify different pipeline software
popup generate-config --analysis-output-dirpath /path/to/analysis/results --sample-id barcode01 --pipeline-software metaval --output config.yaml
```

### Upload Sample and Metadata

Parse analysis results and upload to Eyrie:

```bash
# Upload sample analysis data only
popup upload --sample config.yaml --api http://localhost:8000/api --username admin --password admin

# Upload metadata only (TSV/CSV file)
popup upload --metadata metadata.tsv --api http://localhost:8000/api --username admin --password admin --create-missing

# Upload both sample data and metadata together
popup upload --sample config.yaml --metadata metadata.tsv --api http://localhost:8000/api --username admin --password admin
```

Use `--dry-run` to parse without uploading:

```bash
popup upload --sample config.yaml --dry-run --verbose
```

### Test Connection

Test connection to Eyrie API:

```bash
popup test-connection --api http://localhost:8000/api --username admin --password admin
```

### Metadata Upload

Upload sample metadata from TSV or CSV files. The metadata file should contain columns for `sample_id` and optional fields like `sample_type`, `tissue`, `sanger_expected_species`, etc.

```bash
# Upload metadata only, creating missing samples
popup upload --metadata metadata.tsv --create-missing --api http://localhost:8000/api --username admin --password admin

# Upload metadata for existing samples only
popup upload --metadata metadata.tsv --api http://localhost:8000/api --username admin --password admin
```

The `--create-missing` flag allows the tool to create new sample entries for samples that don't exist in the database.

## Configuration Format

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

# Analysis output directory containing pipeline output directories (fastqc, krona, nanoplot_processed, etc.)
analysis_output_dirpath: "/path/to/analysis/results"

# Pipeline software used for analysis (trana, metaval, etc.)
pipeline_software: "trana"

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
      # ... additional HTML files
  processed:
    enabled: true
    directory: "nanoplot_processed" 
    stats_file: "barcode01_nanoplot_processed_NanoStats.txt"
    html_files:
      - "barcode01_nanoplot_processed_NanoPlot-report.html"
      # ... additional HTML files

# Analysis results
results:
  enabled: true
  directory: "results"
  rel_abundance_file: "barcode01_filtered.fastq_rel-abundance.tsv"
```

## Supported File Types

- **FastQC**: HTML quality control reports per sample
- **Krona**: Interactive taxonomic classification plots
- **MultiQC**: Aggregated quality control reports
- **NanoPlot**: Nanopore-specific quality plots and statistics
- **Taxonomic Abundances**: Relative abundance TSV files
- **Pipeline Files**: Associated analysis outputs

## Contamination Detection

The tool can automatically detect potential contaminants based on:

- Species names in a suspected contaminants list
- Abundance thresholds (e.g., >5% abundance)
- Custom contamination rules

## API Integration

Samples are uploaded to Eyrie with:

- Quality control status (passed/failed/unprocessed)
- Statistical summaries
- File paths for visualization
- Taxonomic classification data
- Contamination flags

## Development

Install development dependencies:

```bash
pip install -e ".[dev]"
```

