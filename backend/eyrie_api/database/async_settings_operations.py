"""Async settings database operations."""

import re
from datetime import datetime
from typing import Any, Dict, List, Optional
from .utils import get_db_connection

DEFAULT_SPIKE_SPECIES = ["Agrobacterium tumefaciens", "Agrobacterium fabrum", "Salinibacter ruber"]
SPIKE_SETTINGS_ID = 'spike_species'


def lowercase(names: List[str]) -> List[str]:
    return [name.strip().lower() for name in names if name.strip()]


def ignoring_case(name: str):
    return re.compile(f'^{re.escape(name.strip())}$', re.IGNORECASE)


async def get_spike_settings() -> Dict[str, Any]:
    """Get spike species settings, falling back to the defaults."""
    async with get_db_connection() as db:
        settings = await db.settings.find_one({'_id': SPIKE_SETTINGS_ID})
    if not settings:
        return {'species': list(DEFAULT_SPIKE_SPECIES), 'normaliser': None}
    return {'species': settings.get('species', []), 'normaliser': settings.get('normaliser')}


async def update_spike_settings(species: List[str], normaliser: Optional[str]) -> None:
    async with get_db_connection() as db:
        await db.settings.update_one(
            {'_id': SPIKE_SETTINGS_ID},
            {'$set': {'species': species, 'normaliser': normaliser, 'updated_date': datetime.now()}},
            upsert=True
        )


async def _ensure_spike_settings(db) -> None:
    await db.settings.update_one(
        {'_id': SPIKE_SETTINGS_ID},
        {'$setOnInsert': {'species': list(DEFAULT_SPIKE_SPECIES), 'normaliser': None}},
        upsert=True
    )


async def add_spike_species(species: str) -> bool:
    """Add a spike species unless it is already listed, ignoring case. Returns whether it was added."""
    async with get_db_connection() as db:
        await _ensure_spike_settings(db)
        result = await db.settings.update_one(
            {'_id': SPIKE_SETTINGS_ID, 'species': {'$not': ignoring_case(species)}},
            {'$push': {'species': species}, '$set': {'updated_date': datetime.now()}}
        )
    return result.modified_count == 1


async def remove_spike_species(species: List[str]) -> None:
    """Remove spike species, ignoring case, clearing the normaliser if it is one of them."""
    removed = lowercase(species)
    async with get_db_connection() as db:
        await _ensure_spike_settings(db)
        await db.settings.update_one({'_id': SPIKE_SETTINGS_ID}, [{'$set': {
            'species': {'$filter': {'input': '$species', 'cond': {'$not': [{'$in': [{'$toLower': '$$this'}, removed]}]}}},
            'normaliser': {'$cond': [{'$in': [{'$toLower': '$normaliser'}, removed]}, None, '$normaliser']},
            'updated_date': datetime.now(),
        }}])


async def set_spike_normaliser(normaliser: Optional[str]) -> bool:
    """Set the normalising species, which must be a spike species, ignoring case. Returns whether it was set."""
    async with get_db_connection() as db:
        await _ensure_spike_settings(db)
        if not normaliser:
            result = await db.settings.update_one(
                {'_id': SPIKE_SETTINGS_ID}, {'$set': {'normaliser': None, 'updated_date': datetime.now()}}
            )
            return result.matched_count == 1
        spelling = {'$arrayElemAt': [{'$filter': {
            'input': '$species', 'cond': {'$eq': [{'$toLower': '$$this'}, normaliser.strip().lower()]}
        }}, 0]}
        result = await db.settings.update_one(
            {'_id': SPIKE_SETTINGS_ID, 'species': ignoring_case(normaliser)},
            [{'$set': {'normaliser': spelling, 'updated_date': datetime.now()}}]
        )
    return result.matched_count == 1
