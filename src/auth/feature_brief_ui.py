"""Feature brief submission UI for PM Agent chat interface."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class Priority(Enum):
    """Priority levels for feature briefs."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class FeatureStatus(Enum):
    """Status values for feature briefs."""
    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"


@dataclass
class FeatureBrief:
    """Data model for a feature brief submission."""
    title: str
    description: str
    priority: Priority
    user_id: str
    created_at: datetime
    status: FeatureStatus = FeatureStatus.DRAFT
    brief_id: Optional[str] = None
    updated_at: Optional[datetime] = None
    reviewer_notes: Optional[str] = None

    def validate(self) -> list[str]:
        """Validate the feature brief data.
        
        Returns:
            List of validation error messages, empty if valid.
        """
        errors = []
        
        if not self.title or len(self.title.strip()) < 5:
            errors.append("Title must be at least 5 characters long")
        
        if len(self.title) > 200:
            errors.append("Title must not exceed 200 characters")
        
        if not self.description or len(self.description.strip()) < 20:
            errors.append("Description must be at least 20 characters long")
        
        if len(self.description) > 5000:
            errors.append("Description must not exceed 5000 characters")
        
        if not self.user_id:
            errors.append("User ID is required")
        
        return errors


class FeatureBriefUI:
    """Chat interface for submitting and managing feature briefs."""

    def __init__(self, storage_backend: Optional[object] = None):
        """Initialize the feature brief UI.
        
        Args:
            storage_backend: Optional backend for persisting briefs.
        """
        self.storage = storage_backend
        self._briefs: dict[str, FeatureBrief] = {}

    def create_brief(
        self,
        title: str,
        description: str,
        priority: Priority,
        user_id: str
    ) -> tuple[Optional[FeatureBrief], list[str]]:
        """Create a new feature brief.
        
        Args:
            title: Feature title.
            description: Detailed feature description.
            priority: Priority level.
            user_id: ID of the user creating the brief.
        
        Returns:
            Tuple of (created brief or None, list of validation errors).
        """
        brief = FeatureBrief(
            title=title,
            description=description,
            priority=priority,
            user_id=user_id,
            created_at=datetime.utcnow()
        )
        
        errors = brief.validate()
        if errors:
            return None, errors
        
        brief.brief_id = self._generate_id()
        self._briefs[brief.brief_id] = brief
        
        return brief, []

    def submit_brief(self, brief_id: str) -> tuple[bool, str]:
        """Submit a draft brief for review.
        
        Args:
            brief_id: ID of the brief to submit.
        
        Returns:
            Tuple of (success status, message).
        """
        if brief_id not in self._briefs:
            return False, "Brief not found"
        
        brief = self._briefs[brief_id]
        
        if brief.status != FeatureStatus.DRAFT:
            return False, f"Cannot submit brief with status: {brief.status.value}"
        
        brief.status = FeatureStatus.SUBMITTED
        brief.updated_at = datetime.utcnow()
        
        return True, "Brief submitted successfully"

    def get_brief(self, brief_id: str) -> Optional[FeatureBrief]:
        """Retrieve a feature brief by ID.
        
        Args:
            brief_id: ID of the brief to retrieve.
        
        Returns:
            FeatureBrief if found, None otherwise.
        """
        return self._briefs.get(brief_id)

    def list_briefs(self, user_id: Optional[str] = None) -> list[FeatureBrief]:
        """List all briefs, optionally filtered by user.
        
        Args:
            user_id: Optional user ID to filter by.
        
        Returns:
            List of feature briefs.
        """
        briefs = list(self._briefs.values())
        
        if user_id:
            briefs = [b for b in briefs if b.user_id == user_id]
        
        return sorted(briefs, key=lambda b: b.created_at, reverse=True)

    def _generate_id(self) -> str:
        """Generate a unique ID for a brief.
        
        Returns:
            Unique brief ID.
        """
        import uuid
        return f"FB-{uuid.uuid4().hex[:12].upper()}"
