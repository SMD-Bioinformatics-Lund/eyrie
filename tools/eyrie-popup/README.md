# Eyrie POPUP - Pipeline Output Processor and UPloader

A Python tool for processing pipeline outputs and uploading sequencing analysis results to the Eyrie database.

## Features

- **YAML Configuration**: Flexible configuration format for describing analysis runs
- **Multi-format Support**: Parse FastQC, Krona, MultiQC, NanoPlot, and taxonomic abundance files
- **Contamination Detection**: Automatic flagging of potential contaminants
- **API Integration**: Direct upload to Eyrie database via REST API
- **CLI Interface**: Easy-to-use command line tool

## Installation

```bash
cd tools/eyrie-popup
pip install -e .
```

## Usage

### Generate Configuration

Auto-generate a configuration file for a sample:

```bash
popup generate-config /path/to/analysis/results sample_id --output config.yaml
```

### Upload Sample

Parse analysis results and upload to Eyrie:

```bash
popup upload --sample config.yaml --api http://localhost:8000/api --username admin --password admin
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

# Base directory containing all analysis outputs
base_path: "/path/to/analysis/results"

# Run directory name for file paths (defaults to sequencing_run_id if not specified)
run_directory: "test"

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

