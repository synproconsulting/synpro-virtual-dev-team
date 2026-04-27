"""Authentication module for email notifications."""

from .email_notifications import EmailNotificationService

__all__ = ["EmailNotificationService"]
from src.auth.feature_brief_ui import FeatureBriefUI
from src.auth.feature_brief_ui import FeatureBrief
from src.auth.feature_brief_ui import Priority
from src.auth.feature_brief_ui import FeatureStatus
from src.auth.dependency_graph import DependencyGraph
from src.auth.dependency_graph import DependencyVisualizer
from src.auth.email_notifier import RegistrationEmailNotifier
from src.auth.email_notifier import RegistrationEvent
from src.auth.email_notifier import EmailProvider
from src.auth.email_notifier import EmailTemplate
from src.auth.email_notifier import WelcomeEmailTemplate
