"""Negative control comparison for a sample's taxonomic hits, using emuse."""

from typing import Any, Dict, List

from emuse.negative_control import compare_to_negative_controls


def abundance_rows(sample: Dict[str, Any]) -> List[Dict[str, Any]]:
    hits = (sample.get('taxonomic_data') or {}).get('hits', [])
    return [
        {
            'species': hit.get('species'),
            'abundance': hit.get('relative_abundance', hit.get('abundance', 0) / 100),
        }
        for hit in hits
    ]


def classify_sample(sample: Dict[str, Any], negative_controls: List[Dict[str, Any]], spike_settings: Dict[str, Any]) -> Dict[str, Any]:
    controls = {
        control.get('sample_name') or control['sample_id']: abundance_rows(control)
        for control in negative_controls
        if control['sample_id'] != sample['sample_id']
    }
    hits = (sample.get('taxonomic_data') or {}).get('hits', [])
    flags = compare_to_negative_controls(
        abundance_rows(sample), controls, spike_settings['species'], spike_settings['normaliser']
    )

    classified_hits = []
    for hit, flag in zip(hits, flags):
        flag_data = flag.to_dict()
        flag_data.pop('species')
        classified_hits.append({**hit, **flag_data})

    spike = next((hit['species'] for hit in classified_hits if hit['spike']), None)

    return {
        'sample_id': sample['sample_id'],
        'hits': classified_hits,
        'spike': spike,
        'negative_controls': list(controls),
        'spike_settings': spike_settings,
        'classification_qc': sample.get('classification_qc'),
    }
