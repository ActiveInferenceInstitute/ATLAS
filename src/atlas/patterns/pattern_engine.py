"""
PatternEngine - Advanced pattern management and analysis for ATLAS.

The PatternEngine provides sophisticated pattern matching, inheritance,
and analysis capabilities for the ATLAS pattern language system.
"""

import logging
from typing import Dict, List, Any, Set, Tuple, FrozenSet
from collections import defaultdict
import networkx as nx

from .pattern import Pattern

logger = logging.getLogger(__name__)


class PatternEngine:
    """
    Advanced pattern management and analysis engine.

    The PatternEngine provides pattern matching, inheritance analysis,
    pattern discovery, and optimization capabilities for ATLAS patterns.
    """

    def __init__(self):
        """Initialize the PatternEngine."""
        self.patterns: Dict[str, Pattern] = {}
        self.pattern_graph = nx.DiGraph()

        # Pattern analysis caches
        self._inheritance_cache: Dict[str, Set[str]] = {}
        self._similarity_cache: Dict[
            Tuple[str, str], Tuple[Tuple[FrozenSet[str], ...], float]
        ] = {}

        # Pattern discovery state
        self.pattern_clusters: Dict[str, Set[str]] = defaultdict(set)
        self.emerging_patterns: List[Dict[str, Any]] = []

        logger.info("PatternEngine initialized")

    def add_pattern(self, pattern: Pattern) -> bool:
        """
        Add a pattern to the engine.

        Args:
            pattern: Pattern instance to add

        Returns:
            True if pattern was added successfully
        """
        try:
            self.patterns[pattern.id] = pattern

            self._reconcile_hierarchy()
            self._clear_caches()

            logger.info(f"Added pattern {pattern.id} to engine")
            return True

        except Exception as e:
            logger.error(f"Failed to add pattern {pattern.id}: {e}")
            return False

    def remove_pattern(self, pattern_id: str) -> bool:
        """Remove a pattern from the engine."""
        try:
            if pattern_id in self.patterns:
                del self.patterns[pattern_id]

                self._reconcile_hierarchy()
                self._clear_caches()

                logger.info(f"Removed pattern {pattern_id} from engine")
                return True
            return False

        except Exception as e:
            logger.error(f"Failed to remove pattern {pattern_id}: {e}")
            return False

    def _reconcile_hierarchy(self) -> None:
        """Reconcile current declarations without rewriting their owners."""
        edges = set()
        for pattern_id, pattern in self.patterns.items():
            edges.update(
                (parent_id, pattern_id)
                for parent_id in pattern.parents if parent_id in self.patterns
            )
            edges.update(
                (pattern_id, child_id)
                for child_id in pattern.children if child_id in self.patterns
            )

        current_edges = set(self.pattern_graph.edges())
        topology_changed = (
            set(self.pattern_graph) != set(self.patterns)
            or current_edges != edges
        )
        self.pattern_graph.remove_nodes_from(
            set(self.pattern_graph) - self.patterns.keys()
        )
        for pattern_id, pattern in self.patterns.items():
            self.pattern_graph.add_node(pattern_id, pattern=pattern)
        self.pattern_graph.remove_edges_from(current_edges - edges)
        self.pattern_graph.add_edges_from(
            edges - current_edges, relation='parent_of'
        )
        if topology_changed:
            self._clear_caches()

    def get_pattern_hierarchy_graph(self) -> nx.DiGraph:
        """Return detached effective topology for current registered patterns.

        Each record owns its parents/children declarations. Missing endpoints
        remain in those lists until registered; they do not create graph nodes.
        Direct list edits are reconciled here and at other analysis boundaries.
        Pattern objects in node attributes remain the registered live objects.
        """
        self._reconcile_hierarchy()
        return self.pattern_graph.copy()

    def get_pattern_hierarchy(self, pattern_id: str) -> Dict[str, Set[str]]:
        """
        Get the complete hierarchy for a pattern.

        Args:
            pattern_id: Pattern identifier

        Returns:
            Dictionary with 'ancestors' and 'descendants' sets
        """
        try:
            self._reconcile_hierarchy()
            if pattern_id not in self.patterns:
                return {'ancestors': set(), 'descendants': set()}

            if pattern_id not in self._inheritance_cache:
                self._inheritance_cache[pattern_id] = nx.ancestors(
                    self.pattern_graph, pattern_id
                )
            return {
                'ancestors': set(self._inheritance_cache[pattern_id]),
                'descendants': nx.descendants(self.pattern_graph, pattern_id)
            }

        except Exception as e:
            logger.error(
                f"Failed to get hierarchy for pattern {pattern_id}: {e}"
            )
            return {'ancestors': set(), 'descendants': set()}

    def calculate_pattern_similarity(
        self, pattern1_id: str, pattern2_id: str
    ) -> float:
        """
        Calculate similarity between two patterns.

        Args:
            pattern1_id: First pattern identifier
            pattern2_id: Second pattern identifier

        Returns:
            Similarity score between 0.0 and 1.0
        """
        self._reconcile_hierarchy()
        # Handle self-similarity case
        if pattern1_id == pattern2_id:
            return 1.0

        if (
            pattern1_id not in self.patterns
            or pattern2_id not in self.patterns
        ):
            return 0.0

        try:
            cache_key = tuple(sorted((pattern1_id, pattern2_id)))
            pattern1 = self.patterns[cache_key[0]]
            pattern2 = self.patterns[cache_key[1]]

            # Snapshot every mutable input before accepting a cached score.
            qkit1_set = frozenset(pattern1.qkit)
            qkit2_set = frozenset(pattern2.qkit)
            attrs1_keys = frozenset(pattern1.attributes)
            attrs2_keys = frozenset(pattern2.attributes)
            hier1 = self.get_pattern_hierarchy(cache_key[0])
            hier2 = self.get_pattern_hierarchy(cache_key[1])
            inputs = (
                qkit1_set, qkit2_set, attrs1_keys, attrs2_keys,
                frozenset(hier1['ancestors']), frozenset(hier2['ancestors'])
            )
            cached = self._similarity_cache.get(cache_key)
            if cached is not None and cached[0] == inputs:
                return cached[1]

            # QKit similarity
            qkit_intersection = len(qkit1_set & qkit2_set)
            qkit_union = len(qkit1_set | qkit2_set)
            qkit_similarity = (
                qkit_intersection / qkit_union if qkit_union > 0 else 1.0
            )

            # Attribute similarity
            attr_intersection = len(attrs1_keys & attrs2_keys)
            attr_union = len(attrs1_keys | attrs2_keys)
            attr_similarity = (
                attr_intersection / attr_union if attr_union > 0 else 1.0
            )

            # Hierarchy similarity
            hier_intersection = len(hier1['ancestors'] & hier2['ancestors'])
            hier_union = len(hier1['ancestors'] | hier2['ancestors'])
            hier_similarity = (
                hier_intersection / hier_union if hier_union > 0 else 1.0
            )

            # Weighted average
            similarity = (
                0.5 * qkit_similarity
                + 0.3 * attr_similarity
                + 0.2 * hier_similarity
            )

            # Cache result
            self._similarity_cache[cache_key] = (inputs, similarity)

            return similarity

        except Exception as e:
            logger.error(
                f"Failed to calculate similarity between {pattern1_id} and "
                f"{pattern2_id}: {e}"
            )
            return 0.0

    def find_similar_patterns(
        self, pattern_id: str, threshold: float = 0.7
    ) -> List[Tuple[str, float]]:
        """
        Find patterns similar to the given pattern.

        Args:
            pattern_id: Pattern to find similarities for
            threshold: Minimum similarity threshold

        Returns:
            List of (pattern_id, similarity_score) tuples
        """
        self._reconcile_hierarchy()
        if pattern_id not in self.patterns:
            return []

        similar_patterns = []

        for other_id in self.patterns:
            if other_id != pattern_id:
                similarity = self.calculate_pattern_similarity(
                    pattern_id, other_id
                )
                if similarity >= threshold:
                    similar_patterns.append((other_id, similarity))

        # Sort by similarity descending
        similar_patterns.sort(key=lambda x: x[1], reverse=True)

        return similar_patterns

    def detect_pattern_clusters(
        self, similarity_threshold: float = 0.6
    ) -> Dict[str, Set[str]]:
        """
        Detect clusters of similar patterns.

        Args:
            similarity_threshold: Minimum similarity for clustering

        Returns:
            Dictionary mapping cluster IDs to sets of pattern IDs
        """
        try:
            self._reconcile_hierarchy()
            # Create similarity graph
            similarity_graph = nx.Graph()
            similarity_graph.add_nodes_from(self.patterns.keys())

            # Add edges for similar patterns
            for pattern1_id in self.patterns:
                for pattern2_id in self.patterns:
                    if pattern1_id < pattern2_id:  # Avoid duplicates
                        similarity = self.calculate_pattern_similarity(
                            pattern1_id, pattern2_id
                        )
                        if similarity >= similarity_threshold:
                            similarity_graph.add_edge(
                                pattern1_id, pattern2_id, weight=similarity
                            )

            # Find connected components as clusters
            clusters = {}
            for i, component in enumerate(
                nx.connected_components(similarity_graph)
            ):
                cluster_id = f"cluster_{i}"
                clusters[cluster_id] = component

            self.pattern_clusters = clusters
            return clusters

        except Exception as e:
            logger.error(f"Failed to detect pattern clusters: {e}")
            return {}

    def suggest_pattern_merges(
        self, similarity_threshold: float = 0.8
    ) -> List[Dict[str, Any]]:
        """
        Suggest pattern merges based on high similarity.

        Args:
            similarity_threshold: Minimum similarity for merge suggestion

        Returns:
            List of merge suggestions with pattern pairs and reasons
        """
        self._reconcile_hierarchy()
        suggestions = []

        for pattern1_id in self.patterns:
            similar = self.find_similar_patterns(
                pattern1_id, similarity_threshold
            )
            for pattern2_id, similarity in similar:
                if pattern1_id < pattern2_id:  # Avoid duplicates
                    suggestion = {
                        'pattern1': pattern1_id,
                        'pattern2': pattern2_id,
                        'similarity': similarity,
                        'reason': (
                            f"High similarity ({similarity:.2f}) suggests "
                            "potential merge"
                        ),
                        'common_qkit': list(
                            set(self.patterns[pattern1_id].qkit)
                            & set(self.patterns[pattern2_id].qkit)
                        ),
                        'common_attributes': list(
                            set(self.patterns[pattern1_id].attributes.keys())
                            & set(self.patterns[pattern2_id].attributes.keys())
                        )
                    }
                    suggestions.append(suggestion)

        return suggestions

    def analyze_pattern_usage(self) -> Dict[str, Any]:
        """
        Analyze pattern usage across the system.

        Returns:
            Dictionary with usage statistics and insights
        """
        try:
            self._reconcile_hierarchy()
            total_patterns = len(self.patterns)
            total_usage = sum(
                pattern.usage_count for pattern in self.patterns.values()
            )

            # Most used patterns
            most_used = sorted(
                [(pid, p.usage_count) for pid, p in self.patterns.items()],
                key=lambda x: x[1], reverse=True
            )[:10]

            # Least used patterns
            least_used = sorted(
                [(pid, p.usage_count) for pid, p in self.patterns.items()],
                key=lambda x: x[1]
            )[:10]

            # Orphaned patterns (no parents or children)
            orphaned = [
                pid for pid in self.patterns
                if self.pattern_graph.degree(pid) == 0
            ]

            # Root patterns (no parents)
            root_patterns = [
                pid for pid in self.patterns
                if self.pattern_graph.in_degree(pid) == 0
            ]

            # Leaf patterns (no children)
            leaf_patterns = [
                pid for pid in self.patterns
                if self.pattern_graph.out_degree(pid) == 0
            ]
            hierarchy_depth = (
                nx.dag_longest_path_length(self.pattern_graph)
                if nx.is_directed_acyclic_graph(self.pattern_graph) else None
            )

            return {
                'total_patterns': total_patterns,
                'total_usage': total_usage,
                'average_usage': (
                    total_usage / total_patterns if total_patterns > 0 else 0
                ),
                'most_used_patterns': most_used,
                'least_used_patterns': least_used,
                'orphaned_patterns': orphaned,
                'root_patterns': root_patterns,
                'leaf_patterns': leaf_patterns,
                'hierarchy_depth': hierarchy_depth
            }

        except Exception as e:
            logger.error(f"Failed to analyze pattern usage: {e}")
            return {}

    def optimize_pattern_hierarchy(self) -> List[Dict[str, Any]]:
        """
        Suggest optimizations for the pattern hierarchy.

        Returns:
            List of optimization suggestions
        """
        suggestions = []

        try:
            self._reconcile_hierarchy()
            # Detect cycles
            if not nx.is_directed_acyclic_graph(self.pattern_graph):
                cycles = list(nx.simple_cycles(self.pattern_graph))
                for cycle in cycles:
                    suggestions.append({
                        'type': 'cycle_detected',
                        'patterns': cycle,
                        'priority': 'high',
                        'description': (
                            f"Circular dependency detected: "
                            f"{' -> '.join(cycle)}"
                        )
                    })

            # Exclude each edge in a read-only view, then look for a real
            # alternate path. Starting with a successor also handles self-loops
            # without mistaking the zero-length path for an alternative.
            for parent_id, pattern_id in self.pattern_graph.edges():
                alternate = nx.restricted_view(
                    self.pattern_graph, [], [(parent_id, pattern_id)]
                )
                if any(
                    nx.has_path(alternate, successor, pattern_id)
                    for successor in alternate.successors(parent_id)
                ):
                    suggestions.append({
                        'type': 'redundant_relationship',
                        'pattern': pattern_id,
                        'parent': parent_id,
                        'priority': 'medium',
                        'description': (
                            f"Direct parent {parent_id} is also "
                            "indirect ancestor"
                        )
                    })

            # Find isolated patterns
            for pattern_id in self.patterns:
                if (
                    self.pattern_graph.in_degree(pattern_id) == 0
                    and self.pattern_graph.out_degree(pattern_id) == 0
                ):
                    suggestions.append({
                        'type': 'isolated_pattern',
                        'pattern': pattern_id,
                        'priority': 'low',
                        'description': (
                            f"Pattern {pattern_id} has no relationships"
                        )
                    })

            return suggestions

        except Exception as e:
            logger.error(f"Failed to optimize pattern hierarchy: {e}")
            return []

    def _clear_caches(self) -> None:
        """Clear internal caches."""
        self._inheritance_cache.clear()
        self._similarity_cache.clear()

    def get_statistics(self) -> Dict[str, Any]:
        """Get engine statistics."""
        self._reconcile_hierarchy()
        return {
            'pattern_count': len(self.patterns),
            'graph_nodes': self.pattern_graph.number_of_nodes(),
            'graph_edges': self.pattern_graph.number_of_edges(),
            'cache_sizes': {
                'inheritance': len(self._inheritance_cache),
                'similarity': len(self._similarity_cache)
            },
            'cluster_count': len(self.pattern_clusters),
            'emerging_patterns': len(self.emerging_patterns)
        }