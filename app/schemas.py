from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


def clean_name(value: str) -> str:
    value = " ".join(value.split())
    if not value:
        raise ValueError("El nombre no puede estar vacío")
    return value


class VoterCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        return clean_name(value)


class VoterRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: EmailStr
    has_voted: bool


class CandidateCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    party: str | None = Field(default=None, max_length=120)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        return clean_name(value)


class CandidateRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    party: str | None
    votes: int


class VoteCreate(BaseModel):
    voter_id: int = Field(gt=0)
    candidate_id: int = Field(gt=0)


class VoteRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    voter_id: int
    candidate_id: int


class CandidateStatistics(BaseModel):
    candidate_id: int
    candidate_name: str
    votes: int
    percentage: float


class VoteStatistics(BaseModel):
    total_votes: int
    voters_who_voted: int
    candidates: list[CandidateStatistics]
