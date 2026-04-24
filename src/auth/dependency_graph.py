"""Dependency graph management for story execution order."""

from collections import defaultdict, deque
from typing import Dict, List, Set, Tuple


class DependencyGraph:
    """Manages dependencies between stories and determines execution order."""

    def __init__(self) -> None:
        """Initialize an empty dependency graph."""
        self.graph: Dict[str, List[str]] = defaultdict(list)
        self.reverse_graph: Dict[str, List[str]] = defaultdict(list)
        self.nodes: Set[str] = set()

    def add_story(self, story_id: str) -> None:
        """Add a story to the graph.

        Args:
            story_id: Unique identifier for the story
        """
        self.nodes.add(story_id)
        if story_id not in self.graph:
            self.graph[story_id] = []
        if story_id not in self.reverse_graph:
            self.reverse_graph[story_id] = []

    def add_dependency(self, story_id: str, depends_on: str) -> None:
        """Add a dependency relationship between stories.

        Args:
            story_id: Story that has a dependency
            depends_on: Story that must be completed first

        Raises:
            ValueError: If adding dependency would create a cycle
        """
        self.add_story(story_id)
        self.add_story(depends_on)

        # Check for cycle before adding
        if self._would_create_cycle(story_id, depends_on):
            raise ValueError(f"Adding dependency {story_id} -> {depends_on} would create a cycle")

        self.graph[depends_on].append(story_id)
        self.reverse_graph[story_id].append(depends_on)

    def _would_create_cycle(self, from_node: str, to_node: str) -> bool:
        """Check if adding an edge would create a cycle.

        Args:
            from_node: Source node
            to_node: Destination node

        Returns:
            True if cycle would be created, False otherwise
        """
        visited: Set[str] = set()
        queue = deque([to_node])

        while queue:
            current = queue.popleft()
            if current == from_node:
                return True
            if current in visited:
                continue
            visited.add(current)
            queue.extend(self.graph.get(current, []))

        return False

    def get_execution_order(self) -> List[str]:
        """Calculate topological sort for story execution order.

        Returns:
            List of story IDs in execution order

        Raises:
            ValueError: If graph contains cycles
        """
        in_degree = {node: len(self.reverse_graph[node]) for node in self.nodes}
        queue = deque([node for node in self.nodes if in_degree[node] == 0])
        result: List[str] = []

        while queue:
            current = queue.popleft()
            result.append(current)

            for neighbor in self.graph[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(result) != len(self.nodes):
            raise ValueError("Graph contains cycles")

        return result

    def get_dependencies(self, story_id: str) -> List[str]:
        """Get direct dependencies for a story.

        Args:
            story_id: Story identifier

        Returns:
            List of story IDs that must be completed first
        """
        return self.reverse_graph.get(story_id, [])

    def get_dependents(self, story_id: str) -> List[str]:
        """Get stories that depend on this story.

        Args:
            story_id: Story identifier

        Returns:
            List of story IDs that depend on this story
        """
        return self.graph.get(story_id, [])

    def get_levels(self) -> List[List[str]]:
        """Group stories by execution level.

        Returns:
            List of levels, each containing stories that can be executed in parallel
        """
        in_degree = {node: len(self.reverse_graph[node]) for node in self.nodes}
        levels: List[List[str]] = []

        while any(degree == 0 for degree in in_degree.values()):
            current_level = [node for node in self.nodes if in_degree[node] == 0]
            levels.append(sorted(current_level))

            for node in current_level:
                in_degree[node] = -1
                for neighbor in self.graph[node]:
                    in_degree[neighbor] -= 1

        return levels
