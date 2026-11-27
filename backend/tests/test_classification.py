import pytest
from pydantic import ValidationError

from eyrie_api.models.settings import SpikeSettings
from eyrie_api.utils.classification import classify_sample, detected_spike

SPIKE = 'Salinibacter ruber'
SETTINGS = {'species': [SPIKE], 'normaliser': SPIKE}


def sample(sample_id, hits):
    return {'sample_id': sample_id, 'sample_name': sample_id.upper(), 'taxonomic_data': {'hits': [
        {'species': species, 'relative_abundance': abundance} for species, abundance in hits
    ]}}


def flags(result, species):
    return next(hit for hit in result['hits'] if hit['species'] == species)


def test_only_analysed_controls_other_than_the_sample_are_compared():
    clinical = sample('s1', [('Escherichia coli', 0.7)])
    without_results = {'sample_id': 'nc1', 'sample_name': 'NC1'}
    without_species = sample('nc2', [])

    result = classify_sample(clinical, [clinical, without_results, without_species], SETTINGS)

    assert result['negative_controls'] == ['NC2']
    assert result['excluded_controls'] == ['NC1']
    assert flags(result, 'Escherichia coli')['absent_in_controls']


@pytest.mark.parametrize('spike_abundance, enriched', [(0.1, True), (0, False), (float('nan'), False)])
def test_enrichment_needs_a_positive_spike_in_the_sample(spike_abundance, enriched):
    historical_control = {'sample_id': 'nc1', 'taxonomic_data': {'hits': [
        {'species': 'Escherichia coli', 'abundance': 0.1}, {'species': SPIKE, 'abundance': 10.0},
    ]}}
    result = classify_sample(
        sample('s1', [('Escherichia coli', 0.5), (SPIKE, spike_abundance)]), [historical_control], SETTINGS
    )
    assert flags(result, 'Escherichia coli')['enriched'] is enriched
    assert flags(result, 'Escherichia coli')['enrichment_unchecked_against'] == ([] if enriched else ['nc1'])


def test_a_control_without_the_spike_is_reported_as_unchecked():
    with_spike = sample('nc1', [('Escherichia coli', 0.001), (SPIKE, 0.1)])
    without_spike = sample('nc2', [('Escherichia coli', 0.001)])
    result = classify_sample(sample('s1', [('Escherichia coli', 0.5), (SPIKE, 0.1)]), [with_spike, without_spike], SETTINGS)

    assert not flags(result, 'Escherichia coli')['enriched']
    assert flags(result, 'Escherichia coli')['enrichment_unchecked_against'] == ['NC2']
    assert result['controls_without_normaliser'] == ['NC2']


def test_detected_spike_is_the_most_abundant_ignoring_case_and_order():
    hits = sample('s1', [('Agrobacterium fabrum', 0.01), ('salinibacter ruber', 0.2)])
    assert detected_spike(hits, ['Agrobacterium fabrum', SPIKE]) == 'salinibacter ruber'


def test_spike_settings_are_validated_ignoring_case():
    assert SpikeSettings(species=[f' {SPIKE} '], normaliser=SPIKE.lower()).normaliser == SPIKE
    for species, normaliser in (([SPIKE, SPIKE.upper()], None), ([SPIKE, ' '], None), ([SPIKE], 'Imtechella halotolerans')):
        with pytest.raises(ValidationError):
            SpikeSettings(species=species, normaliser=normaliser)
