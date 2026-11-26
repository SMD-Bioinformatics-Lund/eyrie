import pytest
from pydantic import ValidationError

from eyrie_api.models.settings import SpikeSettings
from eyrie_api.utils.classification import classify_sample, detected_spike

SPIKE = 'Salinibacter ruber'
SETTINGS = {'species': [SPIKE], 'normaliser': SPIKE}


def sample(sample_id, hits):
    return {'sample_id': sample_id, 'taxonomic_data': {'hits': [
        {'species': species, 'relative_abundance': abundance} for species, abundance in hits
    ]}}


def flags(result):
    return {hit['species']: hit for hit in result['hits']}


def test_control_without_results_is_excluded_not_treated_as_empty():
    result = classify_sample(
        sample('s1', [('Escherichia coli', 0.7), (SPIKE, 0.1)]),
        [{'sample_id': 'nc1', 'sample_name': 'NC1'}],
        SETTINGS,
    )
    assert result['negative_controls'] == []
    assert result['excluded_controls'] == ['NC1']
    assert not flags(result)['Escherichia coli']['absent_in_controls']


def test_control_with_no_hits_is_compared():
    result = classify_sample(sample('s1', [('Escherichia coli', 0.7)]), [sample('nc1', [])], SETTINGS)
    assert result['negative_controls'] == ['nc1']
    assert flags(result)['Escherichia coli']['absent_in_controls']


def test_negative_control_is_not_compared_with_itself():
    control = sample('nc1', [('Escherichia coli', 0.7)])
    result = classify_sample(control, [control], SETTINGS)
    assert result['negative_controls'] == []
    assert not flags(result)['Escherichia coli']['absent_in_controls']


def test_enriched_against_control_normalised_to_spike():
    result = classify_sample(
        sample('s1', [('Escherichia coli', 0.5), (SPIKE, 0.1)]),
        [sample('nc1', [('Escherichia coli', 0.001), (SPIKE, 0.1)])],
        SETTINGS,
    )
    assert flags(result)['Escherichia coli']['enriched']
    assert flags(result)['Escherichia coli']['highlight'] == 'not_in_control'


@pytest.mark.parametrize('spike_abundance', [0, float('nan')])
def test_sample_spike_without_abundance_never_gives_enrichment(spike_abundance):
    result = classify_sample(
        sample('s1', [('Escherichia coli', 0.02), (SPIKE, spike_abundance)]),
        [sample('nc1', [('Escherichia coli', 0.001), (SPIKE, 0.1)])],
        SETTINGS,
    )
    assert result['normaliser'] is None
    assert not flags(result)['Escherichia coli']['enriched']


def test_historical_hits_fall_back_to_rounded_percentage():
    hits = [{'species': 'Escherichia coli', 'abundance': 70.0, 'relative_abundance': None},
            {'species': SPIKE, 'abundance': 10.0}]
    result = classify_sample({'sample_id': 's1', 'taxonomic_data': {'hits': hits}},
                             [sample('nc1', [('Escherichia coli', 0.001), (SPIKE, 0.1)])], SETTINGS)
    assert result['normaliser'] == SPIKE
    assert flags(result)['Escherichia coli']['enriched']


def test_detected_spike_is_the_most_abundant_regardless_of_order():
    hits = sample('s1', [('Agrobacterium fabrum', 0.01), ('salinibacter ruber', 0.2)])
    assert detected_spike(hits, ['Agrobacterium fabrum', SPIKE]) == 'salinibacter ruber'


def test_spike_settings_reject_duplicates_ignoring_case():
    with pytest.raises(ValidationError):
        SpikeSettings(species=[SPIKE, SPIKE.upper()], normaliser=SPIKE)


def test_spike_settings_reject_blank_species():
    with pytest.raises(ValidationError):
        SpikeSettings(species=[SPIKE, '  '])


def test_spike_settings_normaliser_uses_species_spelling():
    assert SpikeSettings(species=[f' {SPIKE} '], normaliser=SPIKE.lower()).normaliser == SPIKE


def test_spike_settings_normaliser_must_be_a_spike():
    with pytest.raises(ValidationError):
        SpikeSettings(species=[SPIKE], normaliser='Imtechella halotolerans')
