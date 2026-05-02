"""
Tests for SonarCloud router - SDT1-61
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi import HTTPException
from sonarcloud_router import (
    router,
    _get_sonar_headers,
    SonarTriggerRequest,
    SonarResultsResponse,
)


class TestSonarCloudRouter:
    """Test suite for SonarCloud router endpoints."""

    def test_get_sonar_headers_with_token(self):
        """Test that headers include Bearer token when configured."""
        with patch("sonarcloud_router.SONARCLOUD_TOKEN", "test-token-123"):
            headers = _get_sonar_headers()
            assert headers["Authorization"] == "Bearer test-token-123"
            assert headers["Accept"] == "application/json"

    def test_get_sonar_headers_without_token(self):
        """Test that headers work without token (for public projects)."""
        with patch("sonarcloud_router.SONARCLOUD_TOKEN", ""):
            headers = _get_sonar_headers()
            assert "Authorization" not in headers
            assert headers["Accept"] == "application/json"

    @pytest.mark.asyncio
    async def test_trigger_analysis_success(self):
        """Test successful trigger analysis request."""
        from fastapi.testclient import TestClient
        from main import app
        
        client = TestClient(app)
        
        request_data = {
            "projectKey": "test-project",
            "branch": "main",
            "pullRequest": None
        }
        
        response = client.post("/api/sonarcloud/trigger", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["projectKey"] == "test-project"
        assert "dashboardUrl" in data
        assert "test-project" in data["dashboardUrl"]

    @pytest.mark.asyncio
    async def test_trigger_analysis_missing_project_key(self):
        """Test trigger analysis with missing project key."""
        from fastapi.testclient import TestClient
        from main import app
        
        client = TestClient(app)
        
        request_data = {
            "projectKey": "",
            "branch": "main"
        }
        
        response = client.post("/api/sonarcloud/trigger", json=request_data)
        
        # Should fail validation
        assert response.status_code in [400, 422]

    @pytest.mark.asyncio
    async def test_trigger_analysis_with_pr(self):
        """Test trigger analysis with pull request."""
        from fastapi.testclient import TestClient
        from main import app
        
        client = TestClient(app)
        
        request_data = {
            "projectKey": "test-project",
            "branch": "feature-branch",
            "pullRequest": "123"
        }
        
        response = client.post("/api/sonarcloud/trigger", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "pullRequest=123" in data["dashboardUrl"]

    @pytest.mark.asyncio
    async def test_fetch_results_no_token(self):
        """Test fetch results fails without token."""
        from fastapi.testclient import TestClient
        from main import app
        
        with patch("sonarcloud_router.SONARCLOUD_TOKEN", ""):
            client = TestClient(app)
            response = client.get("/api/sonarcloud/results?projectKey=test-project")
            
            assert response.status_code == 500
            assert "token not configured" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_fetch_results_success(self):
        """Test successful fetch results."""
        from fastapi.testclient import TestClient
        from main import app
        
        mock_qg_response = MagicMock()
        mock_qg_response.status_code = 200
        mock_qg_response.json.return_value = {
            "projectStatus": {
                "status": "OK"
            }
        }
        
        mock_measures_response = MagicMock()
        mock_measures_response.status_code = 200
        mock_measures_response.json.return_value = {
            "component": {
                "measures": [
                    {"metric": "bugs", "value": "5"},
                    {"metric": "vulnerabilities", "value": "2"},
                    {"metric": "code_smells", "value": "20"},
                    {"metric": "coverage", "value": "85.5"},
                    {"metric": "ncloc", "value": "1500"}
                ]
            }
        }
        
        with patch("sonarcloud_router.SONARCLOUD_TOKEN", "test-token"):
            with patch("httpx.AsyncClient") as mock_client:
                mock_instance = AsyncMock()
                mock_instance.__aenter__.return_value = mock_instance
                mock_instance.__aexit__.return_value = None
                mock_instance.get = AsyncMock(side_effect=[mock_qg_response, mock_measures_response])
                mock_client.return_value = mock_instance
                
                client = TestClient(app)
                response = client.get("/api/sonarcloud/results?projectKey=test-project&branch=main")
                
                assert response.status_code == 200
                data = response.json()
                assert data["projectKey"] == "test-project"
                assert data["qualityGateStatus"] == "OK"
                assert data["issues"]["bugs"] == 5
                assert data["issues"]["vulnerabilities"] == 2
                assert len(data["metrics"]) > 0

    @pytest.mark.asyncio
    async def test_fetch_results_api_error(self):
        """Test fetch results handles API errors."""
        from fastapi.testclient import TestClient
        from main import app
        
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        
        with patch("sonarcloud_router.SONARCLOUD_TOKEN", "invalid-token"):
            with patch("httpx.AsyncClient") as mock_client:
                mock_instance = AsyncMock()
                mock_instance.__aenter__.return_value = mock_instance
                mock_instance.__aexit__.return_value = None
                mock_instance.get = AsyncMock(return_value=mock_response)
                mock_client.return_value = mock_instance
                
                client = TestClient(app)
                response = client.get("/api/sonarcloud/results?projectKey=test-project")
                
                assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_fetch_results_timeout(self):
        """Test fetch results handles timeout."""
        from fastapi.testclient import TestClient
        from main import app
        import httpx
        
        with patch("sonarcloud_router.SONARCLOUD_TOKEN", "test-token"):
            with patch("httpx.AsyncClient") as mock_client:
                mock_instance = AsyncMock()
                mock_instance.__aenter__.return_value = mock_instance
                mock_instance.__aexit__.return_value = None
                mock_instance.get = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))
                mock_client.return_value = mock_instance
                
                client = TestClient(app)
                response = client.get("/api/sonarcloud/results?projectKey=test-project")
                
                assert response.status_code == 504

    @pytest.mark.asyncio
    async def test_fetch_metrics_success(self):
        """Test fetch metrics endpoint."""
        from fastapi.testclient import TestClient
        from main import app
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "component": {
                "measures": [
                    {"metric": "bugs", "value": "3"}
                ]
            }
        }
        
        with patch("sonarcloud_router.SONARCLOUD_TOKEN", "test-token"):
            with patch("httpx.AsyncClient") as mock_client:
                mock_instance = AsyncMock()
                mock_instance.__aenter__.return_value = mock_instance
                mock_instance.__aexit__.return_value = None
                mock_instance.get = AsyncMock(return_value=mock_response)
                mock_client.return_value = mock_instance
                
                client = TestClient(app)
                response = client.get("/api/sonarcloud/metrics?projectKey=test-project&metrics=bugs")
                
                assert response.status_code == 200
                data = response.json()
                assert "component" in data

    @pytest.mark.asyncio
    async def test_fetch_quality_gate_success(self):
        """Test fetch quality gate endpoint."""
        from fastapi.testclient import TestClient
        from main import app
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "projectStatus": {
                "status": "OK"
            }
        }
        
        with patch("sonarcloud_router.SONARCLOUD_TOKEN", "test-token"):
            with patch("httpx.AsyncClient") as mock_client:
                mock_instance = AsyncMock()
                mock_instance.__aenter__.return_value = mock_instance
                mock_instance.__aexit__.return_value = None
                mock_instance.get = AsyncMock(return_value=mock_response)
                mock_client.return_value = mock_instance
                
                client = TestClient(app)
                response = client.get("/api/sonarcloud/quality-gate?projectKey=test-project")
                
                assert response.status_code == 200
                data = response.json()
                assert data["projectStatus"]["status"] == "OK"

    @pytest.mark.asyncio
    async def test_list_projects_success(self):
        """Test list projects endpoint."""
        from fastapi.testclient import TestClient
        from main import app
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "components": [
                {"key": "project1", "name": "Project 1", "qualifier": "TRK"},
                {"key": "project2", "name": "Project 2", "qualifier": "TRK"},
                {"key": "module1", "name": "Module 1", "qualifier": "BRC"}  # Should be filtered
            ]
        }
        
        with patch("sonarcloud_router.SONARCLOUD_TOKEN", "test-token"):
            with patch("sonarcloud_router.SONARCLOUD_ORG", "test-org"):
                with patch("httpx.AsyncClient") as mock_client:
                    mock_instance = AsyncMock()
                    mock_instance.__aenter__.return_value = mock_instance
                    mock_instance.__aexit__.return_value = None
                    mock_instance.get = AsyncMock(return_value=mock_response)
                    mock_client.return_value = mock_instance
                    
                    client = TestClient(app)
                    response = client.get("/api/sonarcloud/projects")
                    
                    assert response.status_code == 200
                    data = response.json()
                    assert data["total"] == 2
                    assert len(data["projects"]) == 2
                    assert all(p["qualifier"] == "TRK" for p in data["projects"])

    @pytest.mark.asyncio
    async def test_list_projects_no_org(self):
        """Test list projects fails without org configured."""
        from fastapi.testclient import TestClient
        from main import app
        
        with patch("sonarcloud_router.SONARCLOUD_TOKEN", "test-token"):
            with patch("sonarcloud_router.SONARCLOUD_ORG", ""):
                client = TestClient(app)
                response = client.get("/api/sonarcloud/projects")
                
                assert response.status_code == 500
                assert "SONARCLOUD_ORG not configured" in response.json()["detail"]


class TestSonarModels:
    """Test Pydantic models."""

    def test_sonar_trigger_request_valid(self):
        """Test valid trigger request model."""
        request = SonarTriggerRequest(
            projectKey="test-project",
            branch="main",
            pullRequest="123"
        )
        assert request.projectKey == "test-project"
        assert request.branch == "main"
        assert request.pullRequest == "123"

    def test_sonar_trigger_request_defaults(self):
        """Test trigger request with defaults."""
        request = SonarTriggerRequest(projectKey="test-project")
        assert request.projectKey == "test-project"
        assert request.branch == "main"
        assert request.pullRequest is None

    def test_sonar_results_response(self):
        """Test results response model."""
        from sonarcloud_router import SonarMetric, SonarIssuesSummary
        
        metrics = [
            SonarMetric(name="Bugs", value="5"),
            SonarMetric(name="Coverage", value="85%")
        ]
        issues = SonarIssuesSummary(bugs=5, vulnerabilities=2, codeSmells=20)
        
        response = SonarResultsResponse(
            projectKey="test-project",
            qualityGateStatus="OK",
            metrics=metrics,
            issues=issues,
            dashboardUrl="https://sonarcloud.io/dashboard?id=test-project"
        )
        
        assert response.projectKey == "test-project"
        assert response.qualityGateStatus == "OK"
        assert len(response.metrics) == 2
        assert response.issues.bugs == 5
