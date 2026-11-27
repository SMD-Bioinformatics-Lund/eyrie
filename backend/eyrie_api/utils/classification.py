"""Negative control comparison for a sample's taxonomic hits, using emuse."""

import math
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
from emuse.negative_control import compare_to_negative_controls

ENRICHMENT_FOLD = 25
LOW_ABUNDANCE_CUTOFF = 0.005


def species_key(species: Optional[str]) -> str:
    return (species or '').strip().casefold()


def sample_hits(sample: Dict[str, Any]) -> List[Dict[str, Any]]:
    return (sample.get('taxonomic_data') or {}).get('hits') or []


def has_analysis(sample: Dict[str, Any]) -> bool:
    return 'hits' in (sample.get('taxonomic_data') or {})


def relative_abundance(hit: Dict[str, Any]) -> float:
    value = hit.get('relative_abundance')
    if value is None:
        value = (hit.get('abundance') or 0) / 100
    return value


def abundance_table(sample: Dict[str, Any], spellings: Dict[str, str]) -> pd.DataFrame:
    """Hits as an emuse abundance table, with spike species spelled as in the settings."""
    rows = [
        {
            'species': spellings.get(species_key(hit.get('species')), hit.get('species')),
            'abundance': relative_abundance(hit),
        }
        for hit in sample_hits(sample)
    ]
    return pd.DataFrame(rows, columns=['species', 'abundance'])


def usable_normaliser(table: pd.DataFrame, normaliser: Optional[str]) -> Optional[str]:
    """The normaliser, unless the sample lacks a positive abundance of it to divide by."""
    abundances = table.loc[table['species'] == normaliser, 'abundance']
    if abundances.empty:
        return None
    abundance = abundances.iloc[0]
    return normaliser if math.isfinite(abundance) and abundance > 0 else None


def highlight(flags: Dict[str, bool]) -> Optional[str]:
    if flags['spike']:
        return 'spike'
    if flags['absent_in_controls'] or flags['enriched']:
        return 'not_in_control'
    return None


def detected_spike(sample: Dict[str, Any], spike_species: List[str]) -> Optional[str]:
    spikes = {species_key(species) for species in spike_species}
    found = [hit for hit in sample_hits(sample) if species_key(hit.get('species')) in spikes]
    return max(found, key=relative_abundance).get('species') if found else None


def comparison_controls(sample: Dict[str, Any], negative_controls: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Controls to compare the sample with, and those left out because they have no analysis results."""
    others = [control for control in negative_controls if control['sample_id'] != sample['sample_id']]
    return [c for c in others if has_analysis(c)], [c for c in others if not has_analysis(c)]


def control_name(control: Dict[str, Any]) -> str:
    return control.get('sample_name') or control['sample_id']


def unnormalisable_controls(controls: List[Dict[str, Any]], tables: List[pd.DataFrame], configured: Optional[str], normaliser: Optional[str]) -> List[Tuple[str, set]]:
    """Controls that enrichment cannot be checked against, as names with the species they contain.

    Without a usable normaliser in the sample, that is every control. emuse treats such a control
    as not showing enrichment, so it keeps any species it contains from being flagged as enriched.
    """
    if not configured:
        return []
    return [
        (control_name(control), set(table['species']))
        for control, table in zip(controls, tables)
        if not (normaliser and usable_normaliser(table, normaliser))
    ]


def classify_sample(sample: Dict[str, Any], negative_controls: List[Dict[str, Any]], spike_settings: Dict[str, Any]) -> Dict[str, Any]:
    spellings = {species_key(species): species for species in spike_settings['species']}
    controls, excluded = comparison_controls(sample, negative_controls)
    sample_table = abundance_table(sample, spellings)
    normaliser = usable_normaliser(sample_table, spike_settings['normaliser'])
    control_tables = [abundance_table(control, spellings) for control in controls]
    unchecked = unnormalisable_controls(controls, control_tables, spike_settings['normaliser'], normaliser)
    thresholds = {
        'enrichment_fold': spike_settings.get('enrichment_fold', ENRICHMENT_FOLD),
        'low_abundance_cutoff': spike_settings.get('low_abundance_cutoff', LOW_ABUNDANCE_CUTOFF),
    }
    flags = compare_to_negative_controls(
        sample_table,
        control_tables,
        spike_settings['species'],
        normaliser,
        fold=thresholds['enrichment_fold'],
        low_abundance_cutoff=thresholds['low_abundance_cutoff'],
    ).to_dict(orient='records')

    classified_hits = [
        {
            **hit,
            **{name: bool(value) for name, value in flag.items()},
            'highlight': highlight(flag),
            'enrichment_unchecked_against': [name for name, species in unchecked if table_species in species],
        }
        for hit, table_species, flag in zip(sample_hits(sample), sample_table['species'], flags)
    ]

    return {
        'sample_id': sample['sample_id'],
        'hits': classified_hits,
        'spike': detected_spike(sample, spike_settings['species']),
        'negative_controls': [control_name(control) for control in controls],
        'excluded_controls': [control_name(control) for control in excluded],
        'controls_without_normaliser': [name for name, _ in unchecked] if normaliser else [],
        'normaliser': normaliser,
        'spike_settings': spike_settings,
        'thresholds': thresholds,
        'classification_qc': sample.get('classification_qc'),
    }
