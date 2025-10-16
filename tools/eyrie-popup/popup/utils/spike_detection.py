"""Spike species detection utilities."""

from typing import List, Optional
from ..config import SPIKE


def is_spike(species_name: str) -> bool:
    """
    Check if a species name matches any of the configured spike species.
    
    Args:
        species_name: The species name to check
        
    Returns:
        True if the species is a spike species, False otherwise
    """
    if not species_name:
        return False

    # Normalize the species name for comparison (case-insensitive)
    normalized_name = species_name.lower().strip()

    # Check for exact matches
    for spike in SPIKE:
        if normalized_name == spike.lower():
            return True

    return False


def get_detected_spike(taxonomic_data: List) -> Optional[str]:
    """
    Find the first spike species detected in taxonomic data.
    
    Args:
        taxonomic_data: List of taxonomic abundance data
        
    Returns:
        The name of the detected spike species, or None if no spike found
    """
    if not taxonomic_data:
        return None

    # Sort by abundance (highest first) to prioritize the most abundant spike
    sorted_data = sorted(taxonomic_data, key=lambda x: getattr(x, 'abundance', 0), reverse=True)

    for organism in sorted_data:
        species_name = getattr(organism, 'species', '')
        if is_spike(species_name):
            return species_name

    return None
