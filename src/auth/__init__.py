"""Authentication module for email notifications."""

from .email_notifications import EmailNotificationService

__all__ = ["EmailNotificationService"]
from src.auth.feature_brief_ui import FeatureBriefUI
from src.auth.feature_brief_ui import FeatureBrief
from src.auth.feature_brief_ui import Priority
from src.auth.feature_brief_ui import FeatureStatus
from src.auth.dependency_graph import DependencyGraph
from src.auth.dependency_graph import DependencyVisualizer
from src.auth.sprint_dashboard import SprintDashboard
from src.auth.sprint_dashboard import DashboardService
from src.auth.sprint_dashboard import JiraAdapter
from src.auth.sprint_dashboard import GitHubAdapter
from src.auth.sprint_dashboard import CIAdapter
from src.auth.sprint_dashboard import JiraIssue
from src.auth.sprint_dashboard import PullRequest
from src.auth.sprint_dashboard import SprintMetrics
from src.auth.sprint_dashboard import IssueStatus
from src.auth.sprint_dashboard import PRStatus
from src.auth.sprint_dashboard import CIStatus
