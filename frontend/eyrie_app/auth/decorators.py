"""
Authentication decorators for Flask view routes
"""
from functools import wraps
from flask import request, redirect, url_for, current_app
from typing import Callable, Any, List


def get_current_user():
    """Get current user from session"""
    # Import here to avoid circular imports
    from ..app import sessions, find_user_by_id
    
    session_id = request.cookies.get("session_id")
    if not session_id or session_id not in sessions:
        return None

    user_id = sessions[session_id].get("user_id")
    user = find_user_by_id(user_id)
    return user


def login_required(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Decorator to require authentication for view routes.
    Redirects to login page if user is not authenticated.
    """
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        user = get_current_user()
        if not user:
            return redirect('/login')
        
        # Add user to kwargs for the decorated function
        kwargs['current_user'] = user
        return func(*args, **kwargs)
    
    return wrapper


def role_required(allowed_roles: List[str]) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Decorator to require specific roles for view routes.
    Redirects to login page if user is not authenticated.
    Redirects to samples page if user doesn't have required role.
    
    Args:
        allowed_roles: List of roles that are allowed to access the view
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            user = get_current_user()
            if not user:
                return redirect('/login')
            
            if user.get('role') not in allowed_roles:
                # Redirect to samples page if user doesn't have required role
                return redirect('/samples')
            
            # Add user to kwargs for the decorated function
            kwargs['current_user'] = user
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def admin_required_view(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Decorator to require admin role for view routes.
    Shorthand for @role_required(['admin'])
    """
    return role_required(['admin'])(func)


def uploader_or_admin_required(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Decorator to require uploader or admin role for view routes.
    Shorthand for @role_required(['admin', 'uploader'])
    """
    return role_required(['admin', 'uploader'])(func)
