from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime, timedelta
import jwt
import os
from typing import Optional
from bson import ObjectId

from ..models.auth import LoginRequest, UserCreate
from ..database.connection import db

router = APIRouter(prefix="/api/auth", tags=["authentication"])
security = HTTPBearer()

# JWT Secret - in production this should be a strong secret from environment
JWT_SECRET = os.getenv('JWT_SECRET', 'your-secret-key-change-in-production')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = 24

def create_jwt_token(user_data: dict) -> str:
    """Create JWT token for authenticated user"""
    payload = {
        'user_id': str(user_data['_id']),
        'username': user_data['username'],
        'role': user_data['role'],
        'exp': datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_jwt_token(token: str) -> dict:
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current authenticated user from JWT token"""
    payload = verify_jwt_token(credentials.credentials)

    # Get user from database
    user = db.users.find_one({'_id': ObjectId(payload['user_id'])})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    if not user.get('is_active', True):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is disabled"
        )

    return user

async def require_admin_or_uploader(current_user: dict = Depends(get_current_user)):
    """Require user to have admin or uploader role"""
    if current_user['role'] not in ['admin', 'uploader']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions. Admin or uploader role required."
        )
    return current_user

async def require_admin(current_user: dict = Depends(get_current_user)):
    """Require user to have admin role"""
    if current_user['role'] != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user

@router.post("/login")
async def login(login_data: LoginRequest):
    """Authenticate user and return JWT token"""
    # Find user in database
    user = db.users.find_one({'username': login_data.username})

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )

    # Check password
    if not check_password_hash(user['password_hash'], login_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )

    # Check if user is active
    if not user.get('is_active', True):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is disabled"
        )

    # Create JWT token
    token = create_jwt_token(user)

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "username": user['username'],
            "role": user['role'],
            "email": user.get('email', '')
        }
    }

@router.get("/me")
async def get_user_profile(current_user: dict = Depends(get_current_user)):
    """Get current user profile"""
    return {
        "username": current_user['username'],
        "email": current_user.get('email', ''),
        "role": current_user['role'],
        "created_date": current_user.get('created_date'),
        "is_active": current_user.get('is_active', True)
    }

@router.post("/create-uploader")
async def create_uploader_user(
    user_data: UserCreate, 
    current_user: dict = Depends(require_admin)
):
    """Create a new uploader user (admin only)"""
    # Check if username already exists
    if db.users.find_one({'username': user_data.username}):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )

    # Create new user
    new_user = {
        'username': user_data.username,
        'email': user_data.email,
        'password_hash': generate_password_hash(user_data.password),
        'role': user_data.role if user_data.role in ['admin', 'uploader', 'user'] else 'user',
        'created_date': datetime.now(),
        'is_active': True
    }

    result = db.users.insert_one(new_user)

    return {
        "message": f"User '{user_data.username}' created successfully",
        "user_id": str(result.inserted_id),
        "role": new_user['role']
    }
