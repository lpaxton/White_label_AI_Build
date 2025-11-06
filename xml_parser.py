"""Utilities for parsing XML content files."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional
import xml.etree.ElementTree as ET


@dataclass
class ContentItem:
    """Represents a single learning content item extracted from XML."""

    title: str
    description: str
    category: Optional[str] = None
    difficulty: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    duration: Optional[str] = None
    metadata: Dict[str, str] = field(default_factory=dict)

    def to_prompt_fragment(self, index: int) -> str:
        """Return a human readable string for LLM prompting."""
        parts = [f"{index}. {self.title.strip()}"]
        if self.category:
            parts.append(f"Category: {self.category.strip()}")
        if self.difficulty:
            parts.append(f"Difficulty: {self.difficulty.strip()}")
        if self.duration:
            parts.append(f"Duration: {self.duration.strip()}")
        if self.tags:
            parts.append("Tags: " + ", ".join(tag.strip() for tag in self.tags))
        parts.append("Description: " + self.description.strip())
        return " | ".join(parts)


class XMLContentError(RuntimeError):
    """Raised when the XML content file is invalid."""


def _read_text(element: Optional[ET.Element]) -> Optional[str]:
    if element is None or element.text is None:
        return None
    text = element.text.strip()
    return text or None


def _collect_tags(element: Optional[ET.Element]) -> List[str]:
    if element is None:
        return []
    tags: List[str] = []
    for child in element:
        value = _read_text(child)
        if value:
            tags.append(value)
    return tags


def _extract_metadata(element: Optional[ET.Element]) -> Dict[str, str]:
    if element is None:
        return {}
    metadata: Dict[str, str] = {}
    for child in element:
        text = _read_text(child)
        if text:
            metadata[child.tag] = text
    return metadata


def parse_content_xml(path: str | Path) -> List[ContentItem]:
    """Parse ``path`` and return a list of :class:`ContentItem` objects."""
    file_path = Path(path).expanduser().resolve()
    if not file_path.exists():
        raise XMLContentError(f"XML content file not found: {file_path}")

    try:
        tree = ET.parse(file_path)
    except ET.ParseError as exc:  # pragma: no cover - pass through for clarity
        raise XMLContentError(f"Failed to parse XML file {file_path}: {exc}") from exc

    root = tree.getroot()
    if root.tag.lower() not in {"content", "items", "library"}:
        raise XMLContentError(
            "Root element must be <content>, <items>, or <library>, "
            f"got <{root.tag}>"
        )

    items: List[ContentItem] = []
    for item_el in root.findall(".//item"):
        title = _read_text(item_el.find("title"))
        description = _read_text(item_el.find("description"))
        if not title or not description:
            raise XMLContentError("Each <item> must include <title> and <description> elements")

        category = _read_text(item_el.find("category"))
        difficulty = _read_text(item_el.find("difficulty"))
        duration = _read_text(item_el.find("duration"))
        tags = _collect_tags(item_el.find("tags"))
        metadata = _extract_metadata(item_el.find("metadata"))

        items.append(
            ContentItem(
                title=title,
                description=description,
                category=category,
                difficulty=difficulty,
                tags=tags,
                duration=duration,
                metadata=metadata,
            )
        )

    if not items:
        raise XMLContentError("XML file does not contain any <item> elements")

    return items


def format_items_for_prompt(items: Iterable[ContentItem]) -> str:
    """Return a formatted string representing the content library."""
    formatted = [item.to_prompt_fragment(index + 1) for index, item in enumerate(items)]
    return "\n".join(formatted)


__all__ = [
    "ContentItem",
    "XMLContentError",
    "parse_content_xml",
    "format_items_for_prompt",
]
