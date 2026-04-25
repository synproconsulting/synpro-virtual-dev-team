"""SonarCloud analysis results viewer with formatted output."""

from dataclasses import dataclass
from typing import Any

from src.auth.sonarcloud_client import SonarCloudClient


@dataclass
class AnalysisResults:
    """Container for SonarCloud analysis results."""

    project_key: str
    branch: str | None
    quality_gate_status: str
    conditions: list[dict[str, Any]]
    measures: dict[str, str]
    issues_count: int
    issues: list[dict[str, Any]]


class SonarCloudViewer:
    """Viewer for SonarCloud analysis results with formatting utilities."""

    def __init__(self, client: SonarCloudClient) -> None:
        """Initialize viewer with a SonarCloud client.

        Args:
            client: Configured SonarCloudClient instance.
        """
        self.client = client

    def get_analysis_results(
        self,
        project_key: str,
        branch: str | None = None,
        metric_keys: list[str] | None = None,
    ) -> AnalysisResults:
        """Retrieve comprehensive analysis results.

        Args:
            project_key: SonarCloud project key.
            branch: Optional branch name.
            metric_keys: List of metrics to retrieve. Defaults to common metrics.

        Returns:
            AnalysisResults object with all retrieved data.
        """
        if metric_keys is None:
            metric_keys = [
                "bugs",
                "vulnerabilities",
                "code_smells",
                "coverage",
                "duplicated_lines_density",
            ]

        # Get quality gate status
        status_data = self.client.get_project_status(project_key, branch)
        project_status = status_data.get("projectStatus", {})

        # Get measures
        measures_data = self.client.get_measures(project_key, metric_keys, branch)
        measures = {
            m["metric"]: m.get("value", "N/A")
            for m in measures_data.get("component", {}).get("measures", [])
        }

        # Get issues
        issues_data = self.client.get_issues(project_key, branch)
        issues = issues_data.get("issues", [])

        return AnalysisResults(
            project_key=project_key,
            branch=branch,
            quality_gate_status=project_status.get("status", "UNKNOWN"),
            conditions=project_status.get("conditions", []),
            measures=measures,
            issues_count=issues_data.get("total", 0),
            issues=issues,
        )

    def format_results(self, results: AnalysisResults) -> str:
        """Format analysis results as readable text.

        Args:
            results: AnalysisResults object to format.

        Returns:
            Formatted string representation of results.
        """
        lines = [
            f"Project: {results.project_key}",
            f"Branch: {results.branch or 'default'}",
            f"Quality Gate: {results.quality_gate_status}",
            "",
            "Metrics:",
        ]

        for metric, value in results.measures.items():
            lines.append(f"  {metric}: {value}")

        lines.extend([
            "",
            f"Total Issues: {results.issues_count}",
        ])

        if results.conditions:
            lines.extend(["", "Quality Gate Conditions:"])
            for cond in results.conditions:
                status = cond.get("status", "UNKNOWN")
                metric = cond.get("metricKey", "unknown")
                actual = cond.get("actualValue", "N/A")
                lines.append(f"  [{status}] {metric}: {actual}")

        return "\n".join(lines)

    def print_results(self, project_key: str, branch: str | None = None) -> None:
        """Retrieve and print analysis results.

        Args:
            project_key: SonarCloud project key.
            branch: Optional branch name.
        """
        results = self.get_analysis_results(project_key, branch)
        print(self.format_results(results))
