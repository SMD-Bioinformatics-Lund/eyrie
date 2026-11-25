"""Negative control comparison for a sample's taxonomic hits, using emuse."""

from typing import Any, Dict, List, Optional

import pandas as pd
from emuse.negative_control import compare_to_negative_controls

ENRICHMENT_FOLD = 25
LOW_ABUNDANCE_CUTOFF = 0.005


def species_key(species: Optional[str]) -> str:
    return (species or '').strip().casefold()


def abundance_table(sample: Dict[str, Any], spellings: Dict[str, str]) -> pd.DataFrame:
    """Hits as an emuse abundance table, with spike species spelled as in the settings."""
    hits = (sample.get('taxonomic_data') or {}).get('hits', [])
    rows = [
        {
            'species': spellings.get(species_key(hit.get('species')), hit.get('species')),
            'abundance': hit.get('relative_abundance', hit.get('abundance', 0) / 100),
        }
        for hit in hits
    ]
    return pd.DataFrame(rows, columns=['species', 'abundance'])


def highlight(flags: Dict[str, bool]) -> Optional[str]:
    if flags['spike']:
        return 'spike'
    if flags['absent_in_controls'] or flags['enriched']:
        return 'not_in_control'
    return None


def detected_spike(sample: Dict[str, Any], spike_species: List[str]) -> Optional[str]:
    hits = (sample.get('taxonomic_data') or {}).get('hits', [])
    spikes = {species_key(species) for species in spike_species}
    return next((hit.get('species') for hit in hits if species_key(hit.get('species')) in spikes), None)


def classify_sample(sample: Dict[str, Any], negative_controls: List[Dict[str, Any]], spike_settings: Dict[str, Any]) -> Dict[str, Any]:
    spellings = {species_key(species): species for species in spike_settings['species']}
    controls = [control for control in negative_controls if control['sample_id'] != sample['sample_id']]
    hits = (sample.get('taxonomic_data') or {}).get('hits', [])
    flags = compare_to_negative_controls(
        abundance_table(sample, spellings),
        [abundance_table(control, spellings) for control in controls],
        spike_settings['species'],
        spike_settings['normaliser'],
        fold=ENRICHMENT_FOLD,
        low_abundance_cutoff=LOW_ABUNDANCE_CUTOFF,
    ).to_dict(orient='records')

    classified_hits = [
        {**hit, **{name: bool(value) for name, value in flag.items()}, 'highlight': highlight(flag)}
        for hit, flag in zip(hits, flags)
    ]

    return {
        'sample_id': sample['sample_id'],
        'hits': classified_hits,
        'spike': detected_spike(sample, spike_settings['species']),
        'negative_controls': [control.get('sample_name') or control['sample_id'] for control in controls],
        'spike_settings': spike_settings,
        'thresholds': {'enrichment_fold': ENRICHMENT_FOLD, 'low_abundance_cutoff': LOW_ABUNDANCE_CUTOFF},
        'classification_qc': sample.get('classification_qc'),
    }
