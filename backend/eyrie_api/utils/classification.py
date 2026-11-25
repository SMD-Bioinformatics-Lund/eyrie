"""Negative control comparison for a sample's taxonomic hits, using emuse."""

from typing import Any, Dict, List, Optional

import pandas as pd
from emuse.negative_control import compare_to_negative_controls


def abundance_table(sample: Dict[str, Any]) -> pd.DataFrame:
    hits = (sample.get('taxonomic_data') or {}).get('hits', [])
    rows = [
        {
            'species': hit.get('species'),
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
    return next((hit.get('species') for hit in hits if hit.get('species') in spike_species), None)


def classify_sample(sample: Dict[str, Any], negative_controls: List[Dict[str, Any]], spike_settings: Dict[str, Any]) -> Dict[str, Any]:
    controls = {
        control.get('sample_name') or control['sample_id']: abundance_table(control)
        for control in negative_controls
        if control['sample_id'] != sample['sample_id']
    }
    hits = (sample.get('taxonomic_data') or {}).get('hits', [])
    flags = compare_to_negative_controls(
        abundance_table(sample), list(controls.values()), spike_settings['species'], spike_settings['normaliser']
    ).to_dict(orient='records')

    classified_hits = [
        {**hit, **{name: bool(value) for name, value in flag.items()}, 'highlight': highlight(flag)}
        for hit, flag in zip(hits, flags)
    ]

    return {
        'sample_id': sample['sample_id'],
        'hits': classified_hits,
        'spike': detected_spike(sample, spike_settings['species']),
        'negative_controls': list(controls),
        'spike_settings': spike_settings,
        'classification_qc': sample.get('classification_qc'),
    }
