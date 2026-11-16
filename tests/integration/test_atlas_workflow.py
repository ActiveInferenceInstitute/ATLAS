#!/usr/bin/env python3
"""
Integration tests for ATLAS workflow.

These tests cover end-to-end workflows and component interactions.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

# Import ATLAS classes - if import fails, the test will fail appropriately
from atlas.core.engine import ATLASEngine, ATLASConfig
from atlas.entities.entity import Entity
from atlas.patterns.pattern import Pattern
from atlas.queries.iquery import iQuery, QueryPriority


class TestATLASWorkflowIntegration:
    """Integration tests for ATLAS workflow."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = ATLASConfig(
            auto_pattern_inference=True,
            enable_dynamic_typing=True,
            max_expansion_depth=3,
            enable_quality_metrics=True
        )
        self.atlas = ATLASEngine(self.config)

    def test_basic_workflow_integration(self):
        """Test basic ATLAS workflow integration."""
        # Step 1: Create and add a pattern
        pattern = Pattern(
            pattern_id="test_pattern_001",
            qkit=["what_is_test", "how_to_test"],
            attributes={"domain": "testing"}
        )

        success = self.atlas.add_pattern(pattern.id, pattern.to_dict())
        assert success is True
        assert pattern.id in self.atlas.patterns

        # Step 2: Create and add an entity
        entity = Entity(
            entity_id="test_entity_001",
            attributes={"name": "Test Entity", "type": "test"},
            patterns=[pattern.id]
        )

        success = self.atlas.add_entity(entity.id, entity.to_dict())
        assert success is True
        assert entity.id in self.atlas.entities

        # Step 3: Create and add a query
        query = iQuery(
            query_id="test_query_001",
            query_text="What is this test entity?",
            target_patterns=[pattern.id],
            priority=QueryPriority.NORMAL
        )

        success = self.atlas.add_query(query.id, query.to_dict())
        assert success is True
        assert query.id in self.atlas.queries

        # Step 4: Verify system metrics
        metrics = self.atlas.get_metrics()
        assert metrics['entities_created'] >= 1
        assert metrics['patterns_created'] >= 1

    def test_multi_component_workflow(self):
        """Test workflow with multiple entities and patterns."""
        # Create multiple patterns
        patterns = []
        for i in range(3):
            pattern = Pattern(
                pattern_id=f"pattern_{i}",
                qkit=[f"q{i}_1", f"q{i}_2"],
                attributes={"domain": "test", "index": i}
            )
            patterns.append(pattern)
            self.atlas.add_pattern(pattern.id, pattern.to_dict())

        # Create multiple entities
        entities = []
        for i in range(5):
            entity = Entity(
                entity_id=f"entity_{i}",
                attributes={"index": i, "category": "test"},
                patterns=[patterns[i % len(patterns)].id]
            )
            entities.append(entity)
            self.atlas.add_entity(entity.id, entity.to_dict())

        # Create queries targeting different patterns
        queries = []
        for i, pattern in enumerate(patterns):
            query = iQuery(
                query_id=f"query_{i}",
                query_text=f"Query for pattern {i}",
                target_patterns=[pattern.id],
                priority=QueryPriority.NORMAL
            )
            queries.append(query)
            self.atlas.add_query(query.id, query.to_dict())

        # Verify all components are registered
        assert len(self.atlas.entities) == 5
        assert len(self.atlas.patterns) == 3
        assert len(self.atlas.queries) == 3

        # Verify metrics
        metrics = self.atlas.get_metrics()
        assert metrics['entities_created'] == 5
        assert metrics['patterns_created'] == 3

    def test_search_workflow_integration(self):
        """Test search functionality integration."""
        # Add searchable content
        entity = Entity(
            entity_id="searchable_entity",
            attributes={
                "name": "Searchable Entity", "content": "important test data"
            },
            patterns=[]
        )

        self.atlas.add_entity(entity.id, entity.to_dict())

        # Perform search
        results = self.atlas.query("searchable")
        assert isinstance(results, list)
        assert any(result['id'] == entity.id for result in results)

    def test_configuration_workflow(self):
        """Test different configuration workflows."""
        # Test with different configurations
        config1 = ATLASConfig(
            auto_pattern_inference=False,
            enable_dynamic_typing=False,
            max_expansion_depth=1
        )

        atlas1 = ATLASEngine(config1)

        # Add same components to differently configured engine
        entity = Entity(
            entity_id="config_test_entity",
            attributes={"test": "configuration"},
            patterns=[]
        )

        success = atlas1.add_entity(entity.id, entity.to_dict())
        assert success is True

        # Verify configuration is applied
        assert atlas1.config.auto_pattern_inference is False
        assert atlas1.config.enable_dynamic_typing is False
        assert atlas1.config.max_expansion_depth == 1

    def test_workflow_error_handling(self):
        """Test workflow error handling and recovery."""
        # Empty optional inputs are supported constructor defaults.
        entity = Entity(entity_id="", attributes=None, patterns=None)
        assert entity.id
        assert entity.attributes == {}
        assert entity.patterns == []
        result = self.atlas.add_entity(entity.id, entity.to_dict())
        assert isinstance(result, bool)
        assert result is True

        # Invalid endpoints must fail without registering placeholder nodes.
        assert self.atlas.add_relationship(
            entity.id, "missing", "related"
        ) is False
        assert "missing" not in self.atlas.graph

    def test_workflow_state_consistency(self):
        """Test workflow state consistency across operations."""
        initial_metrics = self.atlas.get_metrics()

        # Add components and verify metrics update consistently
        entity = Entity(
            entity_id="consistency_entity",
            attributes={"test": "consistency"},
            patterns=[]
        )

        self.atlas.add_entity(entity.id, entity.to_dict())

        updated_metrics = self.atlas.get_metrics()

        # Verify state consistency
        assert (
            updated_metrics['entities_created']
            >= initial_metrics['entities_created']
        )
        assert entity.id in self.atlas.entities


if __name__ == "__main__":
    failed_tests = 0
    for method_name in dir(TestATLASWorkflowIntegration):
        if not method_name.startswith('test_'):
            continue
        try:
            instance = TestATLASWorkflowIntegration()
            instance.setup_method()
            getattr(instance, method_name)()
            print(f"PASSED: {method_name}")
        except Exception as exc:
            failed_tests += 1
            print(f"FAILED: {method_name}: {exc}")
    sys.exit(1 if failed_tests else 0)