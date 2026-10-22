from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.auth import require_admin
from app.database import get_db
from app.models import Candidate, Vote, Voter
from app.schemas import CandidateCreate, CandidateRead

router = APIRouter(prefix="/candidates", tags=["Candidates"])


@router.post("", response_model=CandidateRead, status_code=status.HTTP_201_CREATED)
def create_candidate(payload: CandidateCreate, db: Session = Depends(get_db), _: dict = Depends(require_admin)):
    normalized = payload.name.casefold()
    if db.scalar(select(Voter.id).where(func.lower(Voter.name) == normalized)):
        raise HTTPException(status_code=409, detail="El nombre ya está registrado como votante")
    candidate = Candidate(name=payload.name, party=payload.party)
    db.add(candidate)
    db.commit()
    db.refresh(candidate)
    return candidate


@router.get("", response_model=list[CandidateRead])
def list_candidates(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
    name: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    query = select(Candidate).order_by(Candidate.id).offset(skip).limit(limit)
    if name:
        query = query.where(Candidate.name.ilike(f"%{name.strip()}%"))
    return db.scalars(query).all()


@router.get("/{candidate_id}", response_model=CandidateRead)
def get_candidate(candidate_id: int, db: Session = Depends(get_db)):
    candidate = db.get(Candidate, candidate_id)
    if candidate is None:
        raise HTTPException(status_code=404, detail="El candidato no existe")
    return candidate


@router.delete("/{candidate_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_candidate(candidate_id: int, db: Session = Depends(get_db), _: dict = Depends(require_admin)):
    candidate = db.get(Candidate, candidate_id)
    if candidate is None:
        raise HTTPException(status_code=404, detail="El candidato no existe")
    if db.scalar(select(Vote.id).where(Vote.candidate_id == candidate_id)):
        raise HTTPException(status_code=409, detail="No se puede eliminar un candidato con votos")
    db.delete(candidate)
    db.commit()
