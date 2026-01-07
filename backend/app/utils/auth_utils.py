"""
Authentication Utilities
Helper functions for extracting and validating session tokens from requests
"""
from fastapi import Header, HTTPException
from typing import Optional

async def get_session_token(
    authorization: Optional[str] = Header(None),
    token: Optional[str] = Header(None, alias="X-Session-Token")
) -> Optional[str]:
    """
    Extract session token from request headers
    
    Checks in order:
    1. X-Session-Token header
    2. Authorization header (Bearer token)
    
    Args:
        authorization: Authorization header
        token: X-Session-Token header
        
    Returns:
        Session token or None
    """
    # Check X-Session-Token header first
    if token:
        return token
    
    # Check Authorization header
    if authorization and authorization.startswith("Bearer "):
        return authorization.replace("Bearer ", "")
    
    return None


async def require_session_token(
    authorization: Optional[str] = Header(None),
    token: Optional[str] = Header(None, alias="X-Session-Token")
) -> str:
    """
    Require session token from request headers
    Raises HTTPException if not found
    
    Args:
        authorization: Authorization header
        token: X-Session-Token header
        
    Returns:
        Session token
        
    Raises:
        HTTPException: If token not found
    """
    session_token = await get_session_token(authorization, token)
    
    if not session_token:
        raise HTTPException(
            status_code=401,
            detail="Authentication required. Please provide session token in X-Session-Token header or Authorization header."
        )
    
    return session_token
