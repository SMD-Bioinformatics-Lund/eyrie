"""Async sequencing run database operations."""

from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from .utils import get_db_connection


async def find_seqrun(sequencing_run_id: str) -> Optional[Dict[str, Any]]:
    """Find sequencing run by sequencing_run_id."""
    async with get_db_connection() as db:
        return await db.seqruns.find_one({'sequencing_run_id': sequencing_run_id})


async def get_all_seqruns() -> list[Dict[str, Any]]:
    """Get all sequencing runs from the database."""
    async with get_db_connection() as db:
        cursor = db.seqruns.find({})
        return await cursor.to_list(length=None)


async def create_seqrun(seqrun_data: Dict[str, Any]) -> str:
    """Create a new sequencing run."""
    async with get_db_connection() as db:
        existing = await db.seqruns.find_one({'sequencing_run_id': seqrun_data['sequencing_run_id']})
        if existing:
            raise ValueError(f"Sequencing run with ID '{seqrun_data['sequencing_run_id']}' already exists")

        seqrun_data['created_date'] = datetime.now()
        seqrun_data['updated_date'] = datetime.now()

        result = await db.seqruns.insert_one(seqrun_data)
        return str(result.inserted_id)


async def update_seqrun(sequencing_run_id: str, update_data: Dict[str, Any]) -> bool:
    """Update an existing sequencing run."""
    async with get_db_connection() as db:
        # Filter out None values but preserve nested structures like sequencing_metadata
        filtered_data = {}
        for k, v in update_data.items():
            if k == 'sequencing_metadata':
                # Always include sequencing_metadata, even if it has None fields
                filtered_data[k] = v
            elif v is not None:
                filtered_data[k] = v

        if not filtered_data:
            return False

        filtered_data['updated_date'] = datetime.now()

        result = await db.seqruns.update_one(
            {'sequencing_run_id': sequencing_run_id},
            {'$set': filtered_data}
        )
        return result.matched_count > 0


async def upsert_seqrun(seqrun_data: Dict[str, Any]) -> Tuple[str, bool]:
    """Create sequencing run if it doesn't exist, update if it does. Returns (id, was_created)."""
    async with get_db_connection() as db:
        existing = await db.seqruns.find_one({'sequencing_run_id': seqrun_data['sequencing_run_id']})

        if existing:
            # Prepare update data, excluding the sequencing_run_id (used as key)
            raw_update_data = {k: v for k, v in seqrun_data.items() if k != 'sequencing_run_id'}

            # Filter out None values but preserve nested structures like sequencing_metadata
            update_data = {}
            for k, v in raw_update_data.items():
                if k == 'sequencing_metadata':
                    # Always include sequencing_metadata, even if it has None fields
                    update_data[k] = v
                elif v is not None:
                    update_data[k] = v

            update_data['updated_date'] = datetime.now()

            await db.seqruns.update_one(
                {'sequencing_run_id': seqrun_data['sequencing_run_id']},
                {'$set': update_data}
            )
            return str(existing['_id']), False
        else:
            seqrun_data['created_date'] = datetime.now()
            seqrun_data['updated_date'] = datetime.now()
            result = await db.seqruns.insert_one(seqrun_data)
            return str(result.inserted_id), True



async def get_pipeline_file_path(sequencing_run_id: str, file_type: str) -> Optional[str]:
    """Get specific pipeline file path for a sequencing run."""
    async with get_db_connection() as db:
        seqrun = await db.seqruns.find_one(
            {'sequencing_run_id': sequencing_run_id},
            {'pipeline_software': 1, 'pipeline_files': 1, '_id': 0}
        )

        if not seqrun:
            return None

        pipeline_software = seqrun.get('pipeline_software')
        if not pipeline_software:
            return None

        pipeline_files = seqrun.get('pipeline_files', {})
        if not pipeline_files:
            return None

        relative_path = pipeline_files.get(file_type)
        if not relative_path:
            return None

        base_path = f"/app/analysis-files/results/{pipeline_software}"
        return f"{base_path}/{relative_path}"

async def check_seqrun_exists(sequencing_run_id: str) -> bool:
    """Check if a sequencing run already exists in the database."""
    async with get_db_connection() as db:
        seqrun = await db.seqruns.find_one(
            {'sequencing_run_id': sequencing_run_id},
            {'_id': 1}
        )
        return seqrun is not None
