"""Async settings database operations."""

import re
from datetime import datetime
from importlib.metadata import PackageNotFoundError, version
from typing import Any, Dict, Iterable, List, Optional

from pymongo import UpdateOne

from ..utils.classification import ENRICHMENT_FOLD, LOW_ABUNDANCE_CUTOFF
from .utils import get_db_connection

DEFAULT_SPIKE_SPECIES = ["Agrobacterium tumefaciens", "Agrobacterium fabrum", "Salinibacter ruber"]
SPIKE_SETTINGS_ID = 'spike_species'
FROZEN_FIELDS = ('species', 'normaliser', 'enrichment_fold', 'low_abundance_cutoff', 'emuse_version')


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
    await freeze_all_runs()
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
    await freeze_all_runs()
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
    await freeze_all_runs()
    async with get_db_connection() as db:
        await _ensure_spike_settings(db)
        await db.settings.update_one({'_id': SPIKE_SETTINGS_ID}, [{'$set': {
            'species': {'$filter': {'input': '$species', 'cond': {'$not': [{'$in': [{'$toLower': '$$this'}, removed]}]}}},
            'normaliser': {'$cond': [{'$in': [{'$toLower': '$normaliser'}, removed]}, None, '$normaliser']},
            'updated_date': datetime.now(),
        }}])


async def set_spike_normaliser(normaliser: Optional[str]) -> bool:
    """Set the normalising species, which must be a spike species, ignoring case. Returns whether it was set."""
    await freeze_all_runs()
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


def emuse_version() -> Optional[str]:
    try:
        return version('emuse')
    except PackageNotFoundError:
        return None


async def current_run_settings() -> Dict[str, Any]:
    """The settings a new sequencing run is frozen with."""
    return {
        **await get_spike_settings(),
        'enrichment_fold': ENRICHMENT_FOLD,
        'low_abundance_cutoff': LOW_ABUNDANCE_CUTOFF,
        'emuse_version': emuse_version(),
    }


async def freeze_run_settings(run_ids: Iterable[Optional[str]]) -> None:
    """Store the current settings for runs that have none yet. Settings already stored are never changed."""
    run_ids = sorted({run_id for run_id in run_ids if run_id})
    if not run_ids:
        return
    frozen = {**await current_run_settings(), 'frozen_date': datetime.now()}
    async with get_db_connection() as db:
        await db.run_classification_settings.bulk_write(
            [UpdateOne({'_id': run_id}, {'$setOnInsert': frozen}, upsert=True) for run_id in run_ids], ordered=False
        )


async def freeze_all_runs() -> None:
    """Freeze the settings of every run before the defaults change, so no run picks up the change."""
    async with get_db_connection() as db:
        run_ids = await db.samples.distinct('sequencing_run_id')
    await freeze_run_settings(run_ids)


async def get_run_settings(run_ids: Iterable[Optional[str]]) -> Dict[str, Dict[str, Any]]:
    """Settings of each run, freezing the current ones for runs that have none yet."""
    run_ids = {run_id for run_id in run_ids if run_id}

    async def load(ids):
        async with get_db_connection() as db:
            docs = await db.run_classification_settings.find({'_id': {'$in': list(ids)}}).to_list(length=None)
        return {doc['_id']: doc for doc in docs}

    settings = await load(run_ids) if run_ids else {}
    missing = run_ids - settings.keys()
    if missing:
        await freeze_run_settings(missing)
        settings.update(await load(missing))
    return settings


async def settings_for_run(run_id: Optional[str]) -> Dict[str, Any]:
    if not run_id:
        return await current_run_settings()
    return (await get_run_settings([run_id]))[run_id]


async def apply_current_settings_to_run(run_id: str, username: str) -> bool:
    """Replace a run's settings with the current ones, recording who did it, when and what was replaced."""
    async with get_db_connection() as db:
        if not await db.samples.find_one({'sequencing_run_id': run_id}, {'_id': 1}):
            return False
        previous = await db.run_classification_settings.find_one({'_id': run_id}) or {}
        now = datetime.now()
        await db.run_classification_settings.update_one({'_id': run_id}, {
            '$set': {**await current_run_settings(), 'applied_by': username, 'applied_date': now},
            '$setOnInsert': {'frozen_date': now},
            '$push': {'changes': {'by': username, 'date': now, 'previous': {k: previous.get(k) for k in FROZEN_FIELDS}}},
        }, upsert=True)
    return True
