"""Tests for SonarCloud viewer."""

from unittest.mock import Mock

import pytest

from src.auth.sonarcloud_client import SonarCloudClient
from src.auth.sonarcloud_viewer import AnalysisResults, SonarCloudViewer


class TestSonarCloudViewer:
    """Test cases for SonarCloudViewer."""

    @pytest.fixture
    def mock_client(self) -> Mock:
        """Create a mock SonarCloud client."""
        client = Mock(spec=SonarCloudClient)
        client.get_project_status.return_value = {
            "projectStatus": {
                "status": "OK",
                "conditions": [
                    {"status": "OK", "metricKey": "coverage", "actualValue": "85.2"},
                ],
            }
        }
        client.get_measures.return_value = {
            "component": {
                "measures": [
                    {"metric": "bugs", "value": "5"},
                    {"metric": "coverage", "value": "85.2"},
                ]
            }
        }
        client.get_issues.return_value = {
            "total": 10,
            "issues": [
                {"key": "issue-1", "severity": "MAJOR"},
            ],
        }
        return client

    def test_get_analysis_results(self, mock_client: Mock) -> None:
        """Test retrieving analysis results."""
        viewer = SonarCloudViewer(mock_client)
        results = viewer.get_analysis_results("my-project", "main")

        assert results.project_key == "my-project"
        assert results.branch == "main"
        assert results.quality_gate_status == "OK"
        assert results.issues_count == 10
        assert len(results.issues) == 1
        assert results.measures["bugs"] == "5"
        assert results.measures["coverage"] == "85.2"

    def test_get_analysis_results_custom_metrics(self, mock_client: Mock) -> None:
        """Test retrieving analysis results with custom metrics."""
        viewer = SonarCloudViewer(mock_client)
        results = viewer.get_analysis_results("my-project", metric_keys=["bugs"])

        mock_client.get_measures.assert_called_once_with("my-project", ["bugs"], None)

    def test_format_results(self, mock_client: Mock) -> None:
        """Test formatting analysis results."""
        viewer = SonarCloudViewer(mock_client)
        results = AnalysisResults(
            project_key="test-project",
            branch="develop",
            quality_gate_status="ERROR",
            conditions=[
                {"status": "ERROR", "metricKey": "coverage", "actualValue": "60.0"},
            ],
            measures={"bugs": "10", "coverage": "60.0"},
            issues_count=25,
            issues=[],
        )

        formatted = viewer.format_results(results)

        assert "Project: test-project" in formatted
        assert "Branch: develop" in formatted
        assert "Quality Gate: ERROR" in formatted
        assert "bugs: 10" in formatted
        assert "coverage: 60.0" in formatted
        assert "Total Issues: 25" in formatted
        assert "[ERROR] coverage: 60.0" in formatted

    def test_format_results_default_branch(self, mock_client: Mock) -> None:
        """Test formatting results with no branch specified."""
        viewer = SonarCloudViewer(mock_client)
        results = AnalysisResults(
            project_key="test-project",
            branch=None,
            quality_gate_status="OK",
            conditions=[],
            measures={},
            issues_count=0,
            issues=[],
        )

        formatted = viewer.format_results(results)
        assert "Branch: default" in formatted

    def test_print_results(self, mock_client: Mock, capsys: pytest.CaptureFixture[str]) -> None:
        """Test printing analysis results."""
        viewer = SonarCloudViewer(mock_client)
        viewer.print_results("my-project", "main")

        captured = capsys.readouterr()
        assert "Project: my-project" in captured.out
        assert "Branch: main" in captured.out
        assert "Quality Gate: OK" in captured.out
