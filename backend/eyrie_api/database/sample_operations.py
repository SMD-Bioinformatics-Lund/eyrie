from datetime import datetime
from .connection import db

def get_all_samples():
    """Get all samples"""
    return list(db.samples.find())

def find_sample(sample_id):
    """Find sample by sample_id"""
    return db.samples.find_one({'sample_id': sample_id})

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
