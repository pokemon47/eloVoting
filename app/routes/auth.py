from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from datetime import datetime
import os
import httpx
from typing import Dict, Any

router = APIRouter(prefix="/auth", tags=["auth"])

# Supabase configuration
SUPABASE_PROJECT_URL = os.getenv("SUPABASE_PROJECT_URL")
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")
SUPABASE_JWKS_URL = f"{SUPABASE_PROJECT_URL}/auth/v1/keys" if SUPABASE_PROJECT_URL else None

bearer_scheme = HTTPBearer()
jwks_cache = {}

async def get_jwks() -> Dict[str, Any]:
    """Fetch Supabase's public JWKS for JWT verification."""
    if not SUPABASE_JWKS_URL:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="SUPABASE_PROJECT_URL not configured"
        )
    
    if not jwks_cache:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(SUPABASE_JWKS_URL)
                resp.raise_for_status()
                jwks_cache.update(resp.json())
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch JWKS: {str(e)}"
            )
    return jwks_cache

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)
) -> Dict[str, Any]:
    """
    Verify Supabase JWT and extract user information.
    
    Flow:
    1. Extract JWT from Authorization header
    2. Try to verify using JWKS (preferred)
    3. Fallback to JWT_SECRET if JWKS fails
    4. Check token expiration
    5. Return user payload
    """
    token = credentials.credentials
    
    try:
        # Try JWKS verification first (more secure)
        if SUPABASE_JWKS_URL:
            jwks = await get_jwks()
            payload = jwt.decode(
                token,
                jwks,
                algorithms=["RS256"],
                options={"verify_aud": False}
            )
        # Fallback to JWT_SECRET
        elif SUPABASE_JWT_SECRET:
            payload = jwt.decode(
                token,
                SUPABASE_JWT_SECRET,
                algorithms=["HS256"],
                options={"verify_aud": False}
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="No JWT verification method configured"
            )
        
        # Check token expiration
        if payload.get("exp"):
            current_timestamp = datetime.utcnow().timestamp()
            if current_timestamp > payload["exp"]:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token expired"
                )
        
        # Validate required claims
        if not payload.get("sub"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user ID"
            )
        
        return payload
        
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token verification failed"
        )

@router.get("/me")
async def get_me(user: Dict[str, Any] = Depends(get_current_user)):
    """
    Get current user information from Supabase JWT.
    
    Returns user data extracted from the JWT token.
    """
    return {
        "user_id": user.get("sub"),
        "email": user.get("email"),
        "email_verified": user.get("email_verified", False),
        "aud": user.get("aud"),
        "iat": user.get("iat"),
        "exp": user.get("exp")
    }

@router.get("/verify")
async def verify_token(user: Dict[str, Any] = Depends(get_current_user)):
    """
    Simple endpoint to verify if a token is valid.
    
    Returns success if token is valid, 401 if not.
    """
    return {"message": "Token is valid", "user_id": user.get("sub")}

# Protected route example. Use this for reference when implementing protected routes.
@router.get("/protected")
async def protected_route(user: Dict[str, Any] = Depends(get_current_user)):
    user_id = user.get("sub")
    # Use user_id for authorization
    return {"message": f"Hello user {user_id}"} 