"""
Obsidian Integration for ATLAS

This module provides comprehensive integration with Obsidian vaults,
enabling bidirectional conversion between Obsidian markdown files
and ATLAS knowledge structures.
"""

import hashlib
import json
import logging
import posixpath
import re
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime, date
from pathlib import Path
from typing import Dict, Optional, Set, List, Any

import yaml

from ..core.engine import ATLASEngine
from ..entities.entity import Entity, EntityMetadata
from ..patterns.pattern import Pattern

logger = logging.getLogger(__name__)


class ATLASJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle datetime and other special objects."""
    def default(self, obj: Any) -> Any:  # type: ignore
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        if isinstance(obj, Path):
            return str(obj)
        if isinstance(obj, set):
            return list(obj)
        return super().default(obj)


@dataclass
class ObsidianNote:
    """Represents an Obsidian note with metadata and content."""
    title: str
    content: str
    file_path: Path
    frontmatter: Dict = field(default_factory=dict)
    wiki_links: Set[str] = field(default_factory=set)
    tags: Set[str] = field(default_factory=set)
    created_date: Optional[datetime] = None
    modified_date: Optional[datetime] = None
    note_id: str = ""

    def __post_init__(self):
        """Process note content after initialization."""
        if not self.created_date:
            self.created_date = datetime.now()
        if not self.modified_date:
            self.modified_date = datetime.now()


@dataclass
class ObsidianVault:
    """Represents an Obsidian vault structure."""
    name: str
    root_path: Path
    notes: Dict[str, ObsidianNote] = field(default_factory=dict)
    attachments: Set[Path] = field(default_factory=set)
    templates: Dict[str, str] = field(default_factory=dict)
    settings: Dict = field(default_factory=dict)
    note_ids: Set[str] = field(default_factory=set)
    errors: Dict[str, str] = field(default_factory=dict)


class ObsidianParser:
    """Parser for Obsidian markdown files and vault structures."""

    def __init__(self):
        """Initialize the Obsidian parser."""
        # Regex patterns for Obsidian syntax
        self.wiki_link_pattern = re.compile(
            r'\[\[([^\]|]+)(?:\|([^\]]+))?\]\]'
        )
        self.tag_pattern = re.compile(r'(?:^|\s)#([a-zA-Z0-9/_-]+)')
        self.frontmatter_pattern = re.compile(
            r'^---\s*\n(.*?)\n---\s*\n', re.DOTALL
        )

    def parse_frontmatter(self, content: str) -> tuple[Dict, str]:
        """Parse YAML frontmatter from markdown content."""
        match = self.frontmatter_pattern.match(content)
        if match:
            try:
                frontmatter_data = yaml.safe_load(match.group(1))
                frontmatter = (
                    frontmatter_data
                    if isinstance(frontmatter_data, dict) else {}
                )
                content_without_frontmatter = content[match.end():]
                return frontmatter, content_without_frontmatter
            except yaml.YAMLError as e:
                logger.warning(f"Failed to parse YAML frontmatter: {e}")
                return {}, content
        return {}, content

    def extract_wiki_links(self, content: str) -> Set[str]:
        """Extract wiki-style links from content."""
        links = set()
        for match in self.wiki_link_pattern.finditer(content):
            link_target = match.group(1).strip()
            links.add(link_target)
        return links

    def extract_tags(self, content: str,
                     frontmatter: Optional[Dict] = None) -> Set[str]:
        """Extract tags from content and frontmatter."""
        tags = set()

        # Extract from content
        for match in self.tag_pattern.finditer(content):
            tag = match.group(1)
            tags.add(tag)

        # Extract from frontmatter
        if frontmatter:
            fm_tags = frontmatter.get('tags', [])
            if isinstance(fm_tags, str):
                fm_tags = [fm_tags]
            elif isinstance(fm_tags, list):
                fm_tags = [str(tag) for tag in fm_tags]
            else:
                fm_tags = []
            tags.update(fm_tags)

        return tags

    def parse_note(self, file_path: Path) -> ObsidianNote:
        """Parse a single Obsidian note file."""
        if not file_path.exists() or file_path.suffix.lower() != '.md':
            raise ValueError(f"Invalid note file: {file_path}")

        try:
            content = file_path.read_text(encoding='utf-8')
        except Exception as e:
            logger.error(f"Failed to read file {file_path}: {e}")
            raise

        frontmatter, clean_content = self.parse_frontmatter(content)

        # Extract components
        wiki_links = self.extract_wiki_links(clean_content)
        tags = self.extract_tags(clean_content, frontmatter)

        # Get file metadata
        try:
            stat = file_path.stat()
            created = datetime.fromtimestamp(stat.st_ctime)
            modified = datetime.fromtimestamp(stat.st_mtime)
        except Exception as e:
            logger.warning(f"Failed to get file stats for {file_path}: {e}")
            created = datetime.now()
            modified = datetime.now()

        return ObsidianNote(
            title=file_path.stem,
            content=clean_content,
            file_path=file_path,
            frontmatter=frontmatter,
            wiki_links=wiki_links,
            tags=tags,
            created_date=created,
            modified_date=modified,
            note_id=file_path.stem
        )

    def parse_vault(self, vault_path: Path) -> ObsidianVault:
        """Parse notes by vault-relative, extensionless POSIX path.

        Failed note reads remain in ``note_ids`` and ``errors`` so an
        unreadable duplicate cannot make a short link appear unambiguous.
        """
        vault_path = Path(vault_path)
        if not vault_path.exists() or not vault_path.is_dir():
            raise ValueError(f"Invalid vault path: {vault_path}")

        vault = ObsidianVault(name=vault_path.name, root_path=vault_path)
        templates_dir = vault_path / 'Templates'

        for md_file in sorted(vault_path.rglob('*.md')):
            if (md_file.name.startswith('.')
                    or templates_dir in md_file.parents):
                continue
            relative_path = md_file.relative_to(vault_path)
            note_id = relative_path.with_suffix('').as_posix()
            vault.note_ids.add(note_id)
            try:
                note = self.parse_note(md_file)
                note.note_id = note_id
                vault.notes[note_id] = note
                logger.debug("Parsed note: %s", note_id)
            except Exception as e:
                vault.errors[relative_path.as_posix()] = str(e)
                logger.warning("Could not parse %s: %s", md_file, e)

        attachment_extensions = {
            '.png', '.jpg', '.jpeg', '.gif', '.pdf', '.mp4', '.mp3', '.wav',
            '.doc', '.docx'
        }
        for file_path in vault_path.rglob('*'):
            if (file_path.is_file()
                    and file_path.suffix.lower() in attachment_extensions):
                vault.attachments.add(file_path)

        if templates_dir.exists():
            for template_file in sorted(templates_dir.glob('*.md')):
                try:
                    vault.templates[template_file.stem] = (
                        template_file.read_text(encoding='utf-8')
                    )
                except Exception as e:
                    relative_path = template_file.relative_to(vault_path)
                    vault.errors[relative_path.as_posix()] = str(e)
                    logger.warning(
                        "Could not read template %s: %s", template_file, e
                    )

        logger.info(
            "Parsed vault %r with %s notes, %s attachments, %s templates",
            vault.name, len(vault.notes), len(vault.attachments),
            len(vault.templates)
        )
        return vault


class ObsidianIntegration:
    """Main integration class for Obsidian-ATLAS conversion."""

    def __init__(self, atlas_engine: Optional[ATLASEngine] = None):
        """Initialize the Obsidian integration."""
        self.atlas = atlas_engine or ATLASEngine()
        self.parser = ObsidianParser()
        self.imported_notes = {}
        self.exported_files = set()
        self.created_patterns = set()

    def import_vault(self, vault_path: Path,
                     create_patterns_from_tags: bool = True,
                     create_entities_from_notes: bool = True,
                     link_related_content: bool = True) -> Dict:
        """Refresh source-owned fields, preserving unrelated ATLAS data."""
        vault = self.parser.parse_vault(vault_path)
        vault_key = str(vault.root_path.resolve())
        # Ignore views of records already in this engine, not source notes.
        # A fresh engine can still import an exported vault.
        for note_id, note in list(vault.notes.items()):
            frontmatter = note.frontmatter
            if frontmatter.get('atlas_export') is not True:
                continue
            if (frontmatter.get('type') == 'index'
                    or frontmatter.get('entity_id') in self.atlas.entities
                    or frontmatter.get('pattern_id') in self.atlas.patterns):
                del vault.notes[note_id]
                vault.note_ids.discard(note_id)
        import_stats: Dict[str, Any] = {
            'notes_processed': 0,
            'entities_created': 0,
            'entities_updated': 0,
            'patterns_created': 0,
            'relationships_created': 0,
            'errors': [
                f"Error reading '{path}': {error}"
                for path, error in vault.errors.items()
            ]
        }
        self.imported_notes, blocked = self._map_existing_notes(
            vault, vault_key, import_stats['errors']
        )

        if create_patterns_from_tags:
            all_tags = {
                tag for note in vault.notes.values() for tag in note.tags
            }
            for tag in sorted(all_tags):
                pattern_id = self._tag_pattern_id(tag)
                if pattern_id in self.atlas.patterns:
                    self.created_patterns.add(pattern_id)
                    continue
                try:
                    pattern = Pattern(
                        pattern_id=pattern_id,
                        qkit=[f"what_is_{tag.replace('/', '_')}",
                              f"how_to_{tag.replace('/', '_')}",
                              f"examples_of_{tag.replace('/', '_')}"],
                        attributes={
                            'source': 'obsidian',
                            'tag': tag,
                            'domain': tag.split('/')[0],
                            'pattern_type': 'tag_based'
                        }
                    )
                    if not self.atlas.add_pattern(
                        pattern.id, pattern.to_dict()
                    ):
                        raise ValueError("ATLAS rejected the pattern")
                    self.created_patterns.add(pattern_id)
                    import_stats['patterns_created'] += 1
                except Exception as e:
                    import_stats['errors'].append(
                        f"Error creating pattern for tag '{tag}': {e}"
                    )

        refreshed = set()
        if create_entities_from_notes:
            for note_id, note in vault.notes.items():
                if note_id in blocked:
                    continue
                try:
                    entity_id = self.imported_notes.get(note_id)
                    is_new = entity_id is None
                    if is_new:
                        entity_id = "obsidian_note_" + self._source_key(
                            vault_key, note_id
                        )
                        if self.atlas.get_node(entity_id) is not None:
                            raise ValueError(
                                f"Entity identity {entity_id!r} already in use"
                            )
                    note_patterns = None
                    if create_patterns_from_tags:
                        note_patterns = [
                            self._tag_pattern_id(tag)
                            for tag in sorted(note.tags)
                            if self._tag_pattern_id(tag) in self.atlas.patterns
                        ]
                    entity_data = self._note_entity_data(
                        note, entity_id, vault_key, note_patterns
                    )
                    if not self.atlas.add_entity(entity_id, entity_data):
                        raise ValueError("ATLAS rejected the entity")
                    self.imported_notes[note_id] = entity_id
                    refreshed.add(note_id)
                    count_key = (
                        'entities_created' if is_new else 'entities_updated'
                    )
                    import_stats[count_key] += 1
                    import_stats['notes_processed'] += 1
                except Exception as e:
                    import_stats['errors'].append(
                        f"Error importing '{note_id}.md': {e}"
                    )

        if link_related_content:
            for note_id, note in vault.notes.items():
                if note_id in blocked:
                    continue
                if create_entities_from_notes and note_id not in refreshed:
                    continue
                source_id = self.imported_notes.get(note_id)
                if source_id is None:
                    continue
                try:
                    targets = set()
                    for link in sorted(note.wiki_links):
                        try:
                            target_note = self._resolve_link(
                                link, note_id, vault.note_ids
                            )
                        except ValueError as e:
                            import_stats['errors'].append(
                                f"Error linking '{note_id}.md': {e}"
                            )
                            continue
                        target_id = self.imported_notes.get(target_note)
                        if target_id is not None and target_id != source_id:
                            targets.add(target_id)
                    relationships = [
                        (source_id, target_id, 'references')
                        for target_id in sorted(targets)
                    ]
                    owner = "obsidian:" + self._source_key(vault_key, note_id)
                    if not self.atlas.replace_owned_relationships(
                        owner, relationships
                    ):
                        raise ValueError("ATLAS rejected source relationships")
                    import_stats['relationships_created'] += len(relationships)
                except Exception as e:
                    import_stats['errors'].append(
                        f"Error linking '{note_id}.md': {e}"
                    )

        logger.info("Import completed: %s", import_stats)
        return import_stats

    @staticmethod
    def _source_key(vault_key: str, note_id: str) -> str:
        """Bind a relative note identity to its vault without lossy names."""
        identity = json.dumps([vault_key, note_id], ensure_ascii=False)
        return hashlib.sha256(identity.encode('utf-8')).hexdigest()

    @staticmethod
    def _tag_pattern_id(tag: str) -> str:
        return f"obsidian_tag_{tag.replace('/', '_').replace('-', '_')}"

    def _map_existing_notes(
        self, vault: ObsidianVault, vault_key: str, errors: List[str]
    ) -> tuple[Dict[str, str], Set[str]]:
        """Reuse proven identities; refuse non-unique legacy associations."""
        claims = {note_id: [] for note_id in vault.note_ids}
        paths = {
            str((vault.root_path / f"{note_id}.md").resolve()): note_id
            for note_id in vault.note_ids
        }
        legacy_ids: Dict[str, List[str]] = {}
        for note_id in sorted(vault.note_ids):
            title = posixpath.basename(note_id)
            legacy_id = "obsidian_note_" + title.replace(' ', '_')
            legacy_ids.setdefault(legacy_id, []).append(note_id)

        blocked = set()
        for entity_id, data in self.atlas.entities.items():
            ownership = data.get('obsidian', {})
            if ownership:
                note_id = ownership.get('note_id')
                if (ownership.get('vault_path') == vault_key
                        and note_id in claims):
                    claims[note_id].append(entity_id)
                continue
            attributes = data.get('attributes', {})
            if (attributes.get('source') != 'obsidian'
                    and data.get('metadata', {}).get('source')
                    != 'obsidian_import'):
                continue
            file_path = attributes.get('file_path')
            if file_path:
                try:
                    note_id = paths.get(str(Path(file_path).resolve()))
                except (TypeError, ValueError, OSError) as e:
                    blocked.update(legacy_ids.get(entity_id, []))
                    errors.append(
                        f"Invalid legacy path for {entity_id!r}: {e}"
                    )
                    continue
                if note_id is not None:
                    claims[note_id].append(entity_id)
                continue
            candidates = legacy_ids.get(entity_id, [])
            if len(candidates) == 1:
                claims[candidates[0]].append(entity_id)
            elif candidates:
                blocked.update(candidates)
                errors.append(
                    f"AMBIGUOUS legacy mapping {entity_id!r}: {candidates}"
                )

        mapping = {}
        for note_id, entity_ids in claims.items():
            if len(entity_ids) > 1:
                blocked.add(note_id)
                errors.append(
                    f"AMBIGUOUS mapping for '{note_id}.md': {entity_ids}"
                )
            elif entity_ids and note_id not in blocked:
                mapping[note_id] = entity_ids[0]
        return mapping, blocked

    def _note_entity_data(
        self, note: ObsidianNote, entity_id: str, vault_key: str,
        note_patterns: Optional[List[str]]
    ) -> Dict[str, Any]:
        """Refresh recorded source fields, retaining unrelated ATLAS state."""
        previous = self.atlas.entities.get(entity_id, {})
        ownership = previous.get('obsidian', {})
        old_attributes = previous.get('attributes', {})
        old_tags = ownership.get('tags', old_attributes.get('tags', []))
        manual_attribute_tags = set(old_attributes.get('tags', [])) - set(
            ownership.get('attribute_tags', old_tags)
        )
        manual_metadata_tags = set(
            previous.get('metadata', {}).get('tags', [])
        ) - set(ownership.get('metadata_tags', old_tags))
        source_attributes = {
            'title': note.title,
            'content': (
                note.content[:1000] + '...'
                if len(note.content) > 1000 else note.content
            ),
            'file_path': str(note.file_path.resolve()),
            'source': 'obsidian',
            'tags': sorted(note.tags | manual_attribute_tags),
            'wiki_links': sorted(note.wiki_links),
            'created_date': (
                note.created_date.isoformat() if note.created_date else None
            ),
            'modified_date': (
                note.modified_date.isoformat() if note.modified_date else None
            ),
            'content_length': len(note.content),
            'has_frontmatter': bool(note.frontmatter)
        }
        for key, value in note.frontmatter.items():
            if key not in source_attributes:
                source_attributes[f"fm_{key}"] = value

        previous_keys = ownership.get('attribute_keys')
        if previous_keys is None:
            # Legacy imports reserved the core fields and the fm_ namespace.
            previous_keys = set(source_attributes) | {
                key for key in old_attributes if key.startswith('fm_')
            }
        conflicts = (
            set(source_attributes) & set(old_attributes) - set(previous_keys)
        )
        if conflicts:
            raise ValueError(
                "Source fields conflict with manual attributes: "
                f"{sorted(conflicts)}"
            )
        attributes = {
            key: value for key, value in old_attributes.items()
            if key not in previous_keys
        }
        attributes.update(source_attributes)

        previous_patterns = ownership.get('pattern_ids')
        if previous_patterns is None:
            previous_patterns = [
                self._tag_pattern_id(tag) for tag in old_tags
            ]
        patterns = list(previous.get('patterns', []))
        if note_patterns is not None:
            patterns = [
                pattern for pattern in patterns
                if pattern not in previous_patterns
            ]
            note_patterns = [
                pattern for pattern in dict.fromkeys(note_patterns)
                if pattern not in patterns
            ]
            patterns.extend(note_patterns)
        else:
            note_patterns = previous_patterns

        data = dict(previous) if previous else Entity(
            entity_id=entity_id,
            metadata=EntityMetadata(
                created_at=note.created_date or datetime.now(),
                updated_at=note.modified_date or datetime.now(),
                source='obsidian_import'
            )
        ).to_dict()
        metadata = dict(data.get('metadata', {}))
        metadata['updated_at'] = (
            note.modified_date or datetime.now()
        ).isoformat()
        metadata['tags'] = sorted(
            note.tags | manual_metadata_tags
        )
        data.update({
            'attributes': attributes,
            'patterns': patterns,
            'metadata': metadata,
            'obsidian': {
                'vault_path': vault_key,
                'note_id': note.note_id,
                'attribute_keys': sorted(source_attributes),
                'pattern_ids': list(note_patterns),
                'tags': sorted(note.tags),
                'attribute_tags': sorted(note.tags - manual_attribute_tags),
                'metadata_tags': sorted(note.tags - manual_metadata_tags),
            }
        })
        return data

    @staticmethod
    def _resolve_link(link: str, source_note: str,
                      note_ids: Set[str]) -> Optional[str]:
        """Resolve qualified links or a unique short name, never a guess."""
        target = link.split('#', 1)[0].strip()
        if target.lower().endswith('.md'):
            target = target[:-3]
        if not target:
            return source_note
        if '/' in target:
            if target.startswith(('./', '../')):
                target = posixpath.join(posixpath.dirname(source_note), target)
            target = posixpath.normpath(target.lstrip('/'))
            return target if target in note_ids else None
        candidates = sorted(
            note_id for note_id in note_ids
            if posixpath.basename(note_id) == target
        )
        if len(candidates) > 1:
            raise ValueError(
                f"Ambiguous wiki link {link!r}; qualify one of {candidates}"
            )
        return candidates[0] if candidates else None

    def export_to_vault(self, output_path: Path,
                        vault_name: str = "ATLAS_Export",
                        include_entities: bool = True,
                        include_patterns: bool = True,
                        create_index: bool = True) -> Dict[str, Any]:
        """Export selected records using one collision-free vault path map."""
        vault_path = output_path / vault_name
        vault_path.mkdir(parents=True, exist_ok=True)
        export_stats: Dict[str, Any] = {
            'files_created': 0,
            'entities_exported': 0,
            'patterns_exported': 0,
            'errors': []
        }
        paths = self._allocate_export_paths(
            vault_path, include_entities, include_patterns, create_index
        )
        written = set()
        if include_entities:
            (vault_path / "Entities").mkdir(exist_ok=True)
            for entity_id, entity_data in self.atlas.entities.items():
                try:
                    self._export_entity_as_note(
                        entity_id, entity_data, vault_path, paths
                    )
                    written.add(('entity', entity_id))
                    export_stats['entities_exported'] += 1
                    export_stats['files_created'] += 1
                except Exception as e:
                    export_stats['errors'].append(
                        f"Error exporting entity '{entity_id}': {e}"
                    )

        if include_patterns:
            (vault_path / "Patterns").mkdir(exist_ok=True)
            for pattern_id, pattern_data in self.atlas.patterns.items():
                try:
                    self._export_pattern_as_note(
                        pattern_id, pattern_data, vault_path, paths
                    )
                    written.add(('pattern', pattern_id))
                    export_stats['patterns_exported'] += 1
                    export_stats['files_created'] += 1
                except Exception as e:
                    export_stats['errors'].append(
                        f"Error exporting pattern '{pattern_id}': {e}"
                    )

        if create_index:
            try:
                self._create_vault_index(
                    vault_path, export_stats, paths, written
                )
                export_stats['files_created'] += 1
            except Exception as e:
                export_stats['errors'].append(f"Error creating index: {e}")

        logger.info("Export completed: %s", export_stats)
        return export_stats

    def _allocate_export_paths(self, vault_path: Path, include_entities: bool,
                               include_patterns: bool,
                               create_index: bool) -> Dict[tuple, Path]:
        """Reserve case-insensitive paths without replacing unrelated files."""
        records = []
        if include_entities:
            records.extend(
                ('entity', entity_id, 'Entities',
                 data.get('attributes', {}).get('title', entity_id))
                for entity_id, data in self.atlas.entities.items()
            )
        if include_patterns:
            records.extend(
                ('pattern', pattern_id, 'Patterns',
                 data.get('attributes', {}).get('name', pattern_id))
                for pattern_id, data in self.atlas.patterns.items()
            )
        if create_index:
            records.append(('index', '', '', 'README'))

        occupied = {
            unicodedata.normalize(
                'NFC', path.relative_to(vault_path).as_posix()
            ).casefold(): path
            for path in vault_path.rglob('*')
        }
        allocated = {}
        used = set()
        for kind, record_id, directory, title in sorted(records):
            base = self._sanitize_filename(str(title))
            suffix = 1
            while True:
                filename = base if suffix == 1 else f"{base}__{suffix}"
                relative = Path(directory) / f"{filename}.md"
                key = unicodedata.normalize(
                    'NFC', relative.as_posix()
                ).casefold()
                existing = occupied.get(key)
                reusable = existing is None
                if (existing is not None and not existing.is_symlink()
                        and existing.is_file()):
                    try:
                        frontmatter, _ = self.parser.parse_frontmatter(
                            existing.read_text(encoding='utf-8')
                        )
                        reusable = (
                            frontmatter.get('atlas_export') is True
                            and frontmatter.get('type') == kind
                            and (kind == 'index'
                                 or frontmatter.get(f'{kind}_id') == record_id)
                        )
                    except (OSError, UnicodeError):
                        reusable = False
                if key not in used and reusable:
                    if existing is not None:
                        relative = existing.relative_to(vault_path)
                    allocated[(kind, record_id)] = relative
                    used.add(key)
                    break
                suffix += 1
        return allocated

    @staticmethod
    def _export_link(kind: str, record_id: str,
                     paths: Dict[tuple, Path]) -> str:
        """Link to an allocated vault path; render unexported IDs as text."""
        path = paths.get((kind, record_id))
        if path is None:
            return record_id
        return f"[[{path.with_suffix('').as_posix()}]]"

    def _export_entity_as_note(
        self, entity_id: str, entity_data: Dict[str, Any], vault_path: Path,
        paths: Dict[tuple, Path]
    ) -> None:
        """Export a single entity as an Obsidian note."""
        # Create frontmatter
        frontmatter = {
            'type': 'entity',
            'entity_id': entity_id,
            'atlas_export': True,
            'created': datetime.now().isoformat(),
            'tags': ['atlas-entity']
        }

        # Add entity attributes to frontmatter
        attributes = entity_data.get('attributes', {})
        if 'tags' in attributes:
            existing_tags = frontmatter.get('tags', [])
            if (isinstance(existing_tags, list)
                    and isinstance(attributes['tags'], list)):
                existing_tags.extend(attributes['tags'])
                frontmatter['tags'] = existing_tags

        # Create content
        title = attributes.get('title', entity_id)
        content = f"# {title}\n\n"

        # Add description or content
        if 'content' in attributes:
            content += f"{attributes['content']}\n\n"
        elif 'description' in attributes:
            content += f"{attributes['description']}\n\n"

        # Add metadata section
        content += "## Metadata\n\n"
        for key, value in attributes.items():
            if key not in ['title', 'content', 'description', 'tags']:
                content += f"- **{key}**: {value}\n"

        # Add patterns section
        patterns = entity_data.get('patterns', [])
        if patterns:
            content += "\n## Related Patterns\n\n"
            for pattern in patterns:
                link = self._export_link('pattern', pattern, paths)
                content += f"- {link}\n"

        # Include every occurrence, including repeated manual relationships.
        relationships = self.atlas.get_relationships(entity_id)
        if relationships:
            content += "\n## Relationships\n\n"
            for target_id, rel_type in relationships:
                target_data = self.atlas.get_node(target_id)
                if target_data:
                    link = self._export_link(
                        target_data['type'], target_id, paths
                    )
                    content += (
                        f"- **{str(rel_type).replace('_', ' ').title()}**: {link}\n"
                    )

        file_path = vault_path / paths[('entity', entity_id)]

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("---\n")
                yaml.dump(frontmatter, f, default_flow_style=False)
                f.write("---\n\n")
                f.write(content)

            self.exported_files.add(file_path)
            logger.debug("Exported entity %s to %s", entity_id, file_path)
        except Exception as e:
            logger.error("Failed to write entity file %s: %s", file_path, e)
            raise

    def _export_pattern_as_note(self, pattern_id: str,
                                pattern_data: Dict[str, Any], vault_path: Path,
                                paths: Dict[tuple, Path]) -> None:
        """Export a single pattern as an Obsidian note."""
        # Create frontmatter
        frontmatter = {
            'type': 'pattern',
            'pattern_id': pattern_id,
            'atlas_export': True,
            'created': datetime.now().isoformat(),
            'tags': ['atlas-pattern']
        }

        # Add pattern attributes to frontmatter
        attributes = pattern_data.get('attributes', {})
        if 'domain' in attributes:
            frontmatter['domain'] = attributes['domain']

        # Create content
        title = attributes.get('name', pattern_id)
        content = f"# {title}\n\n"

        # Add description
        if 'description' in attributes:
            content += f"{attributes['description']}\n\n"

        # Add qkit section
        qkit = pattern_data.get('qkit', [])
        if qkit:
            content += "## Key Questions (QKit)\n\n"
            for question in qkit:
                content += f"- {question}\n"
            content += "\n"

        # Add attributes section
        content += "## Pattern Attributes\n\n"
        for key, value in attributes.items():
            if key not in ['name', 'description']:
                content += f"- **{key}**: {value}\n"

        # Add related entities section
        related_entities = self._find_entities_using_pattern(pattern_id)
        if related_entities:
            content += "\n## Related Entities\n\n"
            for entity_id in related_entities:
                link = self._export_link('entity', entity_id, paths)
                content += f"- {link}\n"

        file_path = vault_path / paths[('pattern', pattern_id)]

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("---\n")
                yaml.dump(frontmatter, f, default_flow_style=False)
                f.write("---\n\n")
                f.write(content)

            self.exported_files.add(file_path)
            logger.debug("Exported pattern %s to %s", pattern_id, file_path)
        except Exception as e:
            logger.error("Failed to write pattern file %s: %s", file_path, e)
            raise

    def _find_entities_using_pattern(self, pattern_id: str) -> List[str]:
        """Find entities that use a specific pattern."""
        related_entities = []
        for entity_id, entity_data in self.atlas.entities.items():
            entity_patterns = entity_data.get('patterns', [])
            if pattern_id in entity_patterns:
                related_entities.append(entity_id)
        return related_entities

    def _create_vault_index(
        self, vault_path: Path, export_stats: Dict[str, Any],
        paths: Dict[tuple, Path], written: Set[tuple]
    ) -> None:
        """Create an index file for the exported vault."""
        frontmatter = {
            'type': 'index',
            'atlas_export': True,
            'created': datetime.now().isoformat(),
            'tags': ['atlas-index', 'navigation']
        }

        content = "# ATLAS Knowledge Vault\n\n"
        content += "This vault contains knowledge exported from ATLAS.\n\n"

        # Add export statistics
        content += "## Export Statistics\n\n"
        content += (
            f"- Entities exported: {export_stats['entities_exported']}\n"
            f"- Patterns exported: {export_stats['patterns_exported']}\n"
        )
        content += f"- Total files created: {export_stats['files_created']}\n"
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        content += f"- Export date: {timestamp}\n\n"

        # Index current successes, never stale files from previous exports.
        for kind, heading in [('entity', 'Entities'), ('pattern', 'Patterns')]:
            records = sorted(key for key in written if key[0] == kind)
            if records:
                content += f"## {heading}\n\n"
                for _, record_id in records:
                    content += (
                        f"- {self._export_link(kind, record_id, paths)}\n"
                    )
                content += "\n"

        index_path = vault_path / paths[('index', '')]
        try:
            with open(index_path, 'w', encoding='utf-8') as f:
                f.write("---\n")
                yaml.dump(frontmatter, f, default_flow_style=False)
                f.write("---\n\n")
                f.write(content)
            self.exported_files.add(index_path)
            logger.debug(f"Created vault index at {index_path}")
        except Exception as e:
            logger.error(f"Failed to write index file: {e}")
            raise

    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize a filename for safe use across platforms."""
        # Replace problematic characters
        safe_chars = ".-_() "
        sanitized = ""
        for char in unicodedata.normalize('NFC', filename):
            if char.isalnum() or char in safe_chars:
                sanitized += char
            else:
                sanitized += "_"

        # Limit length and clean up
        sanitized = sanitized.strip(' .')[:100].rstrip(' .')
        sanitized = re.sub(r'_+', '_', sanitized)
        sanitized = sanitized.encode('utf-8')[:200].decode('utf-8', 'ignore')
        return sanitized or "note"

    def sync_vault(self, vault_path: Path,
                   sync_mode: str = "bidirectional") -> Dict[str, Any]:
        """Synchronize an Obsidian vault with ATLAS data."""
        if sync_mode not in ["import", "export", "bidirectional"]:
            raise ValueError(
                "sync_mode must be 'import', 'export', or 'bidirectional'"
            )

        sync_stats: Dict[str, Any] = {
            'mode': sync_mode,
            'timestamp': datetime.now().isoformat(),
            'import_stats': {},
            'export_stats': {}
        }

        if sync_mode in ["import", "bidirectional"]:
            sync_stats['import_stats'] = self.import_vault(vault_path)

        if sync_mode in ["export", "bidirectional"]:
            sync_stats['export_stats'] = self.export_to_vault(
                vault_path.parent, vault_path.name
            )

        logger.info(f"Sync completed in {sync_mode} mode")
        return sync_stats

    def get_integration_stats(self) -> Dict[str, Any]:
        """Get statistics about the integration state."""
        return {
            'imported_notes': len(self.imported_notes),
            'exported_files': len(self.exported_files),
            'created_patterns': len(self.created_patterns),
            'atlas_entities': len(self.atlas.entities),
            'atlas_patterns': len(self.atlas.patterns),
            'atlas_queries': len(self.atlas.queries),
            'atlas_metrics': self.atlas.get_metrics()
        }

    def export_data_as_json(self, output_path: Path) -> Dict[str, Any]:
        """Export ATLAS data as JSON with proper serialization."""
        export_data = {
            'metadata': {
                'export_timestamp': datetime.now().isoformat(),
                'atlas_version': '1.0.0',
                'total_entities': len(self.atlas.entities),
                'total_patterns': len(self.atlas.patterns),
                'total_queries': len(self.atlas.queries)
            },
            'entities': self.atlas.entities,
            'patterns': self.atlas.patterns,
            'queries': self.atlas.queries,
            'integration_stats': self.get_integration_stats()
        }

        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, cls=ATLASJSONEncoder, indent=2)
            logger.info(f"Exported ATLAS data to {output_path}")
            return {'success': True, 'file_path': str(output_path)}
        except Exception as e:
            logger.error(f"Failed to export JSON data: {e}")
            return {'success': False, 'error': str(e)}