"""Tests for SonarCloud viewer."""

from src.auth.sonarcloud_viewer import SonarCloudViewer


class TestSonarCloudViewer:
    """Test cases for SonarCloudViewer."""

    def test_format_quality_gate_ok(self) -> None:
        """Test formatting quality gate with OK status."""
        status_data = {
            "projectStatus": {
                "status": "OK",
                "conditions": [
                    {
                        "metricKey": "coverage",
                        "status": "OK",
                        "actualValue": "85.5",
                        "errorThreshold": "80",
                    }
                ],
            }
        }

        result = SonarCloudViewer.format_quality_gate(status_data)

        assert "Quality Gate Status: OK" in result
        assert "✓ coverage" in result
        assert "85.5" in result

    def test_format_quality_gate_error(self) -> None:
        """Test formatting quality gate with ERROR status."""
        status_data = {
            "projectStatus": {
                "status": "ERROR",
                "conditions": [
                    {
                        "metricKey": "bugs",
                        "status": "ERROR",
                        "actualValue": "15",
                        "errorThreshold": "10",
                    }
                ],
            }
        }

        result = SonarCloudViewer.format_quality_gate(status_data)

        assert "Quality Gate Status: ERROR" in result
        assert "✗ bugs" in result
        assert "15" in result

    def test_format_quality_gate_no_conditions(self) -> None:
        """Test formatting quality gate without conditions."""
        status_data = {"projectStatus": {"status": "OK", "conditions": []}}

        result = SonarCloudViewer.format_quality_gate(status_data)

        assert "Quality Gate Status: OK" in result
        assert "No conditions found" in result

    def test_format_measures(self) -> None:
        """Test formatting measures."""
        measures_data = {
            "component": {
                "name": "My Project",
                "measures": [
                    {"metric": "coverage", "value": "85.5"},
                    {"metric": "bugs", "value": "3"},
                ],
            }
        }

        result = SonarCloudViewer.format_measures(measures_data)

        assert "Measures for: My Project" in result
        assert "coverage: 85.5" in result
        assert "bugs: 3" in result

    def test_format_measures_empty(self) -> None:
        """Test formatting measures with no data."""
        measures_data = {"component": {"name": "My Project", "measures": []}}

        result = SonarCloudViewer.format_measures(measures_data)

        assert "Measures for: My Project" in result
        assert "No measures found" in result

    def test_format_analysis_summary(self) -> None:
        """Test formatting complete analysis summary."""
        quality_gate_data = {
            "projectStatus": {"status": "OK", "conditions": []}
        }
        measures_data = {
            "component": {
                "name": "My Project",
                "measures": [{"metric": "coverage", "value": "85.5"}],
            }
        }

        result = SonarCloudViewer.format_analysis_summary(
            quality_gate_data, measures_data
        )

        assert "Quality Gate Status: OK" in result
        assert "Measures for: My Project" in result
        assert "coverage: 85.5" in result
