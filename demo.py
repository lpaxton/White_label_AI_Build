"""Interactive demonstration script for the persona-based content selector."""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from typing import Dict, Iterable, List, Sequence

from content_selector import ContentSelector
from xml_parser import ContentItem


@dataclass
class MockLLMProvider:
    """Simple mock provider that uses keyword matching to produce recommendations."""

    model: str = "mock-llm"

    def generate(self, prompt: str, **_: str) -> str:
        persona_section = prompt.split("Persona description:", 1)[-1].split("Content library:", 1)[0]
        keywords = {word.lower() for word in persona_section.split() if len(word) > 4}
        recommendations: List[Dict[str, object]] = []
        for line in prompt.split("Content library:")[-1].splitlines():
            if not line.strip():
                continue
            title = line.split("|", 1)[0]
            score = 0.1
            for keyword in keywords:
                if keyword in line.lower():
                    score += 0.2
            if score > 0.2:
                recommendations.append({"title": title.split(".", 1)[-1].strip(), "reason": f"Matched keywords {sorted(keywords)[:2]}", "score": min(score, 1.0)})
        recommendations = recommendations[:3] or [
            {
                "title": prompt.split("Content library:")[-1].splitlines()[0].split(".", 1)[-1].strip(),
                "reason": "Default suggestion from mock provider",
                "score": 0.3,
            }
        ]
        return json.dumps({"recommendations": recommendations})


def load_sample_items() -> Sequence[ContentItem]:
    return [
        ContentItem(
            title="Cloud Architecture Foundations",
            description="Introduction to cloud service models",
            category="Cloud",
            difficulty="Intermediate",
            tags=["cloud", "architecture"],
        ),
        ContentItem(
            title="Design Thinking for Product Managers",
            description="Workshop on applying design thinking",
            category="Product",
            difficulty="Beginner",
            tags=["design", "product"],
        ),
        ContentItem(
            title="Marketing Analytics with SQL",
            description="Analyze campaign performance with SQL",
            category="Marketing",
            difficulty="Intermediate",
            tags=["marketing", "sql"],
        ),
        ContentItem(
            title="Inclusive Leadership Essentials",
            description="Strategies for creating inclusive teams",
            category="Leadership",
            difficulty="Intermediate",
            tags=["leadership", "inclusion"],
        ),
    ]


def run_demo(personas: Iterable[str]) -> None:
    provider = MockLLMProvider()
    selector = ContentSelector(provider, load_sample_items(), top_n=3)
    for persona in personas:
        result = selector.select_content(persona)
        print("Persona:", persona)
        for selection in result.selections:
            print(f" - {selection.title}: {selection.reason} (score={selection.score})")
        print()


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Demo for the persona-based content selector")
    parser.add_argument(
        "personas",
        nargs="*",
        default=[
            "Newly promoted engineering manager leading a distributed team",
            "Marketing manager seeking data storytelling skills",
            "Operations lead preparing for a cloud migration",
        ],
        help="Optional persona descriptions to run through the mock provider",
    )
    args = parser.parse_args(argv)
    run_demo(args.personas)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
