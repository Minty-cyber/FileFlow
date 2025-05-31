from functools import wraps 
from fastapi import HTTPException, status
from app.api.deps import use_oauth2, get_current_user

def superuser_only(func):
    """ 
    Decorator to ensure that the user is a superuser before accessing the decorated route.
    This decorator checks if the user is authenticated and has superuser privileges.  
    The authenticated user is passed to the decorated function as `user`.
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        request = kwargs.get("request") or (args[0] if args else None)
        session = kwargs.get("session") or (args[1] if len(args) > 1 else None)
        if request is None or session is None:
            raise HTTPException(status_code=400, detail="Missing request or session")
        token = await use_oauth2(request)
        if not token:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authenticated"
            )
        user = await get_current_user(session, token)
        if not user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to view error logs"
            )
        kwargs["user"] = user
        return await func(*args, **kwargs)
    return wrapper