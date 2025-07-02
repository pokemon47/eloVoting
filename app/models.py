from sqlalchemy import Column, String, Integer, Float, ForeignKey, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base
import uuid
import datetime

Base = declarative_base()

class Poll(Base):
    __tablename__ = "polls"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String)
    creator_email = Column(String, nullable=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Option(Base):
    __tablename__ = "options"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    poll_id = Column(UUID(as_uuid=True), ForeignKey("polls.id"))
    label = Column(String)

class VoterSession(Base):
    __tablename__ = "sessions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    poll_id = Column(UUID(as_uuid=True), ForeignKey("polls.id"))
    voter_email = Column(String, nullable=True)
    is_complete = Column(Boolean, default=False)
    started_at = Column(DateTime, default=datetime.datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

class MatchResult(Base):
    __tablename__ = "match_results"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id"))
    winner_option_id = Column(UUID(as_uuid=True), ForeignKey("options.id"))
    loser_option_id = Column(UUID(as_uuid=True), ForeignKey("options.id"))
    match_index = Column(Integer)

class GlobalScore(Base):
    __tablename__ = "global_scores"
    poll_id = Column(UUID(as_uuid=True), ForeignKey("polls.id"), primary_key=True)
    option_id = Column(UUID(as_uuid=True), ForeignKey("options.id"), primary_key=True)
    total_score = Column(Float, default=0.0) 