"""Manual UAT deployment interface with service selection."""

from dataclasses import dataclass
from enum import Enum
from typing import Protocol


class DeploymentEnvironment(Enum):
    """Supported deployment environments."""

    UAT = "uat"
    STAGING = "staging"
    PRODUCTION = "production"


class ServiceType(Enum):
    """Available service types for deployment."""

    API = "api"
    WEB = "web"
    WORKER = "worker"
    DATABASE = "database"
    CACHE = "cache"


@dataclass
class ServiceConfig:
    """Configuration for a service deployment."""

    name: str
    service_type: ServiceType
    version: str
    replicas: int = 1
    enabled: bool = True


class DeploymentProvider(Protocol):
    """Protocol for deployment providers."""

    def deploy(self, config: ServiceConfig, environment: DeploymentEnvironment) -> str:
        """Deploy a service to the specified environment.

        Args:
            config: Service configuration
            environment: Target deployment environment

        Returns:
            Deployment ID or confirmation message
        """
        ...

    def validate_config(self, config: ServiceConfig) -> bool:
        """Validate service configuration.

        Args:
            config: Service configuration to validate

        Returns:
            True if configuration is valid
        """
        ...


class ManualUATDeployment:
    """Interface for manual UAT deployments with service selection."""

    def __init__(self, provider: DeploymentProvider) -> None:
        """Initialize the deployment interface.

        Args:
            provider: Deployment provider implementation
        """
        self._provider = provider
        self._selected_services: list[ServiceConfig] = []

    def add_service(self, config: ServiceConfig) -> None:
        """Add a service to the deployment selection.

        Args:
            config: Service configuration to add

        Raises:
            ValueError: If service configuration is invalid
        """
        if not self._provider.validate_config(config):
            raise ValueError(f"Invalid configuration for service: {config.name}")

        if not config.enabled:
            return

        self._selected_services.append(config)

    def remove_service(self, service_name: str) -> None:
        """Remove a service from the deployment selection.

        Args:
            service_name: Name of the service to remove
        """
        self._selected_services = [
            s for s in self._selected_services if s.name != service_name
        ]

    def get_selected_services(self) -> list[ServiceConfig]:
        """Get list of currently selected services.

        Returns:
            List of selected service configurations
        """
        return self._selected_services.copy()

    def clear_selection(self) -> None:
        """Clear all selected services."""
        self._selected_services.clear()

    def deploy_selected(
        self, environment: DeploymentEnvironment = DeploymentEnvironment.UAT
    ) -> dict[str, str]:
        """Deploy all selected services to the specified environment.

        Args:
            environment: Target deployment environment (default: UAT)

        Returns:
            Dictionary mapping service names to deployment IDs

        Raises:
            ValueError: If no services are selected or environment is not UAT
        """
        if not self._selected_services:
            raise ValueError("No services selected for deployment")

        if environment != DeploymentEnvironment.UAT:
            raise ValueError("Manual deployment only allowed to UAT environment")

        results: dict[str, str] = {}
        for config in self._selected_services:
            deployment_id = self._provider.deploy(config, environment)
            results[config.name] = deployment_id

        return results

    def get_deployment_summary(self) -> str:
        """Generate a summary of the planned deployment.

        Returns:
            Human-readable deployment summary
        """
        if not self._selected_services:
            return "No services selected for deployment"

        lines = [f"Deployment Summary ({len(self._selected_services)} services):"]
        for config in self._selected_services:
            lines.append(
                f"  - {config.name} ({config.service_type.value}) v{config.version} "
                f"[{config.replicas} replica(s)]"
            )

        return "\n".join(lines)
