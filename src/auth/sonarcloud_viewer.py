"""Viewer for formatting and displaying SonarCloud analysis results."""

from typing import Any


class SonarCloudViewer:
    """Format and display SonarCloud analysis results."""

    @staticmethod
    def format_quality_gate(status_data: dict[str, Any]) -> str:
        """Format quality gate status into a readable string.

        Args:
            status_data: Quality gate status data from SonarCloud API.

        Returns:
            Formatted string representation of quality gate status.
        """
        project_status = status_data.get("projectStatus", {})
        status = project_status.get("status", "UNKNOWN")
        conditions = project_status.get("conditions", [])

        lines = [f"Quality Gate Status: {status}"]
        lines.append("=" * 50)

        if conditions:
            lines.append("\nConditions:")
            for condition in conditions:
                metric = condition.get("metricKey", "unknown")
                cond_status = condition.get("status", "UNKNOWN")
                actual_value = condition.get("actualValue", "N/A")
                error_threshold = condition.get("errorThreshold", "N/A")
                symbol = "✓" if cond_status == "OK" else "✗"
                lines.append(
                    f"  {symbol} {metric}: {actual_value} (threshold: {error_threshold}) - {cond_status}"
                )
        else:
            lines.append("\nNo conditions found.")

        return "\n".join(lines)

    @staticmethod
    def format_measures(measures_data: dict[str, Any]) -> str:
        """Format measures into a readable string.

        Args:
            measures_data: Measures data from SonarCloud API.

        Returns:
            Formatted string representation of measures.
        """
        component = measures_data.get("component", {})
        measures = component.get("measures", [])
        component_name = component.get("name", "Unknown Project")

        lines = [f"Measures for: {component_name}"]
        lines.append("=" * 50)

        if measures:
            for measure in measures:
                metric = measure.get("metric", "unknown")
                value = measure.get("value", "N/A")
                lines.append(f"  {metric}: {value}")
        else:
            lines.append("\nNo measures found.")

        return "\n".join(lines)

    @staticmethod
    def format_analysis_summary(
        quality_gate_data: dict[str, Any],
        measures_data: dict[str, Any] | None = None,
    ) -> str:
        """Format a complete analysis summary.

        Args:
            quality_gate_data: Quality gate status data.
            measures_data: Optional measures data.

        Returns:
            Complete formatted analysis summary.
        """
        sections = [SonarCloudViewer.format_quality_gate(quality_gate_data)]

        if measures_data:
            sections.append("\n" + SonarCloudViewer.format_measures(measures_data))

        return "\n\n".join(sections)
