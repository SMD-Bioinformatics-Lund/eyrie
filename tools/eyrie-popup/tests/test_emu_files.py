import pytest
import yaml
from click.testing import CliRunner

from popup.api.format import FormatHandler
from popup.cli import cli
from popup.models import SampleConfig
from popup.parser import SampleParser
from popup.parser.taxonomic import TaxonomicParser

ABUNDANCE = 'tax_id\tabundance\tspecies\tgenus\testimated counts\n562\t0.7\tEscherichia coli\tEscherichia\t700\n'
READ_ASSIGNMENT = 'read\t562\nr1\t0.9\nr2\t0.8\n'


@pytest.fixture
def analysis(tmp_path):
    (tmp_path / 'results').mkdir()
    return tmp_path


def write(analysis, name, content=ABUNDANCE):
    (analysis / 'results' / name).write_text(content)


def generate_config(analysis, *args):
    output = analysis / 'config.yaml'
    result = CliRunner().invoke(cli, ['generate-config', '--analysis-output-dirpath', str(analysis),
                                      '--sample-id', 'barcode01', '--output', str(output), *args])
    return result, yaml.safe_load(output.read_text())['results'] if output.exists() else None


def test_read_assignment_comes_from_the_same_emu_run(analysis):
    write(analysis, 'barcode01_filtered.fastq_rel-abundance.tsv')
    write(analysis, 'barcode01_filtered.fastq_read-assignment-distributions.tsv', READ_ASSIGNMENT)
    write(analysis, 'barcode01_downsampled.fastq_read-assignment-distributions.tsv', READ_ASSIGNMENT)
    result, results = generate_config(analysis)
    assert result.exit_code == 0, result.output
    assert results['rel_abundance_file'] == 'barcode01_filtered.fastq_rel-abundance.tsv'
    assert results['read_assignment_file'] == 'barcode01_filtered.fastq_read-assignment-distributions.tsv'


def test_several_rel_abundance_files_stop_generate_config(analysis):
    write(analysis, 'barcode01_filtered.fastq_rel-abundance.tsv')
    write(analysis, 'barcode01_downsampled.fastq_rel-abundance.tsv')
    result, results = generate_config(analysis)
    assert result.exit_code != 0
    assert 'Several' in result.output
    assert results is None


def test_explicit_rel_abundance_file_chooses_between_several(analysis):
    write(analysis, 'barcode01_filtered.fastq_rel-abundance.tsv')
    write(analysis, 'barcode01_downsampled.fastq_rel-abundance.tsv')
    result, results = generate_config(analysis, '--rel-abundance-file', 'barcode01_downsampled.fastq_rel-abundance.tsv')
    assert result.exit_code == 0, result.output
    assert results['rel_abundance_file'] == 'barcode01_downsampled.fastq_rel-abundance.tsv'
    assert results['read_assignment_file'] is None


def test_another_sample_with_the_same_prefix_is_not_used(analysis):
    write(analysis, 'barcode010_filtered.fastq_rel-abundance.tsv')
    result, results = generate_config(analysis)
    assert result.exit_code != 0
    assert 'No rel-abundance.tsv file for barcode01' in result.output


def test_missing_explicit_read_assignment_file_stops_generate_config(analysis):
    write(analysis, 'barcode01_filtered.fastq_rel-abundance.tsv')
    result, _ = generate_config(analysis, '--read-assignment-file', 'missing.tsv')
    assert result.exit_code != 0
    assert 'not found' in result.output


def sample_config(analysis, rel_abundance_file, read_assignment_file=None):
    return SampleConfig(
        sample={'sample_id': 'barcode01', 'sample_name': 'S1', 'lims_id': 'L1',
                'sequencing_run_id': 'RUN', 'classification_type': '16S'},
        analysis_output_dirpath=str(analysis),
        results={'rel_abundance_file': rel_abundance_file, 'read_assignment_file': read_assignment_file},
    )


def test_parser_rejects_a_pattern_matching_several_files(analysis):
    write(analysis, 'barcode01_filtered.fastq_rel-abundance.tsv')
    write(analysis, 'barcode01_downsampled.fastq_rel-abundance.tsv')
    config = sample_config(analysis, 'barcode01*.fastq_rel-abundance.tsv')
    with pytest.raises(ValueError, match='Several'):
        TaxonomicParser(analysis).parse_rel_abundance(config.results)


def test_parser_rejects_a_missing_rel_abundance_file(analysis):
    config = sample_config(analysis, 'barcode01_filtered.fastq_rel-abundance.tsv')
    with pytest.raises(FileNotFoundError):
        TaxonomicParser(analysis).parse_rel_abundance(config.results)


def test_unreadable_read_assignment_file_only_skips_probabilities(analysis, capsys):
    write(analysis, 'barcode01_filtered.fastq_rel-abundance.tsv')
    write(analysis, 'barcode01_filtered.fastq_read-assignment-distributions.tsv', '')
    config = sample_config(analysis, 'barcode01_filtered.fastq_rel-abundance.tsv',
                           'barcode01_filtered.fastq_read-assignment-distributions.tsv')
    sample_data = SampleParser(config).parse_sample().sample_data
    assert [taxa.species for taxa in sample_data.taxonomic_abundances] == ['Escherichia coli']
    assert sample_data.taxonomic_abundances[0].median_probability is None
    assert 'Skipped read assignment probabilities' in capsys.readouterr().out


def test_read_assignment_probabilities_are_added(analysis):
    write(analysis, 'barcode01_filtered.fastq_rel-abundance.tsv')
    write(analysis, 'barcode01_filtered.fastq_read-assignment-distributions.tsv', READ_ASSIGNMENT)
    config = sample_config(analysis, 'barcode01_filtered.fastq_rel-abundance.tsv',
                           'barcode01_filtered.fastq_read-assignment-distributions.tsv')
    taxa = SampleParser(config).parse_sample().sample_data.taxonomic_abundances[0]
    assert taxa.median_probability == pytest.approx(0.85)


def test_sample_without_results_has_no_taxonomic_data(analysis):
    config = sample_config(analysis, 'unused.tsv')
    config.results = None
    sample_data = SampleParser(config).parse_sample().sample_data
    assert FormatHandler().convert_to_eyrie_format(sample_data, config)['taxonomic_data'] is None


def test_sample_with_no_species_has_empty_hits(analysis):
    write(analysis, 'barcode01_filtered.fastq_rel-abundance.tsv', ABUNDANCE.splitlines()[0] + '\n')
    config = sample_config(analysis, 'barcode01_filtered.fastq_rel-abundance.tsv')
    sample_data = SampleParser(config).parse_sample().sample_data
    assert FormatHandler().convert_to_eyrie_format(sample_data, config)['taxonomic_data']['hits'] == []
