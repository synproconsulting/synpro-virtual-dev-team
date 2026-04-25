"""Manual UAT deployment interface with service selection."""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


class DeploymentEnvironment(Enum):
    """Supported deployment environments."""
    UAT = "uat"
    STAGING = "staging"
    PRODUCTION = "production"


class ServiceType(Enum):
    """Available service types for deployment."""
    AUTH = "auth"
    API = "api"
    FRONTEND = "frontend"
    DATABASE = "database"
    CACHE = "cache"


@dataclass
class DeploymentConfig:
    """Configuration for a deployment operation."""
    environment: DeploymentEnvironment
    services: list[ServiceType]
    version: str
    rollback_enabled: bool = True
    dry_run: bool = False

    def __post_init__(self) -> None:
        """Validate deployment configuration."""
        if not self.services:
            raise ValueError("At least one service must be selected")
        if not self.version:
            raise ValueError("Version must be specified")


@dataclass
class DeploymentResult:
    """Result of a deployment operation."""
    success: bool
    environment: DeploymentEnvironment
    deployed_services: list[ServiceType]
    version: str
    message: str
    rollback_available: bool = False


class DeploymentInterface:
    """Interface for manual UAT deployments with service selection."""

    def __init__(self, executor: Optional[object] = None) -> None:
        """
        Initialize deployment interface.

        Args:
            executor: Optional deployment executor (for dependency injection)
        """
        self._executor = executor
        self._deployment_history: list[DeploymentResult] = []

    def deploy(
        self,
        config: DeploymentConfig
    ) -> DeploymentResult:
        """
        Execute deployment with selected services.

        Args:
            config: Deployment configuration

        Returns:
            DeploymentResult with operation status

        Raises:
            ValueError: If configuration is invalid
        """
        logger.info(
            f"Starting deployment to {config.environment.value} "
            f"for services: {[s.value for s in config.services]}"
        )

        if config.dry_run:
            return self._dry_run_deployment(config)

        try:
            deployed_services = self._execute_deployment(config)
            result = DeploymentResult(
                success=True,
                environment=config.environment,
                deployed_services=deployed_services,
                version=config.version,
                message=f"Successfully deployed {len(deployed_services)} services",
                rollback_available=config.rollback_enabled
            )
            self._deployment_history.append(result)
            return result

        except Exception as e:
            logger.error(f"Deployment failed: {e}")
            result = DeploymentResult(
                success=False,
                environment=config.environment,
                deployed_services=[],
                version=config.version,
                message=f"Deployment failed: {str(e)}"
            )
            self._deployment_history.append(result)
            return result

    def _execute_deployment(
        self,
        config: DeploymentConfig
    ) -> list[ServiceType]:
        """
        Execute actual deployment logic.

        Args:
            config: Deployment configuration

        Returns:
            List of successfully deployed services
        """
        if self._executor:
            return self._executor.execute(config)  # type: ignore

        # Placeholder for actual deployment logic
        logger.info(f"Deploying version {config.version}")
        return config.services

    def _dry_run_deployment(self, config: DeploymentConfig) -> DeploymentResult:
        """
        Simulate deployment without executing.

        Args:
            config: Deployment configuration

        Returns:
            DeploymentResult for dry run
        """
        logger.info("Executing dry run")
        return DeploymentResult(
            success=True,
            environment=config.environment,
            deployed_services=config.services,
            version=config.version,
            message="Dry run completed successfully"
        )

    def get_deployment_history(self) -> list[DeploymentResult]:
        """Get history of deployment operations."""
        return self._deployment_history.copy()
