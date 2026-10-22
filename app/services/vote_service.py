from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Candidate, Vote, Voter


class VoteConflictError(Exception):
    pass


class EntityNotFoundError(Exception):
    pass


def cast_vote(db: Session, voter_id: int, candidate_id: int) -> Vote:
    try:
        voter = db.get(Voter, voter_id)
        if voter is None:
            raise EntityNotFoundError("El votante no existe")

        candidate = db.get(Candidate, candidate_id)
        if candidate is None:
            raise EntityNotFoundError("El candidato no existe")

        if voter.has_voted:
            raise VoteConflictError("El votante ya emitió su voto")

        vote = Vote(voter_id=voter_id, candidate_id=candidate_id)
        db.add(vote)
        voter.has_voted = True
        candidate.votes += 1
        db.commit()
        db.refresh(vote)
        return vote
    except (EntityNotFoundError, VoteConflictError):
        db.rollback()
        raise
    except IntegrityError as exc:
        db.rollback()
        raise VoteConflictError("El votante ya emitió su voto") from exc
    except Exception:
        db.rollback()
        raise
