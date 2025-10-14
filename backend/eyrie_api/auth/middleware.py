from fastapi import HTTPException, Request

# For now, create a simple placeholder that always allows admin access
# This is for getting the backend working - should be properly implemented later
def get_admin_user(request: Request):
    """Placeholder admin authentication - allows all requests"""
    # In a real implementation, this would verify session/token authentication
    # For now, return a mock admin user to get the system working
    return {
        '_id': 'admin_id',
        'username': 'admin',
        'role': 'admin'
    }

def get_current_user(request: Request):
    """Placeholder user authentication - allows all requests"""
    # In a real implementation, this would verify session/token authentication
    return {
        '_id': 'admin_id',
        'username': 'admin',
        'role': 'admin'
    }