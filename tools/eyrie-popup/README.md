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
cd tools/eyrie_popup
pip install -e .
```

## Usage

### Generate Configuration

Auto-generate a configuration file by scanning an analysis directory:

```bash
eyrie-popup generate-config /path/to/analysis/results --output config.yaml
```

### Parse and Upload

Parse analysis results and upload to Eyrie:

```bash
eyrie-popup parse config.yaml
```

Use `--dry-run` to parse without uploading:

```bash
eyrie-popup parse config.yaml --dry-run --verbose
```

### Test Connection

Test connection to Eyrie API:

```bash
eyrie-popup test-connection --api-url http://localhost:3000/api
```

## Configuration Format

The YAML configuration file describes the analysis run structure:

```yaml
run:
  id: "RUN_2025_09_30"
  name: "Example Nanopore Run"
  date: "2025-09-30"
  platform: "nanopore"
  classification_type: "16S"

base_path: "/path/to/analysis/results"

samples:
  - sample_id: "barcode01"
    sample_name: "Sample_BC01"
    lims_id: "LIMS_BC01_001"
    barcode: "barcode01"

fastqc:
  enabled: true
  directory: "fastqc"
  pattern: "{sample_id}_fastqc.html"

krona:
  enabled: true
  directory: "krona"
  pattern: "{sample_id}_krona.html"

# ... additional configuration sections
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

Run tests:

```bash
pytest
```

## License

MIT License - see LICENSE file for details.