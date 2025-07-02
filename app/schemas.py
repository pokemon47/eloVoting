from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Union
from uuid import UUID
from datetime import datetime

class PollBase(BaseModel):
    title: str
    creator_email: Optional[EmailStr] = None

class PollCreate(PollBase):
    pass

class PollOut(PollBase):
    id: UUID
    is_verified: bool
    created_at: datetime

    class Config:
        from_attributes = True

class OptionBase(BaseModel):
    label: str

class OptionCreate(OptionBase):
    poll_id: UUID

class OptionOut(OptionBase):
    id: UUID
    poll_id: UUID

    class Config:
        from_attributes = True

class VoterSessionBase(BaseModel):
    poll_id: UUID
    voter_email: Optional[EmailStr] = None

class VoterSessionCreate(VoterSessionBase):
    pass

class VoterSessionOut(VoterSessionBase):
    id: UUID
    is_complete: bool
    started_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class MatchResultBase(BaseModel):
    session_id: UUID
    winner_option_id: UUID
    loser_option_id: UUID
    match_index: int

class MatchResultCreate(MatchResultBase):
    pass

class MatchResultOut(MatchResultBase):
    id: UUID

    class Config:
        from_attributes = True

class GlobalScoreOut(BaseModel):
    poll_id: UUID
    option_id: UUID
    total_score: float

    class Config:
        from_attributes = True

class LeaderboardEntry(BaseModel):
    label: str
    score: float
    rank: Union[int, str]  # int for ranked, 'NA' for no votes

class LeaderboardResponse(BaseModel):
    leaderboard: list[LeaderboardEntry] 