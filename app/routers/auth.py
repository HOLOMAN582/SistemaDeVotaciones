from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import authenticate_admin, create_access_token, hash_password, verify_password
from app.database import get_db
from app.models import Voter

router = APIRouter(prefix="/auth", tags=["Authentication"])


class LoginRequest(BaseModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    voter_id: int | None = None


class VoterLoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest):
    if not authenticate_admin(payload.username, payload.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return TokenResponse(access_token=create_access_token(payload.username, "admin"), role="admin")


@router.post("/voter-login", response_model=TokenResponse)
def voter_login(payload: VoterLoginRequest, db: Session = Depends(get_db)):
    voter = db.scalar(select(Voter).where(Voter.email == payload.email.lower()))
    if voter is None or not verify_password(payload.password, voter.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return TokenResponse(
        access_token=create_access_token(voter.email, "voter", voter.id),
        role="voter",
        voter_id=voter.id,
    )
