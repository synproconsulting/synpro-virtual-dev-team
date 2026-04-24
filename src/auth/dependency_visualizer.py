"""Visualize dependency graphs in various formats."""

from typing import List, Dict
from src.auth.dependency_graph import DependencyGraph


class DependencyVisualizer:
    """Visualizes story dependencies in different formats."""

    def __init__(self, graph: DependencyGraph) -> None:
        """Initialize visualizer with a dependency graph.

        Args:
            graph: DependencyGraph instance to visualize
        """
        self.graph = graph

    def to_ascii(self) -> str:
        """Generate ASCII tree representation of dependencies.

        Returns:
            ASCII art string representing the dependency tree
        """
        lines: List[str] = []
        levels = self.graph.get_levels()

        lines.append("Dependency Execution Levels:")
        lines.append("=" * 40)

        for level_num, stories in enumerate(levels, 1):
            lines.append(f"\nLevel {level_num}:")
            for story in stories:
                deps = self.graph.get_dependencies(story)
                if deps:
                    lines.append(f"  [{story}] depends on: {', '.join(sorted(deps))}")
                else:
                    lines.append(f"  [{story}] (no dependencies)")

        return "\n".join(lines)

    def to_mermaid(self) -> str:
        """Generate Mermaid diagram syntax for dependency graph.

        Returns:
            Mermaid diagram string
        """
        lines = ["graph TD"]

        for node in sorted(self.graph.nodes):
            lines.append(f"    {node}[{node}]")

        for node in sorted(self.graph.nodes):
            for dependent in sorted(self.graph.get_dependents(node)):
                lines.append(f"    {node} --> {dependent}")

        return "\n".join(lines)

    def to_dot(self) -> str:
        """Generate GraphViz DOT format for dependency graph.

        Returns:
            DOT format string
        """
        lines = ["digraph Dependencies {", "    rankdir=LR;"]

        for node in sorted(self.graph.nodes):
            lines.append(f'    "{node}";')

        for node in sorted(self.graph.nodes):
            for dependent in sorted(self.graph.get_dependents(node)):
                lines.append(f'    "{node}" -> "{dependent}";')

        lines.append("}")
        return "\n".join(lines)

    def get_execution_summary(self) -> Dict[str, object]:
        """Generate execution summary with statistics.

        Returns:
            Dictionary containing execution order and statistics
        """
        execution_order = self.graph.get_execution_order()
        levels = self.graph.get_levels()

        return {
            "total_stories": len(self.graph.nodes),
            "execution_order": execution_order,
            "levels": levels,
            "total_levels": len(levels),
            "max_parallelism": max(len(level) for level in levels) if levels else 0,
            "stories_without_dependencies": [
                story for story in self.graph.nodes
                if not self.graph.get_dependencies(story)
            ],
            "stories_without_dependents": [
                story for story in self.graph.nodes
                if not self.graph.get_dependents(story)
            ],
        }

    def to_json_graph(self) -> Dict[str, object]:
        """Generate JSON-serializable graph structure.

        Returns:
            Dictionary representing the graph structure
        """
        nodes = [
            {
                "id": story,
                "dependencies": self.graph.get_dependencies(story),
                "dependents": self.graph.get_dependents(story),
            }
            for story in sorted(self.graph.nodes)
        ]

        return {
            "nodes": nodes,
            "edges": [
                {"from": dep, "to": story}
                for story in self.graph.nodes
                for dep in self.graph.get_dependencies(story)
            ],
        }
