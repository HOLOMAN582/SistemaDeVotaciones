from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth import hash_password, require_admin
from app.database import get_db
from app.models import Candidate, Vote, Voter
from app.schemas import VoterCreate, VoterRead

router = APIRouter(prefix="/voters", tags=["Voters"])


@router.post("", response_model=VoterRead, status_code=status.HTTP_201_CREATED)
def create_voter(payload: VoterCreate, db: Session = Depends(get_db), _: dict = Depends(require_admin)):
    normalized = payload.name.casefold()
    if db.scalar(select(Candidate.id).where(func.lower(Candidate.name) == normalized)):
        raise HTTPException(status_code=409, detail="El nombre ya está registrado como candidato")
    voter = Voter(
        name=payload.name,
        email=str(payload.email).lower(),
        password_hash=hash_password(payload.password),
    )
    db.add(voter)
    try:
        db.commit()
        db.refresh(voter)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="El email ya está registrado") from exc
    return voter


@router.get("", response_model=list[VoterRead])
def list_voters(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
    name: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    query = select(Voter).order_by(Voter.id).offset(skip).limit(limit)
    if name:
        query = query.where(Voter.name.ilike(f"%{name.strip()}%"))
    return db.scalars(query).all()


@router.get("/{voter_id}", response_model=VoterRead)
def get_voter(voter_id: int, db: Session = Depends(get_db)):
    voter = db.get(Voter, voter_id)
    if voter is None:
        raise HTTPException(status_code=404, detail="El votante no existe")
    return voter


@router.delete("/{voter_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_voter(voter_id: int, db: Session = Depends(get_db), _: dict = Depends(require_admin)):
    voter = db.get(Voter, voter_id)
    if voter is None:
        raise HTTPException(status_code=404, detail="El votante no existe")
    if db.scalar(select(Vote.id).where(Vote.voter_id == voter_id)):
        raise HTTPException(status_code=409, detail="No se puede eliminar un votante que ya votó")
    db.delete(voter)
    db.commit()
