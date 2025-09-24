from fastapi import APIRouter, HTTPException, Request
from ..models.auth import UserCreate, UserUpdate
from ..database.user_operations import get_all_users, create_user, update_user, delete_user, user_exists
from ..auth.middleware import get_admin_user
from ..utils.json_encoder import JSONEncoder
import json

router = APIRouter(prefix="/api/admin", tags=["admin"])

@router.get("/users")
async def get_users(request: Request):
    get_admin_user(request)  # Verify admin access
    try:
        users = get_all_users()
        return json.loads(JSONEncoder().encode(users))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/users")
async def create_new_user(user_data: UserCreate, request: Request):
    get_admin_user(request)  # Verify admin access
    try:
        # Validate input
        if not user_data.username or not user_data.email or not user_data.password:
            raise HTTPException(status_code=400, detail="Username, email, and password are required")

        if user_data.role not in ['user', 'admin', 'uploader']:
            raise HTTPException(status_code=400, detail="Invalid role")

        # Check if user already exists
        if user_exists(username=user_data.username):
            raise HTTPException(status_code=400, detail="Username already exists")

        if user_exists(email=user_data.email):
            raise HTTPException(status_code=400, detail="Email already exists")

        # Create user
        user = create_user(user_data)
        return {'success': True, 'user': user}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/users/{user_id}")
async def update_existing_user(user_id: str, user_data: UserUpdate, request: Request):
    get_admin_user(request)  # Verify admin access
    try:
        update_data = {}
        if user_data.email is not None:
            update_data['email'] = user_data.email
        if user_data.role is not None:
            if user_data.role not in ['user', 'admin', 'uploader']:
                raise HTTPException(status_code=400, detail="Invalid role")
            update_data['role'] = user_data.role
        if user_data.is_active is not None:
            update_data['is_active'] = user_data.is_active
        if user_data.password:
            update_data['password'] = user_data.password

        success = update_user(user_id, update_data)
        if not success:
            raise HTTPException(status_code=404, detail="User not found")

        return {'success': True}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/users/{user_id}")
async def delete_existing_user(user_id: str, request: Request):
    admin_user = get_admin_user(request)  # Verify admin access
    try:
        # Prevent deleting the current user
        if str(admin_user['_id']) == user_id:
            raise HTTPException(status_code=400, detail="Cannot delete your own account")

        success = delete_user(user_id)
        if not success:
            raise HTTPException(status_code=404, detail="User not found")

        return {'success': True}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
