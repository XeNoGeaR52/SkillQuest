import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class DifficultyEnum(str, enum.Enum):
    """Challenge difficulty levels."""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class AttemptStatusEnum(str, enum.Enum):
    """Attempt status options."""
    STARTED = "started"
    SUBMITTED = "submitted"
    PASSED = "passed"
    FAILED = "failed"


class User(Base):
    """User model representing players in the system."""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    total_xp = Column(Integer, default=0, nullable=False, index=True)
    level = Column(Integer, default=1, nullable=False)
    profile = Column(JSONB, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    attempts = relationship("Attempt", back_populates="user", cascade="all, delete-orphan")
    badges = relationship("UserBadge", back_populates="user", cascade="all, delete-orphan")


class Challenge(Base):
    """Challenge model representing tasks users can complete."""
    __tablename__ = "challenges"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    xp = Column(Integer, nullable=False)
    difficulty = Column(SQLEnum(DifficultyEnum), nullable=False, index=True)
    tags = Column(ARRAY(String), nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    published = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    attempts = relationship("Attempt", back_populates="challenge", cascade="all, delete-orphan")


class Attempt(Base):
    """Attempt model representing a user's attempt at a challenge."""
    __tablename__ = "attempts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    challenge_id = Column(UUID(as_uuid=True), ForeignKey("challenges.id"), nullable=False, index=True)
    status = Column(SQLEnum(AttemptStatusEnum), default=AttemptStatusEnum.STARTED, nullable=False)
    score = Column(Float, nullable=True)
    xp_awarded = Column(Integer, default=0, nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    submitted_at = Column(DateTime, nullable=True)
    attempt_metadata = Column(JSONB, nullable=True)

    # Relationships
    user = relationship("User", back_populates="attempts")
    challenge = relationship("Challenge", back_populates="attempts")


class Badge(Base):
    """Badge model representing achievements users can earn."""
    __tablename__ = "badges"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=False)
    condition = Column(JSONB, nullable=False)
    icon_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user_badges = relationship("UserBadge", back_populates="badge", cascade="all, delete-orphan")


class UserBadge(Base):
    """UserBadge model representing badges awarded to users."""
    __tablename__ = "user_badges"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    badge_id = Column(UUID(as_uuid=True), ForeignKey("badges.id"), nullable=False, index=True)
    awarded_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    badge_metadata = Column(JSONB, nullable=True)

    # Relationships
    user = relationship("User", back_populates="badges")
    badge = relationship("Badge", back_populates="user_badges")
