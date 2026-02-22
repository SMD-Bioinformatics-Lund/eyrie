"""
JWT-based authentication module for Eyrie frontend.

This module provides JWT cookie-based authentication, replacing Flask-Login sessions.
The JWT stored in an HTTP-only cookie serves as the single source of truth.
"""

import base64
import json
import logging
from functools import wraps
from typing import Any, Callable, Optional

from flask import g, redirect, request, url_for

from .config import settings

LOG = logging.getLogger(__name__)

# Cookie name for JWT token
JWT_COOKIE_NAME = 'eyrie_jwt'


class JWTUser:
    """
    Represents a user decoded from a JWT token.

    This is a simple container for user data extracted from the JWT payload.
    No verification is done here - the backend validates the token on each API call.
    """

    def __init__(self, username: str, role: str, email: str = '', user_id: str = ''):
        self.username = username
        self.role = role
        self.email = email
        self.user_id = user_id

    @property
    def is_authenticated(self) -> bool:
        """Always True for JWTUser instances - if we have a user, they're authenticated."""
        return True

    @property
    def is_admin(self) -> bool:
        """Check if user has admin role."""
        return self.role == 'admin'

    def __repr__(self) -> str:
        return f'<JWTUser {self.username} ({self.role})>'


def get_jwt_from_cookie() -> Optional[str]:
    """
    Extract JWT token from the eyrie_jwt cookie.

    Returns:
        The JWT token string, or None if not present.
    """
    return request.cookies.get(JWT_COOKIE_NAME)


def decode_jwt_payload(token: str) -> Optional[dict]:
    """
    Decode JWT payload without verification.

    This is safe because:
    1. The cookie is HTTP-only and can't be tampered with client-side
    2. The backend validates the token on every API call
    3. This is only used for UI display (username, role)

    Args:
        token: The JWT token string

    Returns:
        The decoded payload dict, or None if decoding fails.
    """
    try:
        # JWT format: header.payload.signature
        parts = token.split('.')
        if len(parts) != 3:
            return None

        # Decode the payload (middle part)
        payload_b64 = parts[1]

        # Add padding if needed (JWT uses base64url encoding without padding)
        padding = 4 - len(payload_b64) % 4
        if padding != 4:
            payload_b64 += '=' * padding

        # Decode from base64url (replace - with + and _ with /)
        payload_b64 = payload_b64.replace('-', '+').replace('_', '/')
        payload_json = base64.b64decode(payload_b64)

        return json.loads(payload_json)
    except Exception as e:
        LOG.debug(f"Failed to decode JWT payload: {e}")
        return None


def get_current_user() -> Optional[JWTUser]:
    """
    Get the current user from the JWT cookie.

    Results are cached in Flask's g object for the duration of the request.

    Returns:
        JWTUser instance if authenticated, None otherwise.
    """
    # Check cache first
    if hasattr(g, '_current_user'):
        return g._current_user

    # Get token from cookie
    token = get_jwt_from_cookie()
    if not token:
        g._current_user = None
        return None

    # Decode payload
    payload = decode_jwt_payload(token)
    if not payload:
        g._current_user = None
        return None

    # Extract user info from payload
    # JWT payload typically has 'sub' for username, but we may also have custom fields
    username = payload.get('sub') or payload.get('username', '')
    role = payload.get('role', 'user')
    email = payload.get('email', '')
    user_id = payload.get('user_id', '')

    if not username:
        g._current_user = None
        return None

    # Create and cache user
    user = JWTUser(username=username, role=role, email=email, user_id=user_id)
    g._current_user = user
    return user


def jwt_required(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Decorator to require JWT authentication for view routes.

    Redirects to login page if no valid JWT token is present.
    """
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        user = get_current_user()
        if user is None:
            # Store the original path to redirect back after login
            # Use full_path (not url) to get relative path, avoiding scheme mismatches
            return redirect(url_for('login.login', next=request.full_path))
        return func(*args, **kwargs)
    return wrapper


def admin_required(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Decorator to require admin role for view routes.

    First checks for authentication, then checks for admin role.
    Redirects to login if not authenticated, or to samples page if not admin.
    """
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        user = get_current_user()
        if user is None:
            return redirect(url_for('login.login', next=request.full_path))
        if not user.is_admin:
            return redirect(url_for('samples.samples_page'))
        return func(*args, **kwargs)
    return wrapper


def set_jwt_cookie(response, token: str):
    """
    Set the JWT cookie on a response object.

    Args:
        response: Flask response object
        token: JWT token string

    Returns:
        The response object with cookie set
    """
    response.set_cookie(
        JWT_COOKIE_NAME,
        token,
        httponly=True,
        samesite='Lax',
        secure=settings.jwt_cookie_secure,
        path=settings.session_cookie_path
    )
    return response


def clear_jwt_cookie(response):
    """
    Clear the JWT cookie on a response object.

    Args:
        response: Flask response object

    Returns:
        The response object with cookie cleared
    """
    response.set_cookie(
        JWT_COOKIE_NAME,
        '',
        max_age=0,
        httponly=True,
        samesite='Lax',
        secure=settings.jwt_cookie_secure,
        path=settings.session_cookie_path
    )
    return response
