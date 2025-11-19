from fastapi import HTTPException, Request

def get_admin_user(request: Request):
    """Placeholder admin authentication - allows all requests"""
    return {
        '_id': 'admin_id',
        'username': 'admin',
        'role': 'admin'
    }

def get_current_user(request: Request):
    """Placeholder user authentication - allows all requests"""
    return {
        '_id': 'admin_id',
        'username': 'admin',
        'role': 'admin'
    }
