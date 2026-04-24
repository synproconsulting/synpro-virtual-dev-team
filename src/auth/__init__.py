"""Authentication module for email notifications."""

from .email_notifications import EmailNotificationService

__all__ = ["EmailNotificationService"]
from src.auth.feature_brief_ui import FeatureBriefUI
from src.auth.feature_brief_ui import FeatureBrief
from src.auth.feature_brief_ui import Priority
from src.auth.feature_brief_ui import FeatureStatus
from src.auth.sprint_dashboard import SprintDashboard
from src.auth.sprint_dashboard import JiraProvider
from src.auth.sprint_dashboard import PRProvider
from src.auth.sprint_dashboard import CIProvider
from src.auth.sprint_dashboard import StatusType
from src.auth.sprint_dashboard import JiraTicket
from src.auth.sprint_dashboard import PullRequest
from src.auth.sprint_dashboard import CIBuild
from src.auth.sprint_dashboard import SprintMetrics
