"""Async sample database operations."""

from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional
from .utils import get_db_connection


async def get_all_samples() -> List[Dict[str, Any]]:
    """Get all samples."""
    async with get_db_connection() as db:
        cursor = db.samples.find()
        return await cursor.to_list(length=None)


async def find_sample(sample_id: str) -> Optional[Dict[str, Any]]:
    """Find sample by sample_id."""
    async with get_db_connection() as db:
        return await db.samples.find_one({'sample_id': sample_id})


async def create_sample(sample_data: Dict[str, Any]) -> str:
    """Create a new sample."""
    async with get_db_connection() as db:
        # Check if sample already exists
        existing = await db.samples.find_one({'sample_id': sample_data['sample_id']})
        if existing:
            raise ValueError(f"Sample with ID '{sample_data['sample_id']}' already exists")

        # Add timestamps
        sample_data['created_date'] = datetime.now()
        sample_data['updated_date'] = datetime.now()

        result = await db.samples.insert_one(sample_data)
        return str(result.inserted_id)


async def update_sample(sample_id: str, update_data: Dict[str, Any]) -> bool:
    """Update an existing sample."""
    async with get_db_connection() as db:
        # Remove None values from update data
        filtered_data = {k: v for k, v in update_data.items() if v is not None}

        if not filtered_data:
            return False

        # Add updated timestamp
        filtered_data['updated_date'] = datetime.now()

        result = await db.samples.update_one(
            {'sample_id': sample_id},
            {'$set': filtered_data}
        )
        return result.matched_count > 0


async def upsert_sample(sample_data: Dict[str, Any]) -> Tuple[str, bool]:
    """Create sample if it doesn't exist, update if it does. Returns (id, was_created)."""
    async with get_db_connection() as db:
        existing = await db.samples.find_one({'sample_id': sample_data['sample_id']})

        if existing:
            # Update existing sample
            update_data = {k: v for k, v in sample_data.items() if k != 'sample_id'}
            update_data['updated_date'] = datetime.now()

            await db.samples.update_one(
                {'sample_id': sample_data['sample_id']},
                {'$set': update_data}
            )
            return str(existing['_id']), False
        else:
            # Create new sample
            sample_data['created_date'] = datetime.now()
            sample_data['updated_date'] = datetime.now()
            result = await db.samples.insert_one(sample_data)
            return str(result.inserted_id), True


async def update_sample_qc(sample_id: str, qc_status: str, comments: str) -> bool:
    """Update sample QC status and comments."""
    async with get_db_connection() as db:
        result = await db.samples.update_one(
            {'sample_id': sample_id},
            {
                '$set': {
                    'qc': qc_status,
                    'comments': comments,
                    'updated_date': datetime.now()
                }
            }
        )
        return result.matched_count > 0


async def update_sample_comment(sample_id: str, comments: str) -> bool:
    """Update sample comments only."""
    async with get_db_connection() as db:
        result = await db.samples.update_one(
            {'sample_id': sample_id},
            {
                '$set': {
                    'comments': comments,
                    'updated_date': datetime.now()
                }
            }
        )
        return result.matched_count > 0


async def update_sample_species_flags(
    sample_id: str,
    flagged_contaminants: Optional[List] = None,
    flagged_top_hits: Optional[List] = None
) -> bool:
    """Update sample species flags (contaminants and/or top hits)."""
    async with get_db_connection() as db:
        update_data = {'updated_date': datetime.now()}

        if flagged_contaminants is not None:
            update_data['flagged_contaminants'] = flagged_contaminants

        if flagged_top_hits is not None:
            update_data['flagged_top_hits'] = flagged_top_hits

        result = await db.samples.update_one(
            {'sample_id': sample_id},
            {'$set': update_data}
        )
        return result.matched_count > 0