"""Tests for dependency visualization."""

import pytest
from src.auth.dependency_graph import DependencyGraph
from src.auth.dependency_visualizer import DependencyVisualizer


class TestDependencyVisualizer:
    """Test cases for DependencyVisualizer class."""

    @pytest.fixture
    def simple_graph(self) -> DependencyGraph:
        """Create a simple dependency graph for testing."""
        graph = DependencyGraph()
        graph.add_dependency("STORY-2", "STORY-1")
        graph.add_dependency("STORY-3", "STORY-2")
        return graph

    @pytest.fixture
    def complex_graph(self) -> DependencyGraph:
        """Create a complex dependency graph for testing."""
        graph = DependencyGraph()
        graph.add_dependency("B", "A")
        graph.add_dependency("C", "A")
        graph.add_dependency("D", "B")
        graph.add_dependency("D", "C")
        return graph

    def test_to_ascii(self, simple_graph: DependencyGraph) -> None:
        """Test ASCII visualization."""
        visualizer = DependencyVisualizer(simple_graph)
        ascii_output = visualizer.to_ascii()
        assert "Level 1:" in ascii_output
        assert "STORY-1" in ascii_output
        assert "no dependencies" in ascii_output

    def test_to_mermaid(self, simple_graph: DependencyGraph) -> None:
        """Test Mermaid diagram generation."""
        visualizer = DependencyVisualizer(simple_graph)
        mermaid = visualizer.to_mermaid()
        assert "graph TD" in mermaid
        assert "STORY-1 --> STORY-2" in mermaid
        assert "STORY-2 --> STORY-3" in mermaid

    def test_to_dot(self, simple_graph: DependencyGraph) -> None:
        """Test DOT format generation."""
        visualizer = DependencyVisualizer(simple_graph)
        dot = visualizer.to_dot()
        assert "digraph Dependencies" in dot
        assert '"STORY-1" -> "STORY-2"' in dot
        assert '"STORY-2" -> "STORY-3"' in dot

    def test_execution_summary(self, complex_graph: DependencyGraph) -> None:
        """Test execution summary generation."""
        visualizer = DependencyVisualizer(complex_graph)
        summary = visualizer.get_execution_summary()

        assert summary["total_stories"] == 4
        assert summary["total_levels"] == 3
        assert summary["max_parallelism"] == 2
        assert "A" in summary["stories_without_dependencies"]
        assert "D" in summary["stories_without_dependents"]

    def test_to_json_graph(self, simple_graph: DependencyGraph) -> None:
        """Test JSON graph structure generation."""
        visualizer = DependencyVisualizer(simple_graph)
        json_graph = visualizer.to_json_graph()

        assert "nodes" in json_graph
        assert "edges" in json_graph
        assert len(json_graph["nodes"]) == 3
        assert len(json_graph["edges"]) == 2

    def test_empty_graph_visualization(self) -> None:
        """Test visualization of empty graph."""
        graph = DependencyGraph()
        visualizer = DependencyVisualizer(graph)

        summary = visualizer.get_execution_summary()
        assert summary["total_stories"] == 0
        assert summary["total_levels"] == 0

    def test_parallel_execution_levels(self, complex_graph: DependencyGraph) -> None:
        """Test that parallel execution is correctly identified."""
        visualizer = DependencyVisualizer(complex_graph)
        summary = visualizer.get_execution_summary()

        levels = summary["levels"]
        assert len(levels[1]) == 2  # B and C can run in parallel
        assert set(levels[1]) == {"B", "C"}
