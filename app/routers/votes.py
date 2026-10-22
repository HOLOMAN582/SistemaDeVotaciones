from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select, true
from sqlalchemy.orm import Session

from app.auth import require_voter
from app.database import get_db
from app.models import Candidate, Vote, Voter
from app.schemas import CandidateStatistics, VoteCreate, VoteRead, VoteStatistics
from app.services.vote_service import EntityNotFoundError, VoteConflictError, cast_vote

router = APIRouter(prefix="/votes", tags=["Votes"])


@router.post("", response_model=VoteRead, status_code=status.HTTP_201_CREATED)
def create_vote(payload: VoteCreate, db: Session = Depends(get_db), principal: dict = Depends(require_voter)):
    if principal.get("voter_id") != payload.voter_id:
        raise HTTPException(status_code=403, detail="Solo puedes emitir tu propio voto")
    try:
        return cast_vote(db, payload.voter_id, payload.candidate_id)
    except EntityNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except VoteConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("", response_model=list[VoteRead])
def list_votes(db: Session = Depends(get_db)):
    return db.scalars(select(Vote).order_by(Vote.id)).all()


@router.get("/statistics", response_model=VoteStatistics)
def get_statistics(db: Session = Depends(get_db)):
    total_votes = db.scalar(select(func.count(Vote.id))) or 0
    voters_who_voted = db.scalar(select(func.count(Voter.id)).where(Voter.has_voted == true())) or 0
    candidates = db.scalars(select(Candidate).order_by(Candidate.id)).all()
    return VoteStatistics(
        total_votes=total_votes,
        voters_who_voted=voters_who_voted,
        candidates=[
            CandidateStatistics(
                candidate_id=candidate.id,
                candidate_name=candidate.name,
                votes=candidate.votes,
                percentage=round((candidate.votes / total_votes * 100) if total_votes else 0, 2),
            )
            for candidate in candidates
        ],
    )
