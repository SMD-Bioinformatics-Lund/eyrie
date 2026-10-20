"""Async settings database operations."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from .utils import get_db_connection

DEFAULT_SPIKE_SPECIES = ["Agrobacterium tumefaciens", "Agrobacterium fabrum", "Salinibacter ruber"]


async def get_spike_settings() -> Dict[str, Any]:
    """Get spike species settings, falling back to the defaults."""
    async with get_db_connection() as db:
        settings = await db.settings.find_one({'_id': 'spike_species'})
    if not settings:
        return {'species': list(DEFAULT_SPIKE_SPECIES), 'normaliser': None}
    return {'species': settings.get('species', []), 'normaliser': settings.get('normaliser')}


async def update_spike_settings(species: List[str], normaliser: Optional[str]) -> None:
    """Replace spike species settings."""
    async with get_db_connection() as db:
        await db.settings.update_one(
            {'_id': 'spike_species'},
            {'$set': {'species': species, 'normaliser': normaliser, 'updated_date': datetime.now()}},
            upsert=True
        )
