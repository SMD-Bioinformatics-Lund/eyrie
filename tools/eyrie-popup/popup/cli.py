"""Command line interface for Eyrie POPUP (Pipeline Output Processor and UPloader)."""

from datetime import datetime
from pathlib import Path
from typing import Optional
import os
import yaml
import click

from .models import SampleConfig
from .parser import SampleParser
from .parser.metadata import MetadataParser, validate_metadata_file
from .parser.seqrun_metadata import SeqrunMetadataParser
from .api import EyrieAPIClient
from .__version__ import __version__


@click.group()
@click.version_option(version=__version__, prog_name="eyrie-popup")
def cli():
    """Eyrie POPUP - Pipeline Output Processor and UPloader for sequencing analysis results.

    POPUP processes and uploads sequencing analysis data to the Eyrie database, supporting:
    - Sample-level data (FastQC, Krona plots, NanoPlot, taxonomic abundances) 
    - Metadata (sample information from TSV/CSV files)
    - Pipeline data (parameters, execution traces, software versions, HTML reports)

    Use 'popup COMMAND --help' for detailed information about each command.
    """
    pass


def _upload_sample_data(sample_cnf: Path, api: str, username: Optional[str], password: Optional[str],
                       dry_run: bool, verbose: bool, pipeline_datetime_suffix: Optional[str] = None,
                       force: bool = False) -> bool:
    """Upload sample analysis data from YAML configuration.

    Processes and uploads sample-level sequencing analysis data including:
    - Quality control reports (FastQC HTML files)
    - Taxonomic classification plots (Krona HTML files)  
    - Quality plots (NanoPlot HTML and stats files)
    - Taxonomic abundance data (TSV files)
    - Associated sample metadata

    Args:
        sample_cnf: Path to YAML configuration file describing sample data
        api: Eyrie API base URL
        username: Username for authentication
        password: Password for authentication
        dry_run: If True, parse data but don't upload to database
        verbose: Enable detailed output
        pipeline_datetime_suffix: Optional timestamp to include matching pipeline data

    Returns:
        bool: True if upload successful, False otherwise
    """

    click.echo(f"📁 Sample config: {sample_cnf}")

    try:
        # Load configuration
        with open(sample_cnf, 'r') as f:
            config_data = yaml.safe_load(f)

        config = SampleConfig(**config_data)

        if verbose:
            click.echo(f"🧬 Sample: {config.sample.sample_id}")
            click.echo(f"📂 Analysis output directory: {config.analysis_output_dirpath}")

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

            # Display spike species detection
            if hasattr(sample_data, 'spike') and sample_data.spike:
                # Find abundance for the spike species
                spike_abundance = None
                for taxa in sample_data.taxonomic_abundances:
                    if taxa.species == sample_data.spike:
                        spike_abundance = taxa.abundance
                        break
                if spike_abundance is not None:
                    click.echo(f"  🎯 Spike species detected: {sample_data.spike} ({spike_abundance:.2%})")
                else:
                    click.echo(f"  🎯 Spike species detected: {sample_data.spike}")
            else:
                click.echo(f"  ❌ No spike species detected")

        # Add debug info about nanoplot structure
        if sample_data.nanoplot:
            click.echo(f"  ✓ Structured nanoplot data available")
        else:
            click.echo(f"  ✗ No structured nanoplot data found")

        if dry_run:
            click.echo("\n🏃 Dry run mode - skipping sample data upload")

            # In dry run mode, show what would be uploaded
            if verbose:
                temp_client = EyrieAPIClient(api, username, password)
                eyrie_sample = temp_client._convert_to_eyrie_format(sample_data, config)
                click.echo(f"\n📋 Would upload spike field: {eyrie_sample.get('spike', 'NOT_FOUND')}")
                click.echo(f"📋 Sample data spike attr: {getattr(sample_data, 'spike', 'NO_SPIKE_ATTR')}")
            return True

        click.echo("\n📤 Uploading sample data to Eyrie database...")

        api_client = EyrieAPIClient(api, username, password)

        if not api_client.test_connection():
            click.echo("❌ Cannot connect to Eyrie API")
            return False

        # Upload the sample
        if api_client.upload_sample(parsed_sample, config, pipeline_datetime_suffix, force=force):
            click.echo("✅ Successfully uploaded sample data to Eyrie!")
            return True
        else:
            click.echo("❌ Failed to upload sample data")
            return False

    except Exception as e:
        click.echo(f"❌ Error uploading sample data: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        return False


def _upload_seqrun_metadata(seqrun_metadata_file: Path, sequencing_run_id: str, api: str, 
                           username: Optional[str], password: Optional[str], dry_run: bool, verbose: bool) -> bool:
    """Upload sequencing run metadata from markdown report file."""
    click.echo(f"📁 Sequencing run metadata file: {seqrun_metadata_file}")

    try:
        # Parse metadata from markdown file
        click.echo("\n🔍 Parsing sequencing run metadata...")
        parser = SeqrunMetadataParser()
        metadata = parser.parse(seqrun_metadata_file)

        if not metadata:
            click.echo("❌ Failed to parse metadata from file")
            return False

        if not parser.validate_metadata(metadata):
            click.echo("❌ Metadata validation failed")
            return False

        click.echo(f"✅ Successfully parsed metadata with {len(metadata)} fields")
        if verbose:
            for key, value in metadata.items():
                click.echo(f"   {key}: {value}")

        if dry_run:
            click.echo("\n🏃 Dry run mode - skipping sequencing run metadata upload")
            return True

        # Upload to seqruns collection
        click.echo("\n📤 Uploading sequencing run metadata to Eyrie...")
        api_client = EyrieAPIClient(api, username, password)
        if not api_client.test_connection():
            click.echo("❌ Cannot connect to Eyrie API")
            return False

        # Create or update seqrun with metadata
        try:
            result = api_client.create_or_update_seqrun_metadata(sequencing_run_id, metadata)
            if result:
                click.echo("✅ Sequencing run metadata uploaded successfully")
                return True
            else:
                click.echo("❌ Failed to upload sequencing run metadata")
                return False
        except Exception as e:
            click.echo(f"❌ Exception in create_or_update_seqrun_metadata: {e}")
            if verbose:
                import traceback
                traceback.print_exc()
            return False

    except Exception as e:
        click.echo(f"❌ Error processing sequencing run metadata: {e}")
        if verbose:
            import traceback
            click.echo("Full traceback:")
            click.echo(traceback.format_exc())
        return False

def _upload_sample_metadata(sample_metadata_file: Path, api: str, username: Optional[str], password: Optional[str], 
                    dry_run: bool, verbose: bool, create_missing: bool) -> bool:
    """Upload sample metadata from TSV/CSV file."""

    click.echo(f"📁 Sample metadata file: {sample_metadata_file}")

    try:
        # Validate file format first
        click.echo("\n🔍 Validating metadata file format...")
        is_valid, errors = validate_metadata_file(sample_metadata_file)

        if not is_valid:
            click.echo("❌ Sample metadata file validation failed:")
            for error in errors:
                click.echo(f"  • {error}")
            return False

        click.echo("✓ Sample metadata file format is valid")

        # Parse sample metadata
        click.echo("\n📖 Parsing sample metadata...")
        parser = MetadataParser(sample_metadata_file)
        sample_metadata_dict = parser.parse()

        if not sample_metadata_dict:
            click.echo("❌ No valid sample metadata entries found in file")
            return False

        click.echo(f"✓ Parsed {len(sample_metadata_dict)} sample metadata entries")

        if verbose:
            click.echo(f"👤 Create missing samples: {create_missing}")

        # Display parsed entries
        for sample_id, sample_metadata in sample_metadata_dict.items():
            click.echo(f"  ✓ {sample_id}")
            if verbose:
                if sample_metadata.sample_type:
                    click.echo(f"    • Type: {sample_metadata.sample_type}")
                if sample_metadata.material:
                    click.echo(f"    • Material: {sample_metadata.material}")
                if sample_metadata.sanger_expected_species:
                    click.echo(f"    • Expected species: {sample_metadata.sanger_expected_species}")

        if dry_run:
            click.echo("\n🏃 Dry run mode - skipping sample metadata upload")
            click.echo(f"📊 Would process {len(sample_metadata_dict)} samples")
            return True

        # Upload sample metadata
        click.echo("\n📤 Uploading sample metadata to Eyrie...")

        api_client = EyrieAPIClient(api, username, password)

        if not api_client.test_connection():
            click.echo("❌ Cannot connect to Eyrie API")
            return False

        # Process each sample
        created_count = 0
        updated_count = 0
        failed_count = 0

        for sample_id, sample_metadata in sample_metadata_dict.items():
            try:
                success, action = api_client.upload_sample_metadata(sample_id, sample_metadata, create_missing)

                if success:
                    if action == "created":
                        created_count += 1
                        click.echo(f"  ✓ Created sample: {sample_id}")
                    elif action == "updated":
                        updated_count += 1
                        click.echo(f"  ✓ Updated sample: {sample_id}")
                else:
                    failed_count += 1
                    click.echo(f"  ❌ Failed to process sample: {sample_id}")

            except Exception as e:
                failed_count += 1
                click.echo(f"  ❌ Error processing {sample_id}: {e}")
                if verbose:
                    import traceback
                    traceback.print_exc()

        # Summary
        click.echo(f"\n📊 Sample Metadata Upload Summary:")
        if created_count > 0:
            click.echo(f"  ✅ Created: {created_count} samples")
        if updated_count > 0:
            click.echo(f"  ✅ Updated: {updated_count} samples")
        if failed_count > 0:
            click.echo(f"  ❌ Failed: {failed_count} samples")

        if failed_count == 0:
            click.echo("🎉 All sample metadata uploaded successfully!")

        return failed_count == 0

    except Exception as e:
        click.echo(f"❌ Error uploading sample metadata: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        return False


def _upload_pipeline_files_only(sequencing_run_id: str, pipeline_datetime_suffix: str, api: str, 
                                username: Optional[str], password: Optional[str], dry_run: bool, verbose: bool,
                                analysis_output_dirpath: Optional[Path], pipeline_software: str) -> bool:
    """Upload structured pipeline data and HTML reports for a sequencing run.

    This function uploads sequencing run-level data including:
    - Pipeline parameters (parsed from params_*.json)
    - Execution trace (parsed from execution_trace_*.txt) 
    - Software versions (parsed from software_versions.yml)
    - HTML reports (execution_report_*.html, execution_timeline_*.html, pipeline_dag_*.html)

    Args:
        sequencing_run_id: Unique identifier for the sequencing run
        pipeline_datetime_suffix: Timestamp suffix to match specific pipeline files
        api: Eyrie API base URL
        username: Username for authentication
        password: Password for authentication  
        dry_run: If True, parse files but don't upload to database
        verbose: Enable detailed output
        analysis_output_dirpath: Path to analysis results directory containing pipeline software output directories (e.g. fastqc, krona, nanoplot_processed, etc.)
        pipeline_software: Pipeline software used (trana, metaval, etc.)

    Returns:
        bool: True if upload successful, False otherwise
    """

    try:
        click.echo(f"🏃 Sequencing run: {sequencing_run_id}")
        click.echo(f"📅 Pipeline datetime suffix: {pipeline_datetime_suffix}")

        if dry_run:
            click.echo("\n🏃 Dry run mode - skipping pipeline files upload")
            click.echo("📋 Would upload pipeline files for sequencing run")
            return True

        click.echo("\n📤 Uploading pipeline files to Eyrie database...")

        # Create API client
        api_client = EyrieAPIClient(api, username, password)

        if not api_client.test_connection():
            click.echo("❌ Cannot connect to Eyrie API")
            return False

        # Authenticate if credentials are provided
        if username and password:
            if not api_client.authenticate():
                click.echo("❌ Authentication failed")
                return False

        # Determine analysis output directory path
        if analysis_output_dirpath:
            analysis_output_dirpath = str(analysis_output_dirpath)
        else:
            # Check environment variables as fallback (in order of preference)
            env_analysis_path = os.getenv('EYRIE_ANALYSIS_OUTPUT_DIRPATH')
            if env_analysis_path:
                analysis_output_dirpath = env_analysis_path
            else:
                click.echo("❌ Error: Analysis output directory must be specified.")
                click.echo("Please provide either:")
                click.echo("  --analysis-output-dirpath argument, OR")
                click.echo("  Set EYRIE_ANALYSIS_OUTPUT_DIRPATH environment variable")
                click.echo("")
                click.echo("See README.md for examples and detailed usage instructions.")
                return False

        # Upload pipeline files only
        if api_client.upload_handler.upload_pipeline_files_only(sequencing_run_id, pipeline_software, pipeline_datetime_suffix, analysis_output_dirpath):
            click.echo("✅ Successfully uploaded pipeline files!")
            return True
        else:
            click.echo("❌ Failed to upload pipeline files")
            return False

    except Exception as e:
        click.echo(f"❌ Error uploading pipeline files: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        return False


@cli.command()
@click.option('-s', '--sample', 'sample_cnf', type=click.Path(exists=True, path_type=Path), help='YAML configuration file for sample analysis data [optional]')
@click.option('-m', '--sample-metadata', 'sample_metadata_file', type=click.Path(exists=True, path_type=Path), help='TSV or CSV sample metadata file [optional]')
@click.option('--sequencing-run-metadata', 'seqrun_metadata_file', type=click.Path(exists=True, path_type=Path), help='Markdown report file with sequencing run metadata [optional]')
@click.option('--api', default='http://localhost:8000/api', help='Eyrie API base URL')
@click.option('--username', envvar='EYRIE_USER', help='Username for authentication (or set EYRIE_USER env var)')
@click.option('--password', envvar='EYRIE_PASSWORD', help='Password for authentication (or set EYRIE_PASSWORD env var)')
@click.option('--dry-run', is_flag=True, help='Parse data but do not upload to database')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.option('--force', '-f', is_flag=True, help='Force upload even if sample has existing comments')
@click.option('--create-missing', is_flag=True, help='Create sample entries for samples that do not exist (sample metadata only)')
@click.option('--sequencing-run-id', help='Sequencing run identifier (required for pipeline-only uploads)')
@click.option('--pipeline-datetime-suffix', help='Datetime suffix (YYYY-MM-DD_HH-MM-SS) to match specific pipeline files by timestamp')
@click.option('--analysis-output-dirpath', type=click.Path(exists=True, path_type=Path), help='Path to analysis results directory containing pipeline software output results subdirectories (e.g., /path/to/analysis-files/results/trana)')
@click.option('--pipeline-software', default='trana', help='Pipeline software used for analysis (default: trana). Options: trana, metaval, etc.')
def upload(sample_cnf: Optional[Path], sample_metadata_file: Optional[Path], seqrun_metadata_file: Optional[Path], api: str,
          username: Optional[str], password: Optional[str], dry_run: bool, verbose: bool, force: bool, create_missing: bool,
          sequencing_run_id: Optional[str], pipeline_datetime_suffix: Optional[str],
          analysis_output_dirpath: Optional[Path], pipeline_software: str):
    """Upload sample analysis data, sample metadata, sequencing run metadata, and/or pipeline files to Eyrie.

    Upload modes:
      1. Sample data: -s/--sample (YAML config file)
      2. Sample metadata: -m/--sample-metadata (TSV/CSV file) 
      3. Sequencing run metadata: --sequencing-run-metadata (Markdown file)
      4. Pipeline files: --pipeline-datetime-suffix + --sequencing-run-id + --analysis-output-dirpath
  
    Pipeline files include structured data (parameters JSON, execution trace TSV, software versions YAML) 
    and HTML reports (execution report, timeline, DAG) for sequencing run-level analysis.

    For detailed usage examples and configuration options, see the README.md file.
    """

    try:
        # Validate arguments
        if not sample_cnf and not sample_metadata_file and not seqrun_metadata_file and not pipeline_datetime_suffix:
            click.echo("❌ Error: At least one of --sample (-s), --sample-metadata (-m), --sequencing-run-metadata, or --pipeline-datetime-suffix must be provided")
            click.echo("\nExamples:")
            click.echo("  popup upload -s sample_config.yaml")
            click.echo("  popup upload -m sample_metadata.tsv")
            click.echo("  popup upload -s config.yaml -m sample_metadata.tsv")
            click.echo("  popup upload --sequencing-run-id 20250930_1234 --pipeline-datetime-suffix 2025-09-30_09-46-56")
            return

        # Validate pipeline-datetime-suffix requirements
        if pipeline_datetime_suffix and not sample_cnf and not sequencing_run_id:
            click.echo("❌ Error: When using --pipeline-datetime-suffix without --sample, --sequencing-run-id must be provided")
            click.echo("\nSee README.md for examples and detailed usage instructions.")
            return

        click.echo(f"🔬 Eyrie POPUP - Pipeline Output Processor & UPloader")

        if verbose:
            click.echo(f"🔗 API URL: {api}")
            click.echo(f"🔍 Arguments: sample_cnf={sample_cnf}, sample_metadata_file={sample_metadata_file}, pipeline_datetime_suffix={pipeline_datetime_suffix}, sequencing_run_id={sequencing_run_id}")

        sample_success = True
        sample_metadata_success = True

        # Upload sample analysis data if provided
        if sample_cnf:
            click.echo(f"\n📊 Processing sample analysis data...")
            sample_success = _upload_sample_data(sample_cnf, api, username, password, dry_run, verbose, pipeline_datetime_suffix, force=force)

        # Upload sample metadata if provided
        if sample_metadata_file:
            click.echo(f"\n📋 Processing sample metadata...")
            sample_metadata_success = _upload_sample_metadata(sample_metadata_file, api, username, password, dry_run, verbose, create_missing)

        # Upload sequencing run metadata if provided
        seqrun_metadata_success = True
        if seqrun_metadata_file:
            if not sequencing_run_id:
                click.echo("❌ Error: --sequencing-run-id is required when using --sequencing-run-metadata")
                return
            click.echo(f"\n📋 Processing sequencing run metadata...")
            seqrun_metadata_success = _upload_seqrun_metadata(seqrun_metadata_file, sequencing_run_id, api, username, password, dry_run, verbose)

        # Upload pipeline files only if provided
        pipeline_success = True
        if pipeline_datetime_suffix and not sample_cnf and sequencing_run_id:
            click.echo(f"\n🔧 Processing pipeline files only...")
            pipeline_success = _upload_pipeline_files_only(sequencing_run_id, pipeline_datetime_suffix, api, username, password, dry_run, verbose, analysis_output_dirpath, pipeline_software)
        elif pipeline_datetime_suffix and not sample_cnf:
            if verbose:
                click.echo(f"\n🔍 Debug: pipeline_datetime_suffix={pipeline_datetime_suffix}, sample_cnf={sample_cnf}, sequencing_run_id={sequencing_run_id}")
                click.echo("❌ Missing sequencing_run_id for pipeline-only upload")

        # Overall summary for combined uploads only
        if sample_cnf and sample_metadata_file:
            click.echo(f"\n🎯 Overall Summary:")
            if sample_success and sample_metadata_success:
                click.echo("✅ Both sample data and sample metadata uploaded successfully!")
            elif sample_success:
                click.echo("⚠️  Sample data uploaded, but sample metadata failed")
            elif sample_metadata_success:
                click.echo("⚠️  Sample metadata uploaded, but sample data failed") 
            else:
                click.echo("❌ Both uploads failed")

    except Exception as e:
        click.echo(f"❌ Unexpected error in upload: {e}")
        if verbose:
            import traceback
            traceback.print_exc()


@cli.command()
@click.option('--analysis-output-dirpath', required=True, type=click.Path(exists=True, path_type=Path), 
              help='Path to analysis output directory containing pipeline subdirectories (fastqc, krona, nanoplot_processed, etc.)')
@click.option('--sample-id', required=True, help='Sample identifier')
@click.option('--output', '-o', type=click.Path(path_type=Path), 
              help='Output YAML file (default: {sample_id}_config.yaml)')
@click.option('--sample-name', help='Sample name (default: Sample_{sample_id})')
@click.option('--lims-id', help='LIMS identifier (default: LIMS_{sample_id})')
@click.option('--sequencing-run-id', help='Sequencing run identifier')
@click.option('--classification', type=click.Choice(['16S', 'ITS']), default='16S',
              help='Classification type')
@click.option('--pipeline-software', default='trana', help='Pipeline software used (trana, metaval, etc.)')
def generate_config(analysis_output_dirpath: Path, sample_id: str, output: Optional[Path], 
                   sample_name: Optional[str], lims_id: Optional[str], 
                   sequencing_run_id: Optional[str], classification: str, pipeline_software: str):
    """Generate a YAML configuration file for a single sample.

    Creates a YAML config file that can be used with 'popup upload -s' to upload sample analysis data.
    The analysis-output-dirpath should point to the directory containing analysis subdirectories.

    For usage examples and configuration options, see the README.md file.
    """

    click.echo(f"🔍 Generating config for sample: {sample_id}")
    click.echo(f"📁 Analysis output directory: {analysis_output_dirpath}")
    click.echo(f"🔧 Pipeline software: {pipeline_software}")

    # Generate defaults
    if not sample_name:
        sample_name = f"Sample_{sample_id}"

    if not lims_id:
        lims_id = f"LIMS_{sample_id}"

    if not sequencing_run_id:
        sequencing_run_id = f"RUN_{datetime.now().strftime('%Y_%m_%d')}"

    # Create configuration
    config = {
        "sample": {
            "sample_id": sample_id,
            "sample_name": sample_name,
            "lims_id": lims_id,
            "barcode": sample_id if sample_id.startswith("barcode") else None,
            "sequencing_run_id": sequencing_run_id,
            "classification_type": classification,
            "pipeline_software": pipeline_software
        },
        "analysis_output_dirpath": str(analysis_output_dirpath),
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
            "rel_abundance_file": f"{sample_id}*.fastq_rel-abundance.tsv"
        }
    }

    # Write configuration file
    if not output:
        output = Path(f"{sample_id}_config.yaml")

    with open(output, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, indent=2)

    click.echo(f"✅ Generated configuration: {output}")
    click.echo(f"\n🚀 Use 'popup upload --sample {output}' to upload sample data.")
    click.echo(f"   See README.md for complete usage examples.")


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
