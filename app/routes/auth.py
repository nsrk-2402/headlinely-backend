import os
from typing import Optional, Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status, Cookie
from fastapi.responses import RedirectResponse, JSONResponse
from pydantic import BaseModel, EmailStr, constr
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.core.security import hash_password, verify_password, create_access_token, decode_access_token
from app.core.oauth import oauth

router = APIRouter(prefix="/auth", tags=["auth"])

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "false").lower() == "true"

# --- Pydantic schemas (small local definitions)
class SignupSchema(BaseModel):
    email: EmailStr
    password: Annotated[str, constr(min_length=8)]
    full_name: Optional[str] = None

class LoginSchema(BaseModel):
    email: EmailStr
    password: str

# --------- Cookie Helper ----------

def set_auth_cookie(response: Response, token: str):
    """
    Attach JWT as HttpOnly cookie
    """
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        # secure=False,           # For Dev
        secure=COOKIE_SECURE,
        # secure=True,           # send only over HTTPS in production
        samesite="lax",        # or "strict" if frontend and backend on same domain
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )    

# --- Manual Signup
@router.post("/signup")
def signup(payload: SignupSchema, response: Response, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email Already registered")
    
    user = User(
        email = payload.email,
        hashed_password = hash_password(payload.password),
        full_name = payload.full_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(str(user.id))
    set_auth_cookie(response, token)
    return {"message": "Signup successful"}


# --- Manual Login
@router.post("/login")
def login(payload: LoginSchema, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not user.hashed_password:
        raise HTTPException(status_code=400, detail="Invalid Credentails")
    
    if not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid Credentails")
    
    token = create_access_token(str(user.id))
    set_auth_cookie(response, token)
    return {"message": "Login successful"}


# --------- Get Current User ----------
@router.get("/me")
def get_me(access_token: Optional[str] = Cookie(default=None), db: Session=Depends(get_db)):
    if not access_token:
        raise HTTPException(status_code=401, detail="Not Authenticated")
    
    try:
        payload = decode_access_token(access_token)
        user_id = payload.get("sub")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid Token")
    
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not Found")
    
    return {"id": user.id, "email": user.email, "full_name": user.full_name}

# ---Logout---
@router.post("/logout")
def logout(response: Response):
    response.delete_cookie("access_token")
    return {"message": "Logged out"}


# ---OAuth: Login
@router.get("/oauth/{provider}")
async def oauth_login(provider: str, request: Request):
    if provider not in ("google", "github"):
        raise HTTPException(status_code=400, detail="Unsupported Provider")
    
    client = oauth.create_client(provider)
    if not client:
        raise HTTPException(status_code=400, detail=f"{provider} OAuth not configured")
    
    # The callback endpoint in this app:
    # redirect_path = f"/auth/oauth/{provider}/callback"
    # # Build the absolute redirect_uri based on current request host (works in Docker)
    # base = os.getenv("BACKEND_URL") or f"{request.url.scheme}://{request.url.hostname}:{request.url.port}"
    # redirect_uri = base.rstrip("/") + redirect_path
    redirect_uri = request.url_for("oauth_callback", provider=provider)
    return await client.authorize_redirect(request, redirect_uri)

# --- OAuth callback handling; this will be called by provider
@router.get("/oauth/{provider}/callback")
async def oauth_callback(provider: str, request: Request, response: Response, db: Session=Depends(get_db)):
    if provider not in ("google", "github"):
        raise HTTPException(status_code=400, detail="Unsupported Provider")
    
    client = oauth.create_client(provider)
    if not client:
        raise HTTPException(status_code=400, detail=f"{provider} OAuth not configured")
    
    # fetch Token
    token = await client.authorize_access_token(request)

    email, oauth_id, full_name = None, None, None
    

    if provider == "google":
        # For Google OIDC, parse ID token or userinfo
        # Try to parse ID token (preferred)
        try:
            userinfo = await client.parse_id_token(request, token)
            email = userinfo.get("email")
            oauth_id = userinfo.get("sub")
            full_name = userinfo.get("name")
        except Exception:
            # fallback to userinfo endpoint
            resp = await client.get("userinfo", token=token)
            data = resp.json()
            email = data.get("email")
            oauth_id = data.get("sub")
            full_name = data.get("name")

    elif provider == "github":
        # GitHub: get primary email if not present on profile
        resp = await client.get("user", token=token)
        profile = resp.json()
        oauth_id = str(profile.get("id"))
        full_name = profile.get("name") or profile.get("login")
        email = profile.get("email")

        if not email:
            resp2 = await client.get("user/emails", token=token)
            emails = await resp2.json()
            # find primary verified email
            primary = next((e for e in emails if e.get("primary") and e.get("verified")), None)
            # if primary:
            #     email = primary.get("email")
            # elif emails:
            #     email = emails[0].get("email")
            email = primary.get("email") if primary else emails[0].get("email") if emails else None
    if not email:
        # We require email for account linking
        raise HTTPException(status_code=400, detail="Unable to obtain email")
    
    # Check for existing user
    user = db.query(User).filter(User.email == email).first()

    if user:
        # If user exists but provider not set, link it
        if not user.oauth_provider:
            user.oauth_provider = provider
            user.oauth_id = oauth_id
            db.add(user)
            db.commit()
            db.refresh(user)
    else:
        # Create new user entry
        user = User(
            email = email,
            full_name = full_name,
            oauth_provider = provider,
            oauth_id = oauth_id,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    
    token_str = create_access_token(str(user.id))
    set_auth_cookie(response, token_str)

    # Redirect back to frontend (no token in URL)
    return RedirectResponse(FRONTEND_URL)    