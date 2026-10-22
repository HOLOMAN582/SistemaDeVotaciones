from sqlalchemy import Boolean, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Voter(Base):
    __tablename__ = "voters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    has_voted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    vote: Mapped["Vote | None"] = relationship(back_populates="voter", uselist=False)


class Candidate(Base):
    __tablename__ = "candidates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    party: Mapped[str | None] = mapped_column(String(120), nullable=True)
    votes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    votes_cast: Mapped[list["Vote"]] = relationship(back_populates="candidate")


class Vote(Base):
    __tablename__ = "votes"
    __table_args__ = (UniqueConstraint("voter_id", name="uq_votes_voter_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    voter_id: Mapped[int] = mapped_column(ForeignKey("voters.id"), nullable=False)
    candidate_id: Mapped[int] = mapped_column(ForeignKey("candidates.id"), nullable=False)

    voter: Mapped[Voter] = relationship(back_populates="vote")
    candidate: Mapped[Candidate] = relationship(back_populates="votes_cast")
