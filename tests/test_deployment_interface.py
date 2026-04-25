"""Tests for manual UAT deployment interface."""

import pytest
from src.auth.deployment_interface import (
    DeploymentConfig,
    DeploymentEnvironment,
    DeploymentInterface,
    DeploymentResult,
    ServiceType,
)


class TestDeploymentConfig:
    """Test cases for DeploymentConfig."""

    def test_valid_config(self) -> None:
        """Test creation of valid deployment config."""
        config = DeploymentConfig(
            environment=DeploymentEnvironment.UAT,
            services=[ServiceType.AUTH, ServiceType.API],
            version="1.0.0"
        )
        assert config.environment == DeploymentEnvironment.UAT
        assert len(config.services) == 2
        assert config.rollback_enabled is True

    def test_empty_services_raises_error(self) -> None:
        """Test that empty services list raises ValueError."""
        with pytest.raises(ValueError, match="At least one service"):
            DeploymentConfig(
                environment=DeploymentEnvironment.UAT,
                services=[],
                version="1.0.0"
            )

    def test_empty_version_raises_error(self) -> None:
        """Test that empty version raises ValueError."""
        with pytest.raises(ValueError, match="Version must be specified"):
            DeploymentConfig(
                environment=DeploymentEnvironment.UAT,
                services=[ServiceType.AUTH],
                version=""
            )


class TestDeploymentInterface:
    """Test cases for DeploymentInterface."""

    def test_successful_deployment(self) -> None:
        """Test successful deployment operation."""
        interface = DeploymentInterface()
        config = DeploymentConfig(
            environment=DeploymentEnvironment.UAT,
            services=[ServiceType.AUTH],
            version="1.0.0"
        )

        result = interface.deploy(config)

        assert result.success is True
        assert result.environment == DeploymentEnvironment.UAT
        assert result.version == "1.0.0"
        assert ServiceType.AUTH in result.deployed_services

    def test_dry_run_deployment(self) -> None:
        """Test dry run deployment does not execute."""
        interface = DeploymentInterface()
        config = DeploymentConfig(
            environment=DeploymentEnvironment.UAT,
            services=[ServiceType.AUTH, ServiceType.API],
            version="2.0.0",
            dry_run=True
        )

        result = interface.deploy(config)

        assert result.success is True
        assert "Dry run" in result.message
        assert len(result.deployed_services) == 2

    def test_multiple_services_deployment(self) -> None:
        """Test deployment with multiple services."""
        interface = DeploymentInterface()
        config = DeploymentConfig(
            environment=DeploymentEnvironment.UAT,
            services=[ServiceType.AUTH, ServiceType.API, ServiceType.FRONTEND],
            version="3.0.0"
        )

        result = interface.deploy(config)

        assert result.success is True
        assert len(result.deployed_services) == 3

    def test_deployment_history(self) -> None:
        """Test deployment history tracking."""
        interface = DeploymentInterface()
        config1 = DeploymentConfig(
            environment=DeploymentEnvironment.UAT,
            services=[ServiceType.AUTH],
            version="1.0.0"
        )
        config2 = DeploymentConfig(
            environment=DeploymentEnvironment.UAT,
            services=[ServiceType.API],
            version="1.1.0"
        )

        interface.deploy(config1)
        interface.deploy(config2)
        history = interface.get_deployment_history()

        assert len(history) == 2
        assert history[0].version == "1.0.0"
        assert history[1].version == "1.1.0"

    def test_custom_executor(self) -> None:
        """Test deployment with custom executor."""
        class MockExecutor:
            def execute(self, config: DeploymentConfig) -> list[ServiceType]:
                return config.services[:1]  # Only deploy first service

        interface = DeploymentInterface(executor=MockExecutor())
        config = DeploymentConfig(
            environment=DeploymentEnvironment.UAT,
            services=[ServiceType.AUTH, ServiceType.API],
            version="1.0.0"
        )

        result = interface.deploy(config)

        assert result.success is True
        assert len(result.deployed_services) == 1

    def test_rollback_configuration(self) -> None:
        """Test rollback availability configuration."""
        interface = DeploymentInterface()
        config = DeploymentConfig(
            environment=DeploymentEnvironment.UAT,
            services=[ServiceType.AUTH],
            version="1.0.0",
            rollback_enabled=False
        )

        result = interface.deploy(config)

        assert result.rollback_available is False
