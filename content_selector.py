"""Persona-based content selection logic."""
from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from typing import Iterable, List, Optional, Sequence

from llm_providers import LLMProvider
from xml_parser import ContentItem, format_items_for_prompt

logger = logging.getLogger(__name__)


@dataclass
class Selection:
    """Represents a single recommendation returned by the LLM."""

    title: str
    reason: str
    score: Optional[float] = None


@dataclass
class SelectionResult:
    """Return structure for persona evaluations."""

    persona: str
    raw_response: str
    selections: Sequence[Selection]


PROMPT_TEMPLATE = """You are an expert financial literacy instructional designer.
Given the following persona description, recommend the top {top_n} most relevant financial education resources from the provided content library.
Frame each suggestion around the persona's goals and responsibilities while highlighting the financial skills or knowledge they will gain.
Provide a short reason for each recommendation and include a relevance score between 0 and 1.

Persona description:
{persona}

Content library:
{content}

Respond in JSON with the following structure:
{{
  "recommendations": [
    {{"title": "...", "reason": "...", "score": 0.0}}
  ]
}}
If JSON is not possible, provide a numbered list with titles and reasons.
"""


class ContentSelector:
    """Uses an :class:`LLMProvider` to select content for personas."""

    def __init__(self, provider: LLMProvider, content_items: Iterable[ContentItem], top_n: int = 3):
        self.provider = provider
        self.items: List[ContentItem] = list(content_items)
        if not self.items:
            raise ValueError("ContentSelector requires at least one content item")
        self.top_n = max(1, top_n)

    def build_prompt(self, persona_description: str) -> str:
        library_text = format_items_for_prompt(self.items)
        return PROMPT_TEMPLATE.format(
            top_n=self.top_n,
            persona=persona_description.strip(),
            content=library_text,
        )

    def select_content(self, persona_description: str, system_prompt: str | None = None) -> SelectionResult:
        prompt = self.build_prompt(persona_description)
        response = self.provider.generate(prompt, system_prompt=system_prompt)
        selections = self._parse_response(response)
        return SelectionResult(persona=persona_description, raw_response=response, selections=selections)

    def _parse_response(self, response: str) -> Sequence[Selection]:
        parsers = [self._parse_json_block, self._parse_numbered_list]
        for parser in parsers:
            selections = parser(response)
            if selections:
                return selections[: self.top_n]
        logger.warning("Unable to parse LLM response, returning empty selection")
        return []

    def _parse_json_block(self, response: str) -> List[Selection]:
        pattern = re.compile(r"\{.*\}", re.DOTALL)
        match = pattern.search(response)
        if not match:
            return []
        block = match.group(0)
        try:
            data = json.loads(block)
        except json.JSONDecodeError:
            return []
        recommendations = data.get("recommendations")
        if not isinstance(recommendations, list):
            return []
        selections: List[Selection] = []
        for item in recommendations:
            title = item.get("title") if isinstance(item, dict) else None
            reason = item.get("reason") if isinstance(item, dict) else None
            score = item.get("score") if isinstance(item, dict) else None
            if not title or not reason:
                continue
            try:
                score_value = float(score) if score is not None else None
            except (TypeError, ValueError):
                score_value = None
            selections.append(Selection(title=title.strip(), reason=reason.strip(), score=score_value))
        return selections

    def _parse_numbered_list(self, response: str) -> List[Selection]:
        selections: List[Selection] = []
        pattern = re.compile(r"^\s*(\d+)[\).\-]\s*(.+)$", re.MULTILINE)
        for match in pattern.finditer(response):
            line = match.group(2).strip()
            parts = re.split(r"\s+-\s+|:\s+", line, maxsplit=1)
            if len(parts) == 2:
                title, reason = parts
            else:
                fragments = line.split("-", 1)
                if len(fragments) == 2:
                    title, reason = fragments
                else:
                    title = line
                    reason = "No reason provided"
            selections.append(Selection(title=title.strip(), reason=reason.strip()))
        return selections


__all__ = [
    "ContentSelector",
    "Selection",
    "SelectionResult",
]
