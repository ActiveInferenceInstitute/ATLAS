"""
Tests for Obsidian Integration

This module tests the Obsidian integration functionality including
parsing vaults, importing/exporting data, and synchronization.
"""

import os
import sys
import tempfile
import shutil
import unicodedata
from collections import Counter
from copy import deepcopy
from pathlib import Path
import pytest

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    from atlas.integrations.obsidian import ObsidianIntegration, ObsidianParser
    from atlas.core.engine import ATLASEngine
    from atlas.entities.entity import Entity
    from atlas.patterns.pattern import Pattern
    from atlas.queries.iquery import iQuery, QueryPriority
    OBSIDIAN_AVAILABLE = True
except ImportError as e:
    print(f"Obsidian integration not available: {e}")
    OBSIDIAN_AVAILABLE = False


@pytest.mark.skipif(
    not OBSIDIAN_AVAILABLE, reason="Obsidian integration not available"
)
class TestObsidianParser:
    """Test the ObsidianParser functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parser = ObsidianParser()
        self.test_dir = Path(tempfile.mkdtemp())

    def teardown_method(self):
        """Clean up test fixtures."""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_parser_initialization(self):
        """Test parser initialization."""
        assert self.parser is not None
        assert hasattr(self.parser, 'wiki_link_pattern')
        assert hasattr(self.parser, 'tag_pattern')
        assert hasattr(self.parser, 'frontmatter_pattern')

    def test_parse_simple_note(self):
        """Test parsing a simple note without frontmatter."""
        note_content = """# Test Note

This is a simple note with [[linked note]] and #tag.

Some more content here.
"""
        note_file = self.test_dir / "test_note.md"
        with open(note_file, 'w', encoding='utf-8') as f:
            f.write(note_content)

        note = self.parser.parse_note(note_file)

        assert note.title == "test_note"
        assert "linked note" in note.wiki_links
        assert "tag" in note.tags
        assert "This is a simple note" in note.content
        assert note.frontmatter == {}

    def test_parse_note_with_frontmatter(self):
        """Test parsing a note with YAML frontmatter."""
        note_content = """---
title: My Test Note
tags:
  - important
  - project
created: 2023-01-01T10:00:00
modified: 2023-01-02T15:30:00
---

# My Test Note

This note has frontmatter and links to [[another note]].

It also has #inline-tag and content.
"""
        note_file = self.test_dir / "frontmatter_note.md"
        with open(note_file, 'w', encoding='utf-8') as f:
            f.write(note_content)

        note = self.parser.parse_note(note_file)

        # Filename identity is independent of the frontmatter display title.
        assert note.title == "frontmatter_note"
        assert "another note" in note.wiki_links
        assert "important" in note.tags
        assert "project" in note.tags
        assert "inline-tag" in note.tags
        assert note.frontmatter['title'] == "My Test Note"
        assert "This note has frontmatter" in note.content

    def test_parse_note_with_aliases(self):
        """Test parsing notes with wiki link aliases."""
        note_content = """# Note with Aliases

This note links to [[Target Note|Display Name]] and [[Another Note]].
"""
        note_file = self.test_dir / "alias_note.md"
        with open(note_file, 'w', encoding='utf-8') as f:
            f.write(note_content)

        note = self.parser.parse_note(note_file)

        assert "Target Note" in note.wiki_links
        assert "Another Note" in note.wiki_links

    def test_parse_vault_structure(self):
        """Test parsing a complete vault structure."""
        # Create test vault structure
        (self.test_dir / "folder1").mkdir()
        (self.test_dir / "folder2").mkdir()
        (self.test_dir / "Templates").mkdir()

        # Create test notes
        notes = [
            ("note1.md", "# Note 1\nThis is note 1 with [[note2]].\n#tag1"),
            ("folder1/note2.md", "# Note 2\nThis is note 2.\n#tag2"),
            ("folder2/note3.md",
             "# Note 3\nThis links to [[note1]].\n#tag1 #tag3"),
            ("Templates/template.md", "# Template\nThis is a template.\n")
        ]

        for path, content in notes:
            file_path = self.test_dir / path
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

        vault = self.parser.parse_vault(self.test_dir)

        assert len(vault.notes) == 3  # Templates excluded
        assert "note1" in vault.notes
        assert "folder1/note2" in vault.notes
        assert "folder2/note3" in vault.notes
        assert len(vault.templates) == 1


@pytest.mark.skipif(
    not OBSIDIAN_AVAILABLE, reason="Obsidian integration not available"
)
class TestObsidianIntegration:
    """Test the main ObsidianIntegration functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.atlas = ATLASEngine()
        self.integration = ObsidianIntegration(self.atlas)
        self.test_dir = Path(tempfile.mkdtemp())

    def teardown_method(self):
        """Clean up test fixtures."""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_integration_initialization(self):
        """Test integration initialization."""
        assert self.integration.atlas is not None
        assert self.integration.parser is not None
        assert isinstance(self.integration.imported_notes, dict)
        assert isinstance(self.integration.exported_files, set)

    def test_import_simple_vault(self):
        """Test importing a simple vault."""
        # Create test vault
        (self.test_dir / "Notes").mkdir()

        notes = [
            ("note1.md", "# Note 1\nContent about science.\n#science"),
            ("Notes/note2.md",
             "# Note 2\nContent about technology.\n#technology"),
            ("note3.md",
             "# Note 3\nLinks to [[note1]] and [[note2]].\n"
             "#science #technology")
        ]

        for path, content in notes:
            file_path = self.test_dir / path
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

        # Import vault
        stats = self.integration.import_vault(self.test_dir)

        assert stats['notes_processed'] == 3
        assert stats['entities_created'] == 3
        assert stats['patterns_created'] >= 2  # Science and technology tags
        assert stats['relationships_created'] >= 2  # Wiki links

        # Check that entities were created
        assert len(self.atlas.entities) == 3

        # Check that patterns were created
        assert len(self.atlas.patterns) >= 2

    def test_export_to_vault(self):
        """Test exporting ATLAS data to a vault."""
        # Add test data to ATLAS
        entity = Entity(
            entity_id="test_entity",
            attributes={
                "title": "Test Entity",
                "content": "This is test content.",
                "domain": "testing"
            },
            patterns=["test_pattern"]
        )

        pattern = Pattern(
            pattern_id="test_pattern",
            qkit=["what_is_test", "how_to_test"],
            attributes={"domain": "testing", "description": "A test pattern"}
        )

        query = iQuery(
            query_id="test_query",
            query_text="What is testing?",
            target_patterns=["test_pattern"],
            priority=QueryPriority.NORMAL
        )

        self.atlas.add_entity(entity.id, entity.to_dict())
        self.atlas.add_pattern(pattern.id, pattern.to_dict())
        self.atlas.add_query(query.id, query.to_dict())

        # Export to vault
        output_dir = self.test_dir / "export"
        stats = self.integration.export_to_vault(output_dir)

        assert stats['entities_exported'] >= 1
        assert stats['patterns_exported'] >= 1
        assert stats['files_created'] >= 3  # Entity, pattern, and index

        # Check that files were created
        assert (output_dir / "ATLAS_Export" / "Entities").exists()
        assert (output_dir / "ATLAS_Export" / "Patterns").exists()
        assert (output_dir / "ATLAS_Export" / "README.md").exists()

    def test_bidirectional_sync(self):
        """Test bidirectional synchronization."""
        # Create test vault with notes
        (self.test_dir / "vault").mkdir()
        test_note = """---
title: Sync Test Note
tags: [sync, test]
---

# Sync Test Note

This note will be synchronized with ATLAS.
"""
        with open(self.test_dir / "vault" / "sync_note.md", 'w') as f:
            f.write(test_note)

        # Perform bidirectional sync
        stats = self.integration.sync_vault(
            self.test_dir / "vault",
            sync_mode='bidirectional'
        )

        assert 'import_stats' in stats
        assert 'export_stats' in stats
        assert stats['mode'] == 'bidirectional'

    def test_integration_with_real_patterns(self):
        """Test integration with realistic pattern creation."""
        # Create vault with hierarchical tags
        notes = [
            ("ai_overview.md",
             "# AI Overview\nArtificial Intelligence overview.\n"
             "#ai #technology"),
            ("machine_learning.md",
             "# Machine Learning\nML is part of [[ai_overview]].\n"
             "#ai/ml #technology"),
            ("deep_learning.md",
             "# Deep Learning\nDL is part of [[machine_learning]].\n"
             "#ai/ml/dl #technology"),
        ]

        for path, content in notes:
            file_path = self.test_dir / path
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

        stats = self.integration.import_vault(self.test_dir)

        # Should create hierarchical patterns from nested tags
        assert stats['patterns_created'] >= 4

        # Check that patterns were created
        patterns = self.atlas.patterns
        pattern_ids = list(patterns.keys())
        assert any('ai' in p_id for p_id in pattern_ids)
        assert any('technology' in p_id for p_id in pattern_ids)

    def test_export_note_format(self):
        """Test the format of exported notes."""
        # Add entity with comprehensive data
        entity = Entity(
            entity_id="detailed_entity",
            attributes={
                "title": "Detailed Entity",
                "content": "This is detailed content with **markdown**.",
                "tags": ["important", "detailed"],
                "created_date": "2023-01-01T10:00:00",
                "custom_field": "custom_value"
            },
            patterns=["detailed_pattern"]
        )

        self.atlas.add_entity(entity.id, entity.to_dict())

        # Export to vault
        output_dir = self.test_dir / "format_test"
        self.integration.export_to_vault(output_dir)

        # Read exported file
        entities_dir = output_dir / "ATLAS_Export" / "Entities"
        entity_files = list(entities_dir.glob("*.md"))
        assert len(entity_files) > 0

        content = entity_files[0].read_text(encoding='utf-8')

        # Check frontmatter
        assert '---' in content
        assert 'type: entity' in content
        assert 'entity_id: detailed_entity' in content

        # Check content structure
        assert '# Detailed Entity' in content
        assert '## Metadata' in content
        assert 'This is detailed content' in content


@pytest.mark.skipif(
    not OBSIDIAN_AVAILABLE, reason="Obsidian integration not available"
)
class TestObsidianEdgeCases:
    """Test edge cases and error handling."""

    def setup_method(self):
        """Set up test fixtures."""
        self.integration = ObsidianIntegration()
        self.test_dir = Path(tempfile.mkdtemp())

    def teardown_method(self):
        """Clean up test fixtures."""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_empty_vault(self):
        """Test importing an empty vault."""
        stats = self.integration.import_vault(self.test_dir)

        assert stats['notes_processed'] == 0
        assert stats['entities_created'] == 0
        assert stats['patterns_created'] == 0
        assert stats['relationships_created'] == 0

    def test_malformed_frontmatter(self):
        """Test handling malformed YAML frontmatter."""
        malformed_note = """---
title: Test
invalid_yaml: [unclosed list
tags: test
---

# Test Note

Content here.
"""
        note_file = self.test_dir / "malformed.md"
        with open(note_file, 'w') as f:
            f.write(malformed_note)

        # Should not crash
        stats = self.integration.import_vault(self.test_dir)
        assert stats['notes_processed'] == 1

    def test_special_characters_in_filenames(self):
        """Test handling special characters in note names."""
        special_notes = [
            ("note with spaces.md", "# Note with Spaces\nContent.\n"),
            ("note-with-dashes.md", "# Note with Dashes\nContent.\n"),
            ("note_with_underscores.md",
             "# Note with Underscores\nContent.\n"),
        ]

        for filename, content in special_notes:
            note_file = self.test_dir / filename
            with open(note_file, 'w') as f:
                f.write(content)

        stats = self.integration.import_vault(self.test_dir)
        assert stats['notes_processed'] == 3
        assert stats['entities_created'] == 3

    def test_broken_wiki_links(self):
        """Test handling broken wiki links."""
        note_content = """# Test Note

This note has a broken link to [[Non-existent Note]].
And a working link to [[working_note]].
"""
        working_note = """# Working Note

This note exists.
"""

        with open(self.test_dir / "test_note.md", 'w') as f:
            f.write(note_content)

        with open(self.test_dir / "working_note.md", 'w') as f:
            f.write(working_note)

        stats = self.integration.import_vault(self.test_dir)

        # Should create entities for both notes
        assert stats['notes_processed'] == 2
        assert stats['entities_created'] == 2
        # Should only create relationship for working link
        assert stats['relationships_created'] == 1


@pytest.mark.skipif(
    not OBSIDIAN_AVAILABLE, reason="Obsidian integration not available"
)
class TestObsidianOwnershipRegressions:
    """Source identity, ownership, and emitted-link contracts."""

    @staticmethod
    def _write_notes(root, notes):
        for name, content in notes.items():
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding='utf-8')

    @staticmethod
    def _exported_records(vault):
        parser = ObsidianParser()
        records = {}
        for path in vault.rglob('*.md'):
            note = parser.parse_note(path)
            if note.frontmatter.get('atlas_export') is not True:
                continue
            kind = note.frontmatter['type']
            record_id = note.frontmatter.get(f'{kind}_id', '')
            assert (kind, record_id) not in records
            records[(kind, record_id)] = (path.relative_to(vault), note)
        return records

    @pytest.mark.parametrize('reverse', [False, True])
    def test_relative_identities_and_qualified_links(
        self, tmp_path, monkeypatch, reverse
    ):
        self._write_notes(tmp_path, {
            'Left/Overview.md': 'Left overview.',
            'Right/Overview.md': 'Right overview.',
            'Links.md': (
                '[[Left/Overview.md#Details|Left]] [[Right/Overview]]'
            ),
            'Short.md': '[[Overview]]',
            'Left/Local.md': '[[./Overview]] [[../Right/Overview]]',
            'name with spaces.md': 'Spaced name.',
            'name_with_spaces.md': 'Underscored name.',
            'Templates/Overview.md': 'Template, never a source note.'
        })
        original_rglob = Path.rglob

        def reordered_rglob(path, pattern):
            files = list(original_rglob(path, pattern))
            return iter(reversed(files) if reverse else files)

        monkeypatch.setattr(Path, 'rglob', reordered_rglob)
        parser = ObsidianParser()
        vault = parser.parse_vault(tmp_path)
        assert set(vault.notes) == {
            'Left/Overview', 'Right/Overview', 'Links', 'Short', 'Left/Local',
            'name with spaces', 'name_with_spaces'
        }
        for note_id, note in vault.notes.items():
            assert note.note_id == note_id
        assert vault.notes['Left/Overview'].content == 'Left overview.'
        assert vault.notes['Right/Overview'].content == 'Right overview.'

        integration = ObsidianIntegration()
        stats = integration.import_vault(tmp_path)
        ids = integration.imported_notes.copy()
        assert stats['entities_created'] == 7
        assert len(set(ids.values())) == 7
        expected = {
            (ids['Left/Overview'], 'references'),
            (ids['Right/Overview'], 'references')
        }
        assert set(
            integration.atlas.get_relationships(ids['Links'])
        ) == expected
        assert set(
            integration.atlas.get_relationships(ids['Left/Local'])
        ) == expected
        assert integration.atlas.get_relationships(ids['Short']) == []
        assert any(
            'Short.md' in error and 'Ambiguous wiki link' in error
            for error in stats['errors']
        )
        assert ids['name with spaces'] != ids['name_with_spaces']

        # Neither discovery order nor a fresh engine changes the identities.
        reverse = not reverse
        fresh = ObsidianIntegration()
        fresh.import_vault(tmp_path)
        assert fresh.imported_notes == ids
        rebuilt = ObsidianIntegration(integration.atlas)
        repeated = rebuilt.import_vault(tmp_path)
        assert rebuilt.imported_notes == ids
        assert repeated['entities_created'] == 0
        assert repeated['entities_updated'] == 7

    def test_same_relative_note_in_different_vaults(self, tmp_path):
        first = tmp_path / 'First'
        second = tmp_path / 'Second'
        self._write_notes(first, {'Overview.md': 'First vault.'})
        self._write_notes(second, {'Overview.md': 'Second vault.'})
        integration = ObsidianIntegration()
        integration.import_vault(first)
        first_id = integration.imported_notes['Overview']
        integration.import_vault(second)
        second_id = integration.imported_notes['Overview']
        assert first_id != second_id
        assert len(integration.atlas.entities) == 2
        assert (
            integration.atlas.entities[first_id]['attributes']['content']
            == 'First vault.'
        )
        integration.import_vault(first)
        assert integration.imported_notes['Overview'] == first_id

    @pytest.mark.parametrize('with_path', [False, True])
    def test_unique_legacy_identity_is_retained(self, tmp_path, with_path):
        self._write_notes(tmp_path, {'Folder/My Note.md': 'Updated content.'})
        attributes = {
            'source': 'obsidian', 'title': 'My Note', 'manual': 'Keep me'
        }
        if with_path:
            attributes['file_path'] = str(tmp_path / 'Folder/My Note.md')
        legacy = Entity(
            entity_id='obsidian_note_My_Note', attributes=attributes
        )
        engine = ATLASEngine()
        engine.add_entity(legacy.id, legacy.to_dict())
        integration = ObsidianIntegration(engine)
        stats = integration.import_vault(tmp_path)
        assert stats['errors'] == []
        assert stats['entities_created'] == 0
        assert stats['entities_updated'] == 1
        assert integration.imported_notes == {'Folder/My Note': legacy.id}
        data = engine.entities[legacy.id]
        assert data['attributes']['content'] == 'Updated content.'
        assert data['attributes']['manual'] == 'Keep me'
        assert data['obsidian']['note_id'] == 'Folder/My Note'

    def test_legacy_exact_path_disambiguates_duplicate_titles(self, tmp_path):
        self._write_notes(tmp_path, {
            'Left/Overview.md': 'Left.',
            'Right/Overview.md': 'Right.'
        })
        legacy = Entity(
            entity_id='obsidian_note_Overview',
            attributes={
                'source': 'obsidian',
                'file_path': str(tmp_path / 'Right/Overview.md')
            }
        )
        engine = ATLASEngine()
        engine.add_entity(legacy.id, legacy.to_dict())
        integration = ObsidianIntegration(engine)
        stats = integration.import_vault(tmp_path)
        assert stats['errors'] == []
        assert stats['entities_created'] == 1
        assert integration.imported_notes['Right/Overview'] == legacy.id
        assert integration.imported_notes['Left/Overview'] != legacy.id
        assert engine.entities[legacy.id]['attributes']['content'] == 'Right.'

    def test_ambiguous_legacy_identity_is_not_guessed(self, tmp_path):
        self._write_notes(tmp_path, {
            'Left/Overview.md': 'Left.',
            'Right/Overview.md': 'Right.',
            'Independent.md': 'Successful peer.'
        })
        legacy = Entity(
            entity_id='obsidian_note_Overview',
            attributes={'source': 'obsidian', 'content': 'Unattributed legacy'}
        )
        engine = ATLASEngine()
        engine.add_entity(legacy.id, legacy.to_dict())
        before = deepcopy(engine.entities[legacy.id])
        integration = ObsidianIntegration(engine)
        stats = integration.import_vault(tmp_path)
        assert any('AMBIGUOUS legacy mapping' in e for e in stats['errors'])
        assert stats['notes_processed'] == 1
        assert set(integration.imported_notes) == {'Independent'}
        assert engine.entities[legacy.id] == before
        assert len(engine.entities) == 2

    def test_duplicate_persisted_claims_are_refused(self, tmp_path):
        self._write_notes(tmp_path, {'Note.md': 'Original.'})
        integration = ObsidianIntegration()
        integration.import_vault(tmp_path)
        note_id = integration.imported_notes['Note']
        duplicate = deepcopy(integration.atlas.entities[note_id])
        duplicate['id'] = 'duplicate'
        integration.atlas.add_entity('duplicate', duplicate)
        before = deepcopy(integration.atlas.entities)
        self._write_notes(tmp_path, {'Note.md': 'Do not guess an owner.'})
        fresh = ObsidianIntegration(integration.atlas)
        stats = fresh.import_vault(tmp_path)
        assert any('AMBIGUOUS mapping' in e for e in stats['errors'])
        assert fresh.imported_notes == {}
        assert stats['notes_processed'] == 0
        assert integration.atlas.entities == before

    def test_sync_refreshes_only_source_owned_state(self, tmp_path):
        self._write_notes(tmp_path, {
            'Source.md': (
                '---\ntags: [old]\nobsolete: old\nretained: before\n---\n'
                'Before [[Old]].'
            ),
            'Old.md': 'Old target.',
            'New.md': 'New target.'
        })
        integration = ObsidianIntegration()
        first = integration.import_vault(tmp_path)
        assert first['errors'] == []
        ids = integration.imported_notes.copy()
        engine = integration.atlas
        source_id = ids['Source']
        data = engine.entities[source_id]
        data['attributes']['manual_field'] = {'keep': [1, 2]}
        data['attributes']['tags'].append('manual-tag')
        data['attributes']['fm_manual'] = 'Not imported'
        data['metadata']['quality_score'] = 0.75
        data['metadata']['tags'].append('manual-metadata-tag')
        data['anomalies']['manual-query'] = 'Keep anomaly'
        data['pending_rfis'].append('manual-pending')
        engine.add_pattern(
            'manual-pattern', {'attributes': {'name': 'Manual'}}
        )
        data['patterns'].append('manual-pattern')
        for _ in range(2):
            engine.add_relationship(source_id, ids['Old'], 'references')
        engine.add_relationship(source_id, ids['Old'], 'related_to')
        engine.add_relationship(ids['Old'], source_id, 'manual_reverse')

        self._write_notes(tmp_path, {
            'Source.md': (
                '---\ntags: [new]\nretained: after\nadded: present\n---\n'
                'After [[New]].'
            )
        })
        fresh = ObsidianIntegration(engine)
        stats = fresh.sync_vault(tmp_path, sync_mode='import')['import_stats']
        assert stats['errors'] == []
        assert stats['entities_created'] == 0
        assert stats['entities_updated'] == 3
        assert fresh.imported_notes == ids
        updated = engine.entities[source_id]
        attributes = updated['attributes']
        assert attributes['content'] == 'After [[New]].'
        assert attributes['wiki_links'] == ['New']
        assert attributes['fm_retained'] == 'after'
        assert attributes['fm_added'] == 'present'
        assert 'fm_obsolete' not in attributes
        assert attributes['fm_manual'] == 'Not imported'
        assert attributes['manual_field'] == {'keep': [1, 2]}
        assert set(attributes['tags']) == {'new', 'manual-tag'}
        assert set(updated['metadata']['tags']) == {
            'new', 'manual-metadata-tag'
        }
        assert updated['metadata']['quality_score'] == 0.75
        assert updated['anomalies'] == {'manual-query': 'Keep anomaly'}
        assert updated['pending_rfis'] == ['manual-pending']
        assert set(updated['patterns']) == {
            'manual-pattern', 'obsidian_tag_new'
        }
        expected = Counter({
            (ids['Old'], 'references'): 2,
            (ids['Old'], 'related_to'): 1,
            (ids['New'], 'references'): 1
        })
        assert Counter(engine.get_relationships(source_id)) == expected
        assert engine.get_relationships(ids['Old']) == [
            (source_id, 'manual_reverse')
        ]
        assert all(
            occurrence['origin'] == 'explicit'
            for occurrence in engine.graph.edges[
                source_id, ids['Old']
            ]['relationships']
        )
        assert engine.graph.edges[
            source_id, ids['New']
        ]['relationships'][0]['origin'] == 'owned'

        repeated = ObsidianIntegration(engine)
        repeated.import_vault(tmp_path)
        assert repeated.imported_notes == ids
        assert Counter(engine.get_relationships(source_id)) == expected
        self._write_notes(tmp_path, {'Source.md': 'No source links or tags.'})
        repeated.import_vault(tmp_path)
        del expected[(ids['New'], 'references')]
        assert Counter(engine.get_relationships(source_id)) == expected
        assert not engine.graph.has_edge(source_id, ids['New'])
        assert engine.entities[source_id]['patterns'] == ['manual-pattern']

    def test_source_field_conflict_preserves_manual_attribute(self, tmp_path):
        self._write_notes(tmp_path, {
            'Source.md': '[[Target]]', 'Target.md': 'Target.'
        })
        integration = ObsidianIntegration()
        integration.import_vault(tmp_path)
        source_id = integration.imported_notes['Source']
        data = integration.atlas.entities[source_id]
        data['attributes']['fm_new'] = 'Manual value'
        before = deepcopy(data)
        relationships = list(integration.atlas.get_relationships(source_id))
        self._write_notes(tmp_path, {
            'Source.md': '---\nnew: Source value\n---\nChanged content.'
        })
        fresh = ObsidianIntegration(integration.atlas)
        stats = fresh.import_vault(tmp_path)
        assert any(
            'Source.md' in error and 'manual attributes' in error
            for error in stats['errors']
        )
        assert integration.atlas.entities[source_id] == before
        assert integration.atlas.get_relationships(source_id) == relationships

    def test_existing_manual_pattern_assignment_remains_manual(self, tmp_path):
        self._write_notes(tmp_path, {'Source.md': 'No source tag.'})
        integration = ObsidianIntegration()
        integration.import_vault(tmp_path)
        source_id = integration.imported_notes['Source']
        engine = integration.atlas
        pattern = Pattern(
            pattern_id='obsidian_tag_topic', attributes={'manual': True}
        )
        engine.add_pattern(pattern.id, pattern.to_dict())
        before_pattern = deepcopy(engine.patterns[pattern.id])
        engine.entities[source_id]['patterns'].append(pattern.id)
        self._write_notes(tmp_path, {'Source.md': '#topic'})
        fresh = ObsidianIntegration(engine)
        fresh.import_vault(tmp_path)
        assert engine.entities[source_id]['obsidian']['pattern_ids'] == []
        self._write_notes(tmp_path, {'Source.md': 'Source tag withdrawn.'})
        fresh.import_vault(tmp_path)
        assert engine.entities[source_id]['patterns'] == [pattern.id]
        assert engine.patterns[pattern.id] == before_pattern

    def test_fresh_mapping_supports_relationship_only_import(self, tmp_path):
        self._write_notes(tmp_path, {
            'Source.md': '[[First]]',
            'First.md': 'First.',
            'Second.md': 'Second.'
        })
        integration = ObsidianIntegration()
        integration.import_vault(tmp_path)
        ids = integration.imported_notes.copy()
        self._write_notes(tmp_path, {'Source.md': '[[Second]]'})
        fresh = ObsidianIntegration(integration.atlas)
        stats = fresh.import_vault(
            tmp_path, create_entities_from_notes=False,
            create_patterns_from_tags=False
        )
        assert stats['errors'] == []
        assert fresh.imported_notes == ids
        assert integration.atlas.get_relationships(ids['Source']) == [
            (ids['Second'], 'references')
        ]
        assert (
            integration.atlas.entities[ids['Source']]['attributes']['content']
            == '[[First]]'
        )

    def test_failed_source_read_preserves_previous_owned_links(self, tmp_path):
        self._write_notes(tmp_path, {
            'Source.md': '[[Target]]', 'Target.md': 'Original target.'
        })
        integration = ObsidianIntegration()
        integration.import_vault(tmp_path)
        ids = integration.imported_notes.copy()
        before = deepcopy(integration.atlas.entities[ids['Source']])
        (tmp_path / 'Source.md').write_bytes(b'\xff')
        self._write_notes(tmp_path, {'Target.md': 'Refreshed peer.'})
        fresh = ObsidianIntegration(integration.atlas)
        stats = fresh.import_vault(tmp_path)
        assert any('Source.md' in error for error in stats['errors'])
        assert stats['notes_processed'] == 1
        assert fresh.imported_notes == ids
        assert integration.atlas.entities[ids['Source']] == before
        assert integration.atlas.get_relationships(ids['Source']) == [
            (ids['Target'], 'references')
        ]
        assert (
            integration.atlas.entities[ids['Target']]['attributes']['content']
            == 'Refreshed peer.'
        )

    def test_read_failures_coexist_with_tolerated_yaml_and_templates(
        self, tmp_path, monkeypatch
    ):
        self._write_notes(tmp_path, {
            'Good.md': 'Readable.',
            'Malformed.md': '---\ninvalid: [unclosed\n---\nStill a note.',
            'Denied.md': 'Unreadable by fixture.',
            'Left/Overview.md': 'Readable overview.',
            'Short.md': '[[Overview]]',
            'Templates/Excluded.md': 'Template only.'
        })
        (tmp_path / 'Invalid.md').write_bytes(b'\xff')
        (tmp_path / 'Right').mkdir()
        (tmp_path / 'Right/Overview.md').write_bytes(b'\xff')
        original_read_text = Path.read_text

        def deny_one(path, *args, **kwargs):
            if path == tmp_path / 'Denied.md':
                raise PermissionError('Fixture denied this note')
            return original_read_text(path, *args, **kwargs)

        monkeypatch.setattr(Path, 'read_text', deny_one)
        parser = ObsidianParser()
        vault = parser.parse_vault(tmp_path)
        assert set(vault.errors) == {
            'Denied.md', 'Invalid.md', 'Right/Overview.md'
        }
        assert set(vault.notes) == {
            'Good', 'Malformed', 'Left/Overview', 'Short'
        }
        assert vault.notes['Malformed'].frontmatter == {}
        assert 'Still a note.' in vault.notes['Malformed'].content
        assert set(vault.templates) == {'Excluded'}
        assert 'Templates/Excluded' not in vault.note_ids
        integration = ObsidianIntegration()
        stats = integration.import_vault(tmp_path)
        assert stats['notes_processed'] == 4
        assert stats['entities_created'] == 4
        for failed_path in vault.errors:
            assert any(failed_path in e for e in stats['errors'])
        assert any('Ambiguous wiki link' in e for e in stats['errors'])
        assert integration.atlas.get_relationships(
            integration.imported_notes['Short']
        ) == []

    def test_all_export_link_producers_use_allocated_paths(self, tmp_path):
        titles = [
            'Same', 'Same', 'A/B', 'A:B', 'x' * 105 + 'first',
            'x' * 105 + 'second', 'Case', 'case', '...', '界' * 100
        ]
        engine = ATLASEngine()
        for index, title in enumerate(titles):
            pattern = Pattern(
                pattern_id=f'p{index}', attributes={'name': title}
            )
            entity = Entity(
                entity_id=f'e{index}', attributes={'title': title},
                patterns=[pattern.id]
            )
            engine.add_pattern(pattern.id, pattern.to_dict())
            engine.add_entity(entity.id, entity.to_dict())
        for index in range(len(titles)):
            target = (index + 1) % len(titles)
            engine.add_relationship(f'e{index}', f'e{target}', 'references')
            engine.add_relationship(f'e{index}', f'p{target}', 'related_to')
        engine.add_relationship('e0', 'e1', 'references')
        engine.add_relationship('e0', 'e1', 'references')

        integration = ObsidianIntegration(engine)
        stats = integration.export_to_vault(tmp_path)
        assert stats['errors'] == []
        assert stats['entities_exported'] == len(titles)
        assert stats['patterns_exported'] == len(titles)
        assert stats['files_created'] == 2 * len(titles) + 1
        vault = tmp_path / 'ATLAS_Export'
        records = self._exported_records(vault)
        assert len(records) == 2 * len(titles) + 1
        paths = [path for path, _ in records.values()]
        assert len({
            unicodedata.normalize('NFC', path.as_posix()).casefold()
            for path in paths
        }) == len(paths)
        for _, note in records.values():
            for link in note.wiki_links:
                assert (vault / f'{link}.md').is_file()
        for index in range(len(titles)):
            entity_path, entity_note = records[('entity', f'e{index}')]
            pattern_path, pattern_note = records[('pattern', f'p{index}')]
            assert (
                pattern_path.with_suffix('').as_posix()
                in entity_note.wiki_links
            )
            assert (
                entity_path.with_suffix('').as_posix()
                in pattern_note.wiki_links
            )
            target = (index + 1) % len(titles)
            for kind, target_id in [
                ('entity', f'e{target}'), ('pattern', f'p{target}')
            ]:
                path, _ = records[(kind, target_id)]
                target_link = path.with_suffix('').as_posix()
                assert target_link in entity_note.wiki_links
        repeated_target = records[('entity', 'e1')][0]
        repeated_link = repeated_target.with_suffix('').as_posix()
        assert records[('entity', 'e0')][1].content.count(
            f"**References**: [[{repeated_link}]]"
        ) == 3
        _, index_note = records[('index', '')]
        assert index_note.wiki_links == {
            path.with_suffix('').as_posix()
            for key, (path, _) in records.items() if key != ('index', '')
        }
        repeated = integration.export_to_vault(tmp_path)
        assert repeated['errors'] == []
        assert {
            key: path
            for key, (path, _) in self._exported_records(vault).items()
        } == {key: path for key, (path, _) in records.items()}

    def test_export_reserves_existing_notes_and_index(self, tmp_path):
        vault = tmp_path / 'ATLAS_Export'
        self._write_notes(vault, {
            'Entities/Same.md': 'User-owned entity note.',
            'README.md': 'User-owned index.'
        })
        engine = ATLASEngine()
        for entity_id in ['first', 'second']:
            entity = Entity(
                entity_id=entity_id, attributes={'title': 'Same'}
            )
            engine.add_entity(entity.id, entity.to_dict())
        integration = ObsidianIntegration(engine)
        stats = integration.export_to_vault(tmp_path)
        assert stats['errors'] == []
        assert (
            (vault / 'Entities/Same.md').read_text(encoding='utf-8')
            == 'User-owned entity note.'
        )
        assert (
            (vault / 'README.md').read_text(encoding='utf-8')
            == 'User-owned index.'
        )
        records = self._exported_records(vault)
        assert len(records) == 3
        assert records[('index', '')][0] != Path('README.md')
        assert records[('entity', 'first')][0] != Path('Entities/Same.md')
        assert records[('entity', 'second')][0] != Path('Entities/Same.md')
        assert len(records[('index', '')][1].wiki_links) == 2

    @pytest.mark.parametrize('entities', [False, True])
    def test_export_omitted_records_do_not_get_dangling_links(
        self, tmp_path, entities
    ):
        engine = ATLASEngine()
        pattern = Pattern(pattern_id='pattern', attributes={'name': 'Named'})
        entity = Entity(
            entity_id='entity', attributes={'title': 'Named'},
            patterns=[pattern.id]
        )
        engine.add_pattern(pattern.id, pattern.to_dict())
        engine.add_entity(entity.id, entity.to_dict())
        engine.add_relationship(entity.id, pattern.id, 'uses')
        integration = ObsidianIntegration(engine)
        stats = integration.export_to_vault(
            tmp_path, include_entities=entities, include_patterns=not entities
        )
        assert stats['errors'] == []
        records = self._exported_records(tmp_path / 'ATLAS_Export')
        key = ('entity', entity.id) if entities else ('pattern', pattern.id)
        assert set(records) == {key, ('index', '')}
        assert records[key][1].wiki_links == set()
        assert records[('index', '')][1].wiki_links == {
            records[key][0].with_suffix('').as_posix()
        }

    def test_bidirectional_sync_does_not_import_its_own_views(self, tmp_path):
        self._write_notes(tmp_path, {
            'First.md': '[[Second]] #topic', 'Second.md': 'Second.'
        })
        integration = ObsidianIntegration()
        first = integration.sync_vault(tmp_path)
        assert first['import_stats']['errors'] == []
        assert first['export_stats']['errors'] == []
        ids = integration.imported_notes.copy()
        fresh = ObsidianIntegration(integration.atlas)
        second = fresh.sync_vault(tmp_path)
        assert second['import_stats']['errors'] == []
        assert second['export_stats']['errors'] == []
        assert fresh.imported_notes == ids
        assert len(fresh.atlas.entities) == 2
        assert fresh.atlas.get_relationships(ids['First']) == [
            (ids['Second'], 'references')
        ]

    def test_exported_vault_is_importable_into_fresh_engine(self, tmp_path):
        engine = ATLASEngine()
        entity = Entity(
            entity_id='original', attributes={'title': 'Exported source'}
        )
        engine.add_entity(entity.id, entity.to_dict())
        exported = ObsidianIntegration(engine).export_to_vault(tmp_path)
        assert exported['errors'] == []
        fresh = ObsidianIntegration()
        stats = fresh.import_vault(tmp_path / 'ATLAS_Export')
        assert stats['errors'] == []
        assert stats['entities_created'] == 1
        assert set(fresh.imported_notes) == {'Entities/Exported source'}


def test_integration_stats():
    """Test getting integration statistics."""
    if not OBSIDIAN_AVAILABLE:
        pytest.skip("Obsidian integration not available")

    integration = ObsidianIntegration()
    stats = integration.get_integration_stats()

    assert 'imported_notes' in stats
    assert 'exported_files' in stats
    assert 'atlas_entities' in stats
    assert 'atlas_patterns' in stats
    assert 'atlas_queries' in stats


if __name__ == "__main__":
    # Run basic tests
    if OBSIDIAN_AVAILABLE:
        print("Running Obsidian integration tests...")

        # Create a simple test
        test_parser = TestObsidianParser()
        test_parser.setup_method()

        try:
            test_parser.test_parser_initialization()
            print("✓ Parser initialization test passed")

            test_parser.test_parse_simple_note()
            print("✓ Simple note parsing test passed")

            print("🎉 Basic Obsidian integration tests completed successfully!")

        except Exception as e:
            print(f"❌ Test failed: {e}")

        finally:
            test_parser.teardown_method()
    else:
        print("❌ Obsidian integration not available for testing")