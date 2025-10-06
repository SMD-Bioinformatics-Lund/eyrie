"""Command line interface for Eyrie POPUP (Pipeline Output Processor and UPloader)."""

import os
import yaml
import click
from pathlib import Path
from typing import Optional

from .models import SampleConfig
from .parser import SampleParser
from .api_client import EyrieAPIClient


@click.group()
@click.version_option(version="0.1.0", prog_name="eyrie-popup")
def cli():
    """Eyrie POPUP - Pipeline Output Processor and UPloader for sequencing analysis results."""
    pass


@cli.command()
@click.option('-s', '--sample', 'sample_cnf', required=True, type=click.Path(exists=True, path_type=Path), help='YAML configuration file for the sample')
@click.option('--api', default='http://localhost:8000/api', help='Eyrie API base URL')
@click.option('--username', envvar='EYRIE_USER', help='Username for authentication (or set EYRIE_USER env var)')
@click.option('--password', envvar='EYRIE_PASSWORD', help='Password for authentication (or set EYRIE_PASSWORD env var)')
@click.option('--dry-run', is_flag=True, help='Parse data but do not upload to database')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
def upload(sample_cnf: Path, api: str, username: Optional[str], password: Optional[str], dry_run: bool, verbose: bool):
    """Parse analysis results from YAML configuration and upload to Eyrie."""

    click.echo(f"🔬 Eyrie POPUP - Pipeline Output Processor & UPloader")
    click.echo(f"📁 Config file: {sample_cnf}")

    try:
        # Load configuration
        with open(sample_cnf, 'r') as f:
            config_data = yaml.safe_load(f)

        config = SampleConfig(**config_data)

        if verbose:
            click.echo(f"🧬 Sample: {config.sample.sample_id}")
            click.echo(f"📂 Base path: {config.base_path}")
            click.echo(f"🔗 API URL: {api}")

        # Parse the sample
        click.echo("\n🔍 Parsing analysis files...")
        parser = SampleParser(config)
        parsed_sample = parser.parse_sample()

        # Display parsing results
        sample_data = parsed_sample.sample_data
        click.echo(f"✓ Parsed sample: {sample_data.sample_info.sample_id}")

        if sample_data.fastqc_file:
            click.echo(f"  ✓ FastQC: {sample_data.fastqc_file}")

        if sample_data.krona_file:
            click.echo(f"  ✓ Krona: {sample_data.krona_file}")

        if sample_data.nano_stats_processed:
            stats = sample_data.nano_stats_processed
            click.echo(f"  ✓ NanoStats (processed): {stats.number_of_reads:,} reads, Q{stats.mean_read_quality:.1f}")

        if sample_data.nano_stats_unprocessed:
            stats = sample_data.nano_stats_unprocessed
            click.echo(f"  ✓ NanoStats (unprocessed): {stats.number_of_reads:,} reads, Q{stats.mean_read_quality:.1f}")

        if sample_data.taxonomic_abundances:
            total_species = len(sample_data.taxonomic_abundances)
            contaminants = sum(1 for taxa in sample_data.taxonomic_abundances if taxa.contamination)
            click.echo(f"  ✓ Taxonomic data: {total_species} species")
            if contaminants > 0:
                click.echo(f"  ⚠️  Potential contaminants: {contaminants}")

        # Add debug info about nanoplot structure
        if sample_data.nanoplot:
            click.echo(f"  ✓ Structured nanoplot data available")
        else:
            click.echo(f"  ✗ No structured nanoplot data found")

        if dry_run:
            click.echo("\n🏃 Dry run mode - skipping database upload")
            return

        # Upload to Eyrie
        click.echo("\n📤 Uploading to Eyrie database...")

        api_client = EyrieAPIClient(api, username, password)

        # Test connection
        if not api_client.test_connection():
            click.echo("❌ Cannot connect to Eyrie API")
            return

        # Upload the sample
        if api_client.upload_sample(parsed_sample, config):
            click.echo("✅ Successfully uploaded sample to Eyrie!")
        else:
            click.echo("❌ Failed to upload sample")

    except Exception as e:
        click.echo(f"❌ Error: {e}")
        if verbose:
            import traceback
            traceback.print_exc()


@cli.command()
@click.argument('trana_output_dirpath', type=click.Path(exists=True, path_type=Path))
@click.argument('sample_id')
@click.option('--output', '-o', type=click.Path(path_type=Path), 
              help='Output YAML file (default: {sample_id}_config.yaml)')
@click.option('--sample-name', help='Sample name (default: Sample_{sample_id})')
@click.option('--lims-id', help='LIMS identifier (default: LIMS_{sample_id})')
@click.option('--run-id', help='Sequencing run identifier')
@click.option('--run-dir', help='Run directory name (default: auto-detect from path or use run-id)')
@click.option('--classification', type=click.Choice(['16S', 'ITS']), default='16S',
              help='Classification type')
def generate_config(trana_output_dirpath: Path, sample_id: str, output: Optional[Path], 
                   sample_name: Optional[str], lims_id: Optional[str], 
                   run_id: Optional[str], run_dir: Optional[str], classification: str):
    """Generate a YAML configuration file for a single sample."""

    click.echo(f"🔍 Generating config for sample: {sample_id}")
    click.echo(f"📁 TRANA output path: {trana_output_dirpath}")
    click.echo(f"📁 Base path (parent): {trana_output_dirpath.parent}")

    # Generate defaults
    if not sample_name:
        sample_name = f"Sample_{sample_id}"

    if not lims_id:
        lims_id = f"LIMS_{sample_id}"

    if not run_id:
        from datetime import datetime
        run_id = f"RUN_{datetime.now().strftime('%Y_%m_%d')}"

    # Determine run directory
    if not run_dir:
        # Try to auto-detect from trana_output_dirpath
        trana_output_dir_name = trana_output_dirpath.name
        if trana_output_dir_name and trana_output_dir_name != ".":
            run_dir = trana_output_dir_name
        else:
            # Fallback to run_id
            run_dir = run_id

    # Create configuration
    config = {
        "sample": {
            "sample_id": sample_id,
            "sample_name": sample_name,
            "lims_id": lims_id,
            "barcode": sample_id if sample_id.startswith("barcode") else None,
            "sequencing_run_id": run_id,
            "classification_type": classification
        },
        "base_path": str(trana_output_dirpath.parent),
        "run_directory": run_dir,
        "fastqc": {
            "enabled": True,
            "directory": "fastqc",
            "file": f"{sample_id}_fastqc.html"
        },
        "krona": {
            "enabled": True,
            "directory": "krona", 
            "file": f"{sample_id}_krona.html"
        },
        "multiqc": {
            "enabled": True,
            "directory": "multiqc",
            "report_file": "multiqc_report.html"
        },
        "nanoplot": {
            "unprocessed": {
                "enabled": True,
                "directory": "nanoplot_unprocessed",
                "stats_file": f"{sample_id}_nanoplot_unprocessed_NanoStats.txt",
                "html_files": [
                    f"{sample_id}_nanoplot_unprocessed_NanoPlot-report.html",
                    f"{sample_id}_nanoplot_unprocessed_LengthvsQualityScatterPlot_dot.html",
                    f"{sample_id}_nanoplot_unprocessed_LengthvsQualityScatterPlot_kde.html",
                    f"{sample_id}_nanoplot_unprocessed_Non_weightedHistogramReadlength.html",
                    f"{sample_id}_nanoplot_unprocessed_WeightedHistogramReadlength.html",
                    f"{sample_id}_nanoplot_unprocessed_Yield_By_Length.html"
                ]
            },
            "processed": {
                "enabled": True,
                "directory": "nanoplot_processed",
                "stats_file": f"{sample_id}_nanoplot_processed_NanoStats.txt",
                "html_files": [
                    f"{sample_id}_nanoplot_processed_NanoPlot-report.html",
                    f"{sample_id}_nanoplot_processed_LengthvsQualityScatterPlot_dot.html",
                    f"{sample_id}_nanoplot_processed_LengthvsQualityScatterPlot_kde.html",
                    f"{sample_id}_nanoplot_processed_Non_weightedHistogramReadlength.html",
                    f"{sample_id}_nanoplot_processed_WeightedHistogramReadlength.html",
                    f"{sample_id}_nanoplot_processed_Yield_By_Length.html"
                ]
            }
        },
        "results": {
            "enabled": True,
            "directory": "results",
            "rel_abundance_file": f"{sample_id}_filtered.fastq_rel-abundance.tsv"
        }
    }

    # Write configuration file
    if not output:
        output = Path(f"{sample_id}_config.yaml")

    with open(output, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, indent=2)

    click.echo(f"✅ Generated configuration: {output}")
    click.echo(f"\n🚀 Run with: popup upload --sample {output} --api <api_url> --username <user> --password <pass>")


@cli.command()
@click.option('--api', default='http://localhost:8000/api', help='Eyrie API base URL')
@click.option('--username', envvar='EYRIE_USER', help='Username for authentication (or set EYRIE_USER env var)')
@click.option('--password', envvar='EYRIE_PASSWORD', help='Password for authentication (or set EYRIE_PASSWORD env var)')
def test_connection(api: str, username: Optional[str], password: Optional[str]):
    """Test connection to Eyrie API."""

    click.echo(f"🔗 Testing connection to: {api}")

    client = EyrieAPIClient(api, username, password)

    if client.test_connection():
        if username and password:
            if client.authenticate():
                click.echo("✅ Connection and authentication successful!")
            else:
                click.echo("⚠️  Connection successful but authentication failed")
        else:
            click.echo("✅ Connection successful (no authentication provided)")
    else:
        click.echo("❌ Connection failed")


if __name__ == '__main__':
    cli()
