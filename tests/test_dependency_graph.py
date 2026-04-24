"""Tests for dependency graph management."""

import pytest
from src.auth.dependency_graph import DependencyGraph


class TestDependencyGraph:
    """Test cases for DependencyGraph class."""

    def test_add_story(self) -> None:
        """Test adding stories to the graph."""
        graph = DependencyGraph()
        graph.add_story("STORY-1")
        assert "STORY-1" in graph.nodes

    def test_add_dependency(self) -> None:
        """Test adding dependency relationships."""
        graph = DependencyGraph()
        graph.add_dependency("STORY-2", "STORY-1")
        assert "STORY-1" in graph.get_dependencies("STORY-2")
        assert "STORY-2" in graph.get_dependents("STORY-1")

    def test_execution_order_simple(self) -> None:
        """Test execution order for simple dependency chain."""
        graph = DependencyGraph()
        graph.add_dependency("STORY-2", "STORY-1")
        graph.add_dependency("STORY-3", "STORY-2")

        order = graph.get_execution_order()
        assert order.index("STORY-1") < order.index("STORY-2")
        assert order.index("STORY-2") < order.index("STORY-3")

    def test_execution_order_parallel(self) -> None:
        """Test execution order with parallel stories."""
        graph = DependencyGraph()
        graph.add_dependency("STORY-2", "STORY-1")
        graph.add_dependency("STORY-3", "STORY-1")
        graph.add_dependency("STORY-4", "STORY-2")
        graph.add_dependency("STORY-4", "STORY-3")

        order = graph.get_execution_order()
        assert order[0] == "STORY-1"
        assert order[-1] == "STORY-4"
        assert "STORY-2" in order and "STORY-3" in order

    def test_cycle_detection(self) -> None:
        """Test that cycles are detected and prevented."""
        graph = DependencyGraph()
        graph.add_dependency("STORY-2", "STORY-1")
        graph.add_dependency("STORY-3", "STORY-2")

        with pytest.raises(ValueError, match="cycle"):
            graph.add_dependency("STORY-1", "STORY-3")

    def test_get_levels(self) -> None:
        """Test grouping stories by execution level."""
        graph = DependencyGraph()
        graph.add_dependency("STORY-2", "STORY-1")
        graph.add_dependency("STORY-3", "STORY-1")
        graph.add_dependency("STORY-4", "STORY-2")

        levels = graph.get_levels()
        assert levels[0] == ["STORY-1"]
        assert set(levels[1]) == {"STORY-2", "STORY-3"}
        assert levels[2] == ["STORY-4"]

    def test_empty_graph(self) -> None:
        """Test operations on empty graph."""
        graph = DependencyGraph()
        assert graph.get_execution_order() == []
        assert graph.get_levels() == []

    def test_single_story(self) -> None:
        """Test graph with single story."""
        graph = DependencyGraph()
        graph.add_story("STORY-1")
        assert graph.get_execution_order() == ["STORY-1"]
        assert graph.get_levels() == [["STORY-1"]]

    def test_get_dependencies_nonexistent(self) -> None:
        """Test getting dependencies for nonexistent story."""
        graph = DependencyGraph()
        assert graph.get_dependencies("NONEXISTENT") == []

    def test_complex_graph(self) -> None:
        """Test complex dependency graph."""
        graph = DependencyGraph()
        graph.add_dependency("B", "A")
        graph.add_dependency("C", "A")
        graph.add_dependency("D", "B")
        graph.add_dependency("D", "C")
        graph.add_dependency("E", "D")
        graph.add_story("F")

        order = graph.get_execution_order()
        assert len(order) == 6
        assert order.index("A") < order.index("B")
        assert order.index("B") < order.index("D")
        assert order.index("C") < order.index("D")
        assert order.index("D") < order.index("E")
