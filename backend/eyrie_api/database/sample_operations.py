from datetime import datetime
from .connection import db
from typing import Dict, Any, Optional

def get_all_samples():
    """Get all samples"""
    return list(db.samples.find())

def find_sample(sample_id):
    """Find sample by sample_id"""
    return db.samples.find_one({'sample_id': sample_id})

def create_sample(sample_data: Dict[str, Any]) -> str:
    """Create a new sample"""
    # Check if sample already exists
    existing = db.samples.find_one({'sample_id': sample_data['sample_id']})
    if existing:
        raise ValueError(f"Sample with ID '{sample_data['sample_id']}' already exists")
    
    # Add timestamps
    sample_data['created_date'] = datetime.now()
    sample_data['updated_date'] = datetime.now()
    
    result = db.samples.insert_one(sample_data)
    return str(result.inserted_id)

def update_sample(sample_id: str, update_data: Dict[str, Any]) -> bool:
    """Update an existing sample"""
    # Remove None values from update data
    filtered_data = {k: v for k, v in update_data.items() if v is not None}
    
    if not filtered_data:
        return False
    
    # Add updated timestamp
    filtered_data['updated_date'] = datetime.now()
    
    result = db.samples.update_one(
        {'sample_id': sample_id},
        {'$set': filtered_data}
    )
    return result.matched_count > 0

def upsert_sample(sample_data: Dict[str, Any]) -> tuple[str, bool]:
    """Create sample if it doesn't exist, update if it does. Returns (id, was_created)"""
    existing = db.samples.find_one({'sample_id': sample_data['sample_id']})
    
    if existing:
        # Update existing sample
        update_data = {k: v for k, v in sample_data.items() if k != 'sample_id'}
        update_data['updated_date'] = datetime.now()
        
        db.samples.update_one(
            {'sample_id': sample_data['sample_id']},
            {'$set': update_data}
        )
        return str(existing['_id']), False
    else:
        # Create new sample
        sample_data['created_date'] = datetime.now()
        sample_data['updated_date'] = datetime.now()
        result = db.samples.insert_one(sample_data)
        return str(result.inserted_id), True

def update_sample_qc(sample_id, qc_status, comments):
    """Update sample QC status and comments"""
    result = db.samples.update_one(
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

def update_sample_comment(sample_id, comments):
    """Update sample comments only"""
    result = db.samples.update_one(
        {'sample_id': sample_id},
        {
            '$set': {
                'comments': comments,
                'updated_date': datetime.now()
            }
        }
    )
    return result.matched_count > 0

def update_sample_contamination_flags(sample_id, flagged_species):
    """Update sample contamination flags"""
    result = db.samples.update_one(
        {'sample_id': sample_id},
        {
            '$set': {
                'flagged_contaminants': flagged_species,
                'updated_date': datetime.now()
            }
        }
    )
    return result.matched_count > 0
