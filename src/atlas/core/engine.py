"""
ATLAS Engine - Core orchestration system for the ATLAS framework.

The ATLASEngine manages entities, patterns, queries, and provides the main
interface for interacting with the ATLAS knowledge management system.
"""

import copy
import json
import logging
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Dict, List, Optional

import networkx as nx

# Configure logging
logging.basicConfig(
    level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)


@dataclass
class ATLASConfig:
    """Configuration settings for ATLAS engine."""
    auto_pattern_inference: bool = True
    enable_dynamic_typing: bool = True
    max_expansion_depth: int = 10
    enable_quality_metrics: bool = True
    log_level: str = "INFO"


class ATLASEngine:
    """
    Core ATLAS engine that orchestrates all system components.

    The ATLASEngine provides a unified interface for managing entities,
    patterns, queries, and their relationships within the ATLAS framework.
    """

    def __init__(self, config: Optional[ATLASConfig] = None):
        """Initialize the ATLAS engine."""
        self.config = config or ATLASConfig()
        self.graph = nx.DiGraph()

        # Component registries
        self.entities: Dict[str, Any] = {}
        self.patterns: Dict[str, Any] = {}
        self.queries: Dict[str, Any] = {}
        self.attributes: Dict[str, Any] = {}
        self.interfaces: Dict[str, Any] = {}

        # Explicit calls remain ordered and mutable; declarations are separate.
        self.relationships: Dict[str, List[tuple]] = defaultdict(list)
        self._owned_relationships: Dict[str, List[tuple]] = {}
        self._managed_edges = set()
        self._declared_edges = {}

        # Performance and quality metrics
        self.metrics = {
            'entities_created': 0,
            'patterns_created': 0,
            'queries_executed': 0,
            'relationships_added': 0
        }

        logger.info("ATLAS Engine initialized with config: %s", self.config)

    def _replace_node(self, node_id: str, node_type: str,
                      data: Dict[str, Any]) -> None:
        """Replace record attributes without removing incident edges."""
        attrs = dict(data)
        attrs['node_type'] = node_type
        self.graph.add_node(node_id)
        self.graph.nodes[node_id].clear()
        self.graph.nodes[node_id].update(attrs)

    def reconcile_graph(self) -> nx.DiGraph:
        """Refresh effective relationships from current mutable records.

        ``relationships`` on an edge is an ordered list of occurrence dicts.
        One declaration occurrence represents the union of authored hierarchy
        declarations; every explicit call, including repeats, follows it.
        The legacy ``relationship_type`` is the last explicit type, or
        ``parent_of`` on a declaration-only edge.
        """
        for node_type, registry in (
            ('entity', self.entities), ('pattern', self.patterns),
            ('query', self.queries),
        ):
            for node_id, data in registry.items():
                if node_id not in self.graph:
                    self._replace_node(node_id, node_type, data)

        declared = {}
        for pattern_id, data in self.patterns.items():
            for key in ('parents', 'children'):
                if key in data:
                    self.graph.nodes[pattern_id][key] = data[key]
                else:
                    self.graph.nodes[pattern_id].pop(key, None)
            for parent in data.get('parents', []):
                if parent in self.graph:
                    declared[parent, pattern_id] = None
            for child in data.get('children', []):
                if child in self.graph:
                    declared[pattern_id, child] = None

        occurrences = {}
        for edge in declared:
            occurrences[edge] = [
                {'relationship_type': 'parent_of', 'origin': 'declaration'}
            ]
        for owner, relationships in self._owned_relationships.items():
            for source, target, relationship_type in relationships:
                if source in self.graph and target in self.graph:
                    occurrences.setdefault((source, target), []).append({
                        'relationship_type': relationship_type,
                        'origin': 'owned',
                        'owner': owner,
                    })
        for source, relationships in self.relationships.items():
            for target, relationship_type in relationships:
                if source in self.graph and target in self.graph:
                    occurrences.setdefault((source, target), []).append({
                        'relationship_type': relationship_type,
                        'origin': 'explicit',
                    })

        for edge in self._managed_edges - occurrences.keys():
            if self.graph.has_edge(*edge):
                self.graph.remove_edge(*edge)
        for (source, target), records in occurrences.items():
            self.graph.add_edge(
                source, target, relationships=records,
                relationship_type=records[-1]['relationship_type'],
            )
        self._managed_edges = set(occurrences)
        self._declared_edges = declared
        return self.graph

    def replace_owned_relationships(self, owner: str,
                                    relationships: List[tuple]) -> bool:
        """Replace one source's triples without withdrawing manual calls.

        All endpoints must exist. Refusal leaves the previous owned set intact.
        An empty list withdraws this owner's occurrences only.
        """
        records = list(relationships)
        if any(
            source not in self.graph or target not in self.graph
            for source, target, _ in records
        ):
            return False
        if records:
            self._owned_relationships[owner] = records
        else:
            self._owned_relationships.pop(owner, None)
        self.reconcile_graph()
        return True

    def get_pattern_hierarchy_graph(self) -> nx.DiGraph:
        """Return a detached effective hierarchy of registered patterns."""
        self.reconcile_graph()
        hierarchy = nx.DiGraph()
        hierarchy.add_nodes_from(self.patterns)
        for source, target, data in self.graph.edges(data=True):
            if source not in self.patterns or target not in self.patterns:
                continue
            records = data.get('relationships', [data])
            if any(r.get('relationship_type') == 'parent_of' for r in records):
                hierarchy.add_edge(source, target)
        return hierarchy

    def add_entity(self, entity_id: str, entity_data: Dict[str, Any]) -> bool:
        """
        Add an entity to the ATLAS system.

        Args:
            entity_id: Unique identifier for the entity
            entity_data: Entity data including attributes and patterns

        Returns:
            True if entity was added successfully, False otherwise
        """
        try:
            if entity_id in self.entities:
                logger.warning(
                    "Entity %s already exists, updating...", entity_id,
                )

            self._replace_node(entity_id, 'entity', entity_data)
            self.entities[entity_id] = entity_data
            self.reconcile_graph()

            # Update metrics
            self.metrics['entities_created'] += 1

            logger.info(f"Added entity: {entity_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to add entity {entity_id}: {e}")
            return False

    def add_pattern(
        self, pattern_id: str, pattern_data: Dict[str, Any],
    ) -> bool:
        """
        Add a pattern to the ATLAS system.

        Args:
            pattern_id: Unique identifier for the pattern
            pattern_data: Pattern data including qkit, parents, children

        Returns:
            True if pattern was added successfully, False otherwise
        """
        try:
            if pattern_id in self.patterns:
                logger.warning(
                    "Pattern %s already exists, updating...", pattern_id,
                )

            self._replace_node(pattern_id, 'pattern', pattern_data)
            self.patterns[pattern_id] = pattern_data
            self.reconcile_graph()

            # Update metrics
            self.metrics['patterns_created'] += 1

            logger.info(f"Added pattern: {pattern_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to add pattern {pattern_id}: {e}")
            return False

    def add_query(self, query_id: str, query_data: Dict[str, Any]) -> bool:
        """
        Add an iQuery to the ATLAS system.

        Args:
            query_id: Unique identifier for the query
            query_data: Query data including ref_id and prompts

        Returns:
            True if query was added successfully, False otherwise
        """
        try:
            if query_id in self.queries:
                logger.warning(f"Query {query_id} already exists, updating...")

            self._replace_node(query_id, 'query', query_data)
            self.queries[query_id] = query_data
            self.reconcile_graph()

            logger.info(f"Added query: {query_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to add query {query_id}: {e}")
            return False

    def add_relationship(
        self, source_id: str, target_id: str, relationship_type: str,
    ) -> bool:
        """
        Add a relationship between two nodes in the ATLAS system.

        Args:
            source_id: Source node identifier
            target_id: Target node identifier
            relationship_type: Type of relationship

        Returns:
            True if relationship was added successfully, False otherwise
        """
        try:
            self.reconcile_graph()
            if source_id not in self.graph or target_id not in self.graph:
                logger.warning(
                    "Relationship endpoints not found: %s -> %s",
                    source_id, target_id,
                )
                return False

            self.relationships[source_id].append(
                (target_id, relationship_type),
            )
            self.reconcile_graph()

            # Update metrics
            self.metrics['relationships_added'] += 1

            logger.info(
                "Added relationship: %s --[%s]--> %s",
                source_id, relationship_type, target_id,
            )
            return True

        except Exception as e:
            logger.error(
                "Failed to add relationship %s -> %s: %s",
                source_id, target_id, e,
            )
            return False

    def query(
        self, query_string: str, context: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Execute a query against the ATLAS system.

        Args:
            query_string: Query to execute
            context: Optional context for the query

        Returns:
            List of results matching the query
        """
        try:
            # Update metrics
            self.metrics['queries_executed'] += 1

            # Keyword matching over each registered record.
            results = []

            # Search entities
            for entity_id, entity_data in self.entities.items():
                if self._matches_query(entity_data, query_string):
                    results.append({
                        'id': entity_id,
                        'type': 'entity',
                        'data': entity_data,
                        'relevance_score': self._calculate_relevance(
                            entity_data, query_string,
                        ),
                    })

            # Search patterns
            for pattern_id, pattern_data in self.patterns.items():
                if self._matches_query(pattern_data, query_string):
                    results.append({
                        'id': pattern_id,
                        'type': 'pattern',
                        'data': pattern_data,
                        'relevance_score': self._calculate_relevance(
                            pattern_data, query_string,
                        ),
                    })

            # Search queries
            for query_id, query_data in self.queries.items():
                if self._matches_query(query_data, query_string):
                    results.append({
                        'id': query_id,
                        'type': 'query',
                        'data': query_data,
                        'relevance_score': self._calculate_relevance(
                            query_data, query_string,
                        ),
                    })

            # Sort by relevance score
            results.sort(
                key=lambda x: x.get('relevance_score', 0), reverse=True,
            )

            logger.info(
                "Query '%s' returned %s results", query_string, len(results),
            )
            return results

        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            return []

    def _matches_query(
        self, data: Dict[str, Any], query_string: str, max_depth: int = 10,
    ) -> bool:
        """Enhanced query matching logic with recursion protection."""
        query_lower = query_string.lower()
        query_words = query_lower.split()

        # Convert data to searchable text with depth limiting
        searchable_text = ""

        def extract_text(obj: Any, depth: int = 0) -> str:
            """Extract searchable text with a bounded recursion depth."""
            if depth > max_depth:
                return ""

            if isinstance(obj, str):
                return obj.lower() + " "
            elif isinstance(obj, (list, tuple)):
                if len(obj) > 100:  # Limit large collections
                    obj = obj[:100]
                return " ".join(extract_text(item, depth + 1) for item in obj)
            elif isinstance(obj, dict):
                if len(obj) > 50:  # Limit large dictionaries
                    limited_obj = dict(list(obj.items())[:50])
                else:
                    limited_obj = obj
                return " ".join(
                    extract_text(v, depth + 1) for v in limited_obj.values()
                )
            elif hasattr(obj, '__dict__'):
                # Handle objects with attributes, but limit depth
                if depth < max_depth - 2:
                    return extract_text(obj.__dict__, depth + 1)
                else:
                    return str(obj).lower() + " "
            else:
                return str(obj).lower() + " "

        try:
            # Extract all text from data
            searchable_text = extract_text(data)

            # Check if all query words are present
            if all(word in searchable_text for word in query_words):
                return True

            # Check for exact phrase match
            if query_lower in searchable_text:
                return True

            # Check individual keys for exact matches
            for key in data.keys():
                if query_lower == key.lower():
                    return True

            return False

        except RecursionError:
            logger.warning(
                "Recursion detected in query matching: %s", query_string,
            )
            # Fallback to simple string matching
            data_str = str(data).lower()
            return any(word in data_str for word in query_words)
        except Exception as e:
            logger.error(f"Error in query matching: {e}")
            return False

    def _calculate_relevance(
        self, data: Dict[str, Any], query_string: str,
    ) -> float:
        """Calculate relevance score for search results."""
        query_lower = query_string.lower()
        score = 0.0

        for key, value in data.items():
            if isinstance(value, str):
                # Exact match gets higher score
                if query_lower == value.lower():
                    score += 1.0
                elif query_lower in value.lower():
                    score += 0.5

            # Key match
            if query_lower == key.lower():
                score += 0.3
            elif query_lower in key.lower():
                score += 0.1

        return score

    def get_node(self, node_id: str) -> Optional[Dict[str, Any]]:
        """Get a node by its ID."""
        try:
            if node_id in self.entities:
                return {'type': 'entity', 'data': self.entities[node_id]}
            elif node_id in self.patterns:
                return {'type': 'pattern', 'data': self.patterns[node_id]}
            elif node_id in self.queries:
                return {'type': 'query', 'data': self.queries[node_id]}
            return None
        except Exception as e:
            logger.error(f"Failed to get node {node_id}: {e}")
            return None

    def get_relationships(
        self, node_id: str, relationship_type: Optional[str] = None,
    ) -> List[tuple]:
        """Return explicit occurrences and effective hierarchy declarations."""
        try:
            self.reconcile_graph()
            relationships = list(self.relationships.get(node_id, []))
            relationships.extend(
                (target, rtype)
                for records in self._owned_relationships.values()
                for source, target, rtype in records if source == node_id
            )
            relationships.extend(
                (target, 'parent_of')
                for source, target in self._declared_edges if source == node_id
            )
            if relationship_type:
                return [
                    (target, rtype) for target, rtype in relationships
                    if rtype == relationship_type
                ]
            return relationships
        except Exception as e:
            logger.error(f"Failed to get relationships for {node_id}: {e}")
            return []

    def get_metrics(self) -> Dict[str, Any]:
        """Get performance and usage metrics."""
        self.reconcile_graph()
        return {
            **self.metrics,
            'total_nodes': len(self.graph.nodes),
            'total_edges': len(self.graph.edges),
            'graph_density': nx.density(self.graph),
            'connected_components': nx.number_weakly_connected_components(
                self.graph,
            ),
        }

    @staticmethod
    def _json_default(value: Any) -> Any:
        if isinstance(value, (datetime, date)):
            return value.isoformat()
        if isinstance(value, set):
            return sorted(value, key=repr)
        raise TypeError(f"Cannot serialize {type(value).__name__}")

    def export_graph(self, format: str = 'graphml') -> str:
        """Serialize a detached graph; return an empty string on failure.

        JSON preserves nulls and structured attributes. XML omits top-level
        null attributes and JSON-encodes non-scalars (including nested nulls).
        Dates use ISO text and sets use arrays. XML is an interchange view,
        not a typed round trip. Relationship occurrence lists are retained.
        """
        try:
            self.reconcile_graph()
            graph = copy.deepcopy(self.graph)
            if format in ('graphml', 'gexf'):
                attribute_sets = [graph.graph]
                for key in ('node_default', 'edge_default'):
                    defaults = graph.graph.get(key)
                    if isinstance(defaults, dict):
                        attribute_sets.append(defaults)
                attribute_sets.extend(
                    attrs for _, attrs in graph.nodes(data=True)
                )
                attribute_sets.extend(
                    attrs for _, _, attrs in graph.edges(data=True)
                )
                for attrs in attribute_sets:
                    for key, value in list(attrs.items()):
                        if value is None:
                            del attrs[key]
                        elif (
                            attrs is graph.graph
                            and key in ('node_default', 'edge_default')
                        ):
                            continue
                        elif isinstance(value, (datetime, date)):
                            attrs[key] = value.isoformat()
                        elif not isinstance(value, (str, int, float, bool)):
                            attrs[key] = json.dumps(
                                value, default=self._json_default,
                            )
                generator = (
                    nx.generate_graphml if format == 'graphml'
                    else nx.generate_gexf
                )
                return '\n'.join(generator(graph))
            if format == 'json':
                # Retain NetworkX's version-specific node-link envelope.
                import warnings
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", FutureWarning)
                    graph_data = nx.node_link_data(graph)
                return json.dumps(
                    graph_data, default=self._json_default, indent=2,
                )
            if format == 'edgelist':
                return '\n'.join(nx.generate_edgelist(graph, data=True)) + '\n'
            if format == 'adjlist':
                return '\n'.join(nx.generate_adjlist(graph)) + '\n'
            raise ValueError(f"Unsupported format: {format}")
        except Exception as e:
            logger.error(f"Failed to export graph: {e}")
            return ""

    def clear(self) -> None:
        """Clear all data from the ATLAS engine."""
        self.graph.clear()
        self.entities.clear()
        self.patterns.clear()
        self.queries.clear()
        self.attributes.clear()
        self.interfaces.clear()
        self.relationships.clear()
        self._owned_relationships.clear()
        self._managed_edges.clear()
        self._declared_edges.clear()

        # Reset metrics
        for key in self.metrics:
            self.metrics[key] = 0

        logger.info("ATLAS engine cleared")