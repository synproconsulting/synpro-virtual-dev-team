"""Tests for manual UAT deployment interface."""

import pytest

from src.auth.manual_uat_deployment import (
    DeploymentEnvironment,
    ManualUATDeployment,
    ServiceConfig,
    ServiceType,
)


class MockDeploymentProvider:
    """Mock deployment provider for testing."""

    def __init__(self) -> None:
        self.deployed_services: list[tuple[ServiceConfig, DeploymentEnvironment]] = []
        self.validation_failures: set[str] = set()

    def deploy(self, config: ServiceConfig, environment: DeploymentEnvironment) -> str:
        """Mock deploy method."""
        self.deployed_services.append((config, environment))
        return f"deploy-{config.name}-{len(self.deployed_services)}"

    def validate_config(self, config: ServiceConfig) -> bool:
        """Mock validation method."""
        return config.name not in self.validation_failures


@pytest.fixture
def provider() -> MockDeploymentProvider:
    """Create a mock deployment provider."""
    return MockDeploymentProvider()


@pytest.fixture
def deployment(provider: MockDeploymentProvider) -> ManualUATDeployment:
    """Create a deployment interface instance."""
    return ManualUATDeployment(provider)


def test_add_service(deployment: ManualUATDeployment) -> None:
    """Test adding a service to the deployment."""
    config = ServiceConfig(
        name="api-service", service_type=ServiceType.API, version="1.0.0"
    )
    deployment.add_service(config)
    assert len(deployment.get_selected_services()) == 1


def test_add_disabled_service(deployment: ManualUATDeployment) -> None:
    """Test that disabled services are not added."""
    config = ServiceConfig(
        name="api-service",
        service_type=ServiceType.API,
        version="1.0.0",
        enabled=False,
    )
    deployment.add_service(config)
    assert len(deployment.get_selected_services()) == 0


def test_add_invalid_service(
    deployment: ManualUATDeployment, provider: MockDeploymentProvider
) -> None:
    """Test that invalid service configurations raise an error."""
    provider.validation_failures.add("bad-service")
    config = ServiceConfig(
        name="bad-service", service_type=ServiceType.API, version="1.0.0"
    )
    with pytest.raises(ValueError, match="Invalid configuration"):
        deployment.add_service(config)


def test_remove_service(deployment: ManualUATDeployment) -> None:
    """Test removing a service from the deployment."""
    config1 = ServiceConfig(
        name="api-service", service_type=ServiceType.API, version="1.0.0"
    )
    config2 = ServiceConfig(
        name="web-service", service_type=ServiceType.WEB, version="2.0.0"
    )
    deployment.add_service(config1)
    deployment.add_service(config2)
    deployment.remove_service("api-service")
    services = deployment.get_selected_services()
    assert len(services) == 1
    assert services[0].name == "web-service"


def test_clear_selection(deployment: ManualUATDeployment) -> None:
    """Test clearing all selected services."""
    config = ServiceConfig(
        name="api-service", service_type=ServiceType.API, version="1.0.0"
    )
    deployment.add_service(config)
    deployment.clear_selection()
    assert len(deployment.get_selected_services()) == 0


def test_deploy_selected(
    deployment: ManualUATDeployment, provider: MockDeploymentProvider
) -> None:
    """Test deploying selected services."""
    config1 = ServiceConfig(
        name="api-service", service_type=ServiceType.API, version="1.0.0"
    )
    config2 = ServiceConfig(
        name="web-service", service_type=ServiceType.WEB, version="2.0.0"
    )
    deployment.add_service(config1)
    deployment.add_service(config2)
    results = deployment.deploy_selected()
    assert len(results) == 2
    assert "api-service" in results
    assert "web-service" in results
    assert len(provider.deployed_services) == 2


def test_deploy_no_services(deployment: ManualUATDeployment) -> None:
    """Test that deploying with no services raises an error."""
    with pytest.raises(ValueError, match="No services selected"):
        deployment.deploy_selected()


def test_deploy_non_uat_environment(deployment: ManualUATDeployment) -> None:
    """Test that deploying to non-UAT environment raises an error."""
    config = ServiceConfig(
        name="api-service", service_type=ServiceType.API, version="1.0.0"
    )
    deployment.add_service(config)
    with pytest.raises(ValueError, match="Manual deployment only allowed to UAT"):
        deployment.deploy_selected(DeploymentEnvironment.PRODUCTION)


def test_get_deployment_summary(deployment: ManualUATDeployment) -> None:
    """Test generating deployment summary."""
    config = ServiceConfig(
        name="api-service", service_type=ServiceType.API, version="1.0.0", replicas=3
    )
    deployment.add_service(config)
    summary = deployment.get_deployment_summary()
    assert "api-service" in summary
    assert "1.0.0" in summary
    assert "3 replica" in summary


def test_get_deployment_summary_empty(deployment: ManualUATDeployment) -> None:
    """Test deployment summary with no services."""
    summary = deployment.get_deployment_summary()
    assert "No services selected" in summary
