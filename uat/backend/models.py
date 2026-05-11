"""SQLAlchemy models for the application."""

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    JSON,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()


class User(Base):
    """User account model."""

    __tablename__ = "users"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)


class PasswordResetToken(Base):
    """Password reset token model."""

    __tablename__ = "password_reset_tokens"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token = Column(String(255), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class MessageRole(enum.Enum):
    """Enumeration for message roles in a conversation."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Conversation(Base):
    """Conversation thread in the PM Agent chat system."""

    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    user_id = Column(String(100), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Conversation(id={self.id}, title='{self.title}', user_id='{self.user_id}')>"


class Message(Base):
    """Individual message within a conversation."""

    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(Enum(MessageRole), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    conversation = relationship("Conversation", back_populates="messages")

    def __repr__(self) -> str:
        return f"<Message(id={self.id}, conversation_id={self.conversation_id}, role={self.role.value})>"


class Product(Base):
    """Product configuration for virtual dev team multi-product support (SDT1-95).

    Each product maps a software project to its Jira project, GitHub repo,
    and Railway deployment. The Jira proxy uses these values when a product_id
    is supplied, falling back to environment variables for single-product deployments.
    """

    __tablename__ = "products"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )
    name = Column(String(255), nullable=False, unique=True, index=True)
    jira_project_key = Column(String(50), nullable=False)
    jira_base_url = Column(String(500), nullable=True)
    github_org = Column(String(255), nullable=True)
    github_repo = Column(String(255), nullable=False)
    railway_service_id = Column(String(255), nullable=True)
    railway_project_id = Column(String(255), nullable=True)
    railway_backend_service_name = Column(String(255), nullable=True)
    railway_frontend_service_name = Column(String(255), nullable=True)
    railway_dev_service_id = Column(String(255), nullable=True)
    railway_test_service_id = Column(String(255), nullable=True)
    railway_prod_service_id = Column(String(255), nullable=True)
    sonarcloud_key = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<Product(id={self.id}, name='{self.name}', jira='{self.jira_project_key}')>"


class OrchestratorStatus(enum.Enum):
    """Status values for orchestrator execution runs."""

    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class OrchestratorState(Base):
    """Orchestrator execution state for resume capability.

    Tracks the execution progress of a sprint or set of tickets,
    allowing the orchestrator to resume from interruptions.
    """

    __tablename__ = "orchestrator_states"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )
    sprint_id = Column(Integer, nullable=False, index=True)
    sprint_name = Column(String(255), nullable=False)
    jira_project_key = Column(String(50), nullable=False)
    status = Column(Enum(OrchestratorStatus), nullable=False, default=OrchestratorStatus.PENDING)

    # JSON fields for flexible state storage
    ticket_queue = Column(JSON, nullable=False, default=list)  # List of ticket keys in execution order
    completed_tickets = Column(JSON, nullable=False, default=list)  # List of completed ticket keys
    failed_tickets = Column(JSON, nullable=False, default=list)  # List of failed ticket keys with error info
    current_ticket = Column(String(50), nullable=True)  # Currently executing ticket key

    # Metadata
    total_tickets = Column(Integer, nullable=False, default=0)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    last_checkpoint_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<OrchestratorState(id={self.id}, sprint_id={self.sprint_id}, status={self.status.value})>"
