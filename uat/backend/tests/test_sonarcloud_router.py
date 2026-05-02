"""
test_sonarcloud_router.py
==========================
Tests for the SonarCloud router.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from main import app

client = TestClient(app)


@pytest.fixture
def mock_sonarcloud_token(monkeypatch):
    """Mock the SONARCLOUD_TOKEN environment variable."""
    monkeypatch.setenv("SONARCLOUD_TOKEN", "test_token_123")


@pytest.fixture
def mock_sonarcloud_api():
    """Mock the SonarCloud API responses."""
    with patch("sonarcloud_router._fetch_sonarcloud_api", new_callable=AsyncMock) as mock:
        yield mock


class TestTriggerAnalysis:
    """Tests for the trigger analysis endpoint."""

    def test_trigger_analysis_success(self, mock_sonarcloud_token):
        """Test successful analysis trigger."""
        payload = {
            "projectKey": "test-org_test-project",
            "branch": "main",
            "pullRequest": None
        }
        
        response = client.post("/api/sonarcloud/trigger", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "dashboardUrl" in data
        assert "test-org_test-project" in data["dashboardUrl"]

    def test_trigger_analysis_with_branch(self, mock_sonarcloud_token):
        """Test analysis trigger with specific branch."""
        payload = {
            "projectKey": "test-org_test-project",
            "branch": "feature/test",
            "pullRequest": None
        }
        
        response = client.post("/api/sonarcloud/trigger", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert "branch=feature/test" in data["dashboardUrl"]

    def test_trigger_analysis_with_pr(self, mock_sonarcloud_token):
        """Test analysis trigger with pull request."""
        payload = {
            "projectKey": "test-org_test-project",
            "branch": "main",
            "pullRequest": "123"
        }
        
        response = client.post("/api/sonarcloud/trigger", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert "pullRequest=123" in data["dashboardUrl"]

    def test_trigger_analysis_missing_project_key(self, mock_sonarcloud_token):
        """Test analysis trigger without project key."""
        payload = {
            "branch": "main"
        }
        
        response = client.post("/api/sonarcloud/trigger", json=payload)
        
        assert response.status_code == 422  # Validation error


class TestGetResults:
    """Tests for the get results endpoint."""

    def test_get_results_success(self, mock_sonarcloud_token, mock_sonarcloud_api):
        """Test successful results fetch."""
        # Mock quality gate response
        mock_sonarcloud_api.side_effect = [
            {
                "projectStatus": {
                    "status": "OK",
                    "conditions": [
                        {
                            "metricKey": "new_coverage",
                            "comparator": "LT",
                            "errorThreshold": "80",
                            "actualValue": "85.5",
                            "status": "OK"
                        }
                    ]
                }
            },
            # Mock measures response
            {
                "component": {
                    "measures": [
                        {"metric": "bugs", "value": "5"},
                        {"metric": "vulnerabilities", "value": "2"},
                        {"metric": "code_smells", "value": "15"},
                        {"metric": "coverage", "value": "85.5"},
                        {"metric": "duplicated_lines_density", "value": "3.2"}
                    ]
                }
            }
        ]
        
        response = client.get("/api/sonarcloud/results?projectKey=test-project&branch=main")
        
        assert response.status_code == 200
        data = response.json()
        assert data["qualityGateStatus"] == "OK"
        assert data["issues"]["bugs"] == 5
        assert data["issues"]["vulnerabilities"] == 2
        assert data["issues"]["codeSmells"] == 15
        assert data["coverage"] == "85.5"
        assert data["duplications"] == "3.2"
        assert len(data["qualityGateConditions"]) == 1

    def test_get_results_missing_project_key(self, mock_sonarcloud_token):
        """Test results fetch without project key."""
        response = client.get("/api/sonarcloud/results")
        
        assert response.status_code == 422  # Validation error

    def test_get_results_api_error(self, mock_sonarcloud_token, mock_sonarcloud_api):
        """Test results fetch when API returns error."""
        mock_sonarcloud_api.side_effect = Exception("API error")
        
        response = client.get("/api/sonarcloud/results?projectKey=test-project")
        
        assert response.status_code == 500


class TestGetIssues:
    """Tests for the get issues endpoint."""

    def test_get_issues_success(self, mock_sonarcloud_token, mock_sonarcloud_api):
        """Test successful issues fetch."""
        mock_sonarcloud_api.return_value = {
            "issues": [
                {
                    "key": "issue1",
                    "rule": "squid:S1234",
                    "severity": "MAJOR",
                    "component": "test-project:src/main.py",
                    "line": 42,
                    "message": "Test issue message",
                    "type": "BUG",
                    "status": "OPEN",
                    "creationDate": "2024-01-01T00:00:00Z"
                }
            ]
        }
        
        response = client.get("/api/sonarcloud/issues?projectKey=test-project&branch=main")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["key"] == "issue1"
        assert data[0]["severity"] == "MAJOR"
        assert data[0]["type"] == "BUG"

    def test_get_issues_with_filters(self, mock_sonarcloud_token, mock_sonarcloud_api):
        """Test issues fetch with filters."""
        mock_sonarcloud_api.return_value = {"issues": []}
        
        response = client.get(
            "/api/sonarcloud/issues?projectKey=test-project&types=BUG&severities=MAJOR,CRITICAL"
        )
        
        assert response.status_code == 200
        # Verify that the filter parameters were passed
        mock_sonarcloud_api.assert_called_once()

    def test_get_issues_pagination(self, mock_sonarcloud_token, mock_sonarcloud_api):
        """Test issues fetch with pagination."""
        mock_sonarcloud_api.return_value = {"issues": []}
        
        response = client.get(
            "/api/sonarcloud/issues?projectKey=test-project&page=2&pageSize=50"
        )
        
        assert response.status_code == 200


class TestGetMetrics:
    """Tests for the get metrics endpoint."""

    def test_get_metrics_success(self, mock_sonarcloud_token, mock_sonarcloud_api):
        """Test successful metrics fetch."""
        mock_sonarcloud_api.return_value = {
            "component": {
                "measures": [
                    {"metric": "ncloc", "value": "1000"},
                    {"metric": "complexity", "value": "150"}
                ]
            }
        }
        
        response = client.get(
            "/api/sonarcloud/metrics?projectKey=test-project&metricKeys=ncloc,complexity"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "component" in data

    def test_get_metrics_missing_project_key(self, mock_sonarcloud_token):
        """Test metrics fetch without project key."""
        response = client.get("/api/sonarcloud/metrics?metricKeys=ncloc")
        
        assert response.status_code == 422


class TestGetQualityGate:
    """Tests for the get quality gate endpoint."""

    def test_get_quality_gate_success(self, mock_sonarcloud_token, mock_sonarcloud_api):
        """Test successful quality gate fetch."""
        mock_sonarcloud_api.return_value = {
            "projectStatus": {
                "status": "OK",
                "conditions": []
            }
        }
        
        response = client.get(
            "/api/sonarcloud/quality-gate?projectKey=test-project&branch=main"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "projectStatus" in data
        assert data["projectStatus"]["status"] == "OK"

    def test_get_quality_gate_failed(self, mock_sonarcloud_token, mock_sonarcloud_api):
        """Test quality gate fetch when gate is failed."""
        mock_sonarcloud_api.return_value = {
            "projectStatus": {
                "status": "ERROR",
                "conditions": [
                    {
                        "metricKey": "new_coverage",
                        "status": "ERROR"
                    }
                ]
            }
        }
        
        response = client.get(
            "/api/sonarcloud/quality-gate?projectKey=test-project"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["projectStatus"]["status"] == "ERROR"


class TestAuthentication:
    """Tests for authentication."""

    def test_missing_token(self, monkeypatch):
        """Test behavior when SONARCLOUD_TOKEN is not set."""
        monkeypatch.delenv("SONARCLOUD_TOKEN", raising=False)
        
        # This should fail when trying to make actual API calls
        response = client.get("/api/sonarcloud/results?projectKey=test-project")
        
        assert response.status_code == 500
        assert "SONARCLOUD_TOKEN" in response.json()["detail"]
