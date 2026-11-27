import pytest
import yaml
from click.testing import CliRunner

from popup.api.format import FormatHandler
from popup.cli import cli
from popup.models import SampleConfig
from popup.parser import SampleParser

ABUNDANCE = 'tax_id\tabundance\tspecies\tgenus\testimated counts\n562\t0.7\tEscherichia coli\tEscherichia\t700\n'
READ_ASSIGNMENT = 'read\t562\nr1\t0.9\nr2\t0.8\n'


@pytest.fixture
def analysis(tmp_path):
    (tmp_path / 'results').mkdir()
    return tmp_path


def write(analysis, name, content=ABUNDANCE):
    (analysis / 'results' / name).write_text(content)


def generate_config(analysis):
    output = analysis / 'config.yaml'
    result = CliRunner().invoke(cli, ['generate-config', '--analysis-output-dirpath', str(analysis),
                                      '--sample-id', 'barcode01', '--output', str(output)])
    return result, yaml.safe_load(output.read_text())['results'] if output.exists() else None


def sample_config(analysis, rel_abundance_file, read_assignment_file=None):
    return SampleConfig(
        sample={'sample_id': 'barcode01', 'sample_name': 'S1', 'lims_id': 'L1',
                'sequencing_run_id': 'RUN', 'classification_type': '16S'},
        analysis_output_dirpath=str(analysis),
        results={'rel_abundance_file': rel_abundance_file, 'read_assignment_file': read_assignment_file},
    )


def parse(config):
    return SampleParser(config).parse_sample().sample_data


def test_generate_config_takes_the_read_assignment_file_from_the_same_emu_run(analysis):
    write(analysis, 'barcode01_filtered.fastq_rel-abundance.tsv')
    write(analysis, 'barcode01_filtered.fastq_read-assignment-distributions.tsv', READ_ASSIGNMENT)
    write(analysis, 'barcode01_downsampled.fastq_read-assignment-distributions.tsv', READ_ASSIGNMENT)

    result, results = generate_config(analysis)

    assert result.exit_code == 0, result.output
    assert results['rel_abundance_file'] == 'barcode01_filtered.fastq_rel-abundance.tsv'
    assert results['read_assignment_file'] == 'barcode01_filtered.fastq_read-assignment-distributions.tsv'


@pytest.mark.parametrize('files, message', [
    (['barcode01_filtered.fastq_rel-abundance.tsv', 'barcode01_downsampled.fastq_rel-abundance.tsv'], 'Several'),
    (['barcode010_filtered.fastq_rel-abundance.tsv'], 'No rel-abundance.tsv file for barcode01'),
])
def test_generate_config_does_not_guess_the_rel_abundance_file(analysis, files, message):
    for name in files:
        write(analysis, name)

    result, results = generate_config(analysis)

    assert result.exit_code != 0
    assert message in result.output
    assert results is None


@pytest.mark.parametrize('files, error', [
    (['barcode01_filtered.fastq_rel-abundance.tsv', 'barcode01_downsampled.fastq_rel-abundance.tsv'], ValueError),
    ([], FileNotFoundError),
])
def test_upload_fails_without_exactly_one_rel_abundance_file(analysis, files, error):
    for name in files:
        write(analysis, name)
    with pytest.raises(error):
        parse(sample_config(analysis, 'barcode01*.fastq_rel-abundance.tsv'))


def test_unreadable_read_assignment_file_only_skips_probabilities(analysis, capsys):
    write(analysis, 'barcode01_filtered.fastq_rel-abundance.tsv')
    write(analysis, 'barcode01_filtered.fastq_read-assignment-distributions.tsv', '')

    sample_data = parse(sample_config(analysis, 'barcode01_filtered.fastq_rel-abundance.tsv',
                                      'barcode01_filtered.fastq_read-assignment-distributions.tsv'))

    assert [(taxa.species, taxa.median_probability) for taxa in sample_data.taxonomic_abundances] == [('Escherichia coli', None)]
    assert 'Skipped read assignment probabilities' in capsys.readouterr().out


def test_sample_without_results_sends_no_taxonomic_data(analysis):
    config = sample_config(analysis, 'unused.tsv')
    config.results = None
    assert FormatHandler().convert_to_eyrie_format(parse(config), config)['taxonomic_data'] is None
