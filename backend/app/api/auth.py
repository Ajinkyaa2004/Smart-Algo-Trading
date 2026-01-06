"""
Kite Connect Authentication API Routes
Provides endpoints for login, callback, session status, and logout
"""
from fastapi import APIRouter, HTTPException, Query
from app.services.kite_auth import kite_auth_service

router = APIRouter()

@router.get("/login")
async def get_login_url():
    """
    Generate Zerodha login URL
    
    Returns:
        dict: Contains login_url for user to authenticate
    """
    try:
        login_url = kite_auth_service.get_login_url()
        return {
            "status": "success",
            "login_url": login_url,
            "instructions": "Open this URL in browser, login with Zerodha credentials, and you'll be redirected back"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate login URL: {str(e)}")


@router.get("/callback")
async def auth_callback(request_token: str = Query(...)):
    """
    Handle OAuth callback from Zerodha
    
    Args:
        request_token: Token received from Zerodha redirect
        
    Returns:
        RedirectResponse: Redirects to frontend dashboard
    """
    from fastapi.responses import RedirectResponse
    try:
        kite_auth_service.generate_session(request_token)
        return RedirectResponse(url="http://localhost:3000/?login=success")
    except Exception as e:
        error_msg = str(e).replace("'", "").replace('"', "")
        return RedirectResponse(url=f"http://localhost:3000/login?error={error_msg}")


@router.get("/status")
async def get_auth_status():
    """
    Check current authentication status
    
    Returns:
        dict: Authentication status and user info if logged in
    """
    is_authenticated = kite_auth_service.is_authenticated()
    
    response = {
        "is_authenticated": is_authenticated,
        "user": None
    }
    
    if is_authenticated:
        try:
            response["user"] = kite_auth_service.get_user_profile()
        except Exception:
            pass
    
    return response


@router.get("/user")
async def get_user_profile():
    """
    Get current user profile
    
    Returns:
        dict: User profile information
        
    Raises:
        HTTPException: If not authenticated
    """
    try:
        profile = kite_auth_service.get_user_profile()
        return profile
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.post("/logout")
async def logout():
    """
    Logout and clear session
    
    Returns:
        dict: Logout confirmation
    """
    result = kite_auth_service.logout()
    return result


@router.get("/verify")
async def verify_connection():
    """
    Verify that the Kite connection is working
    Tests the connection by fetching user profile
    
    Returns:
        dict: Connection status and profile data
    """
    try:
        kite = kite_auth_service.get_kite_instance()
        profile = kite.profile()
        
        return {
            "status": "success",
            "message": "Connection verified",
            "profile": profile
        }
    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail=f"Connection verification failed: {str(e)}"
        )
