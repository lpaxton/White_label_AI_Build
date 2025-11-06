"""Command line interface for the persona-based content selector."""
from __future__ import annotations

import argparse
import os
import sys
from typing import Iterable, Sequence

from content_selector import ContentSelector, SelectionResult
from llm_providers import create_provider
from xml_parser import XMLContentError, parse_content_xml


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Persona-based content selection tool")
    parser.add_argument("--provider", required=True, choices=["openai", "anthropic", "ollama"], help="LLM provider to use")
    parser.add_argument("--model", help="Model identifier for the selected provider")
    parser.add_argument("--xml-file", default="sample_content.xml", help="Path to XML content file")
    parser.add_argument("--persona", help="Persona description for single query mode")
    parser.add_argument("--top-n", type=int, default=3, help="Number of recommendations to request")
    parser.add_argument("--temperature", type=float, default=0.2, help="Sampling temperature for the LLM")
    parser.add_argument(
        "--max-tokens", type=int, default=1024, help="Maximum tokens to request from the provider"
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Start interactive mode to evaluate multiple personas",
    )
    parser.add_argument(
        "--system-prompt",
        default=(
            "You are a seasoned financial education strategist who curates actionable financial literacy learning plans."
        ),
        help="Custom system prompt passed to the provider",
    )
    return parser.parse_args(argv)


def load_content(xml_file: str) -> Iterable:
    try:
        return parse_content_xml(xml_file)
    except XMLContentError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


def create_selector(args: argparse.Namespace) -> ContentSelector:
    provider = create_provider(
        args.provider,
        model=args.model,
        api_key=os.getenv("API_KEY"),  # optional convenience env var used in tests/demo
        temperature=args.temperature,
        max_tokens=args.max_tokens,
    )
    content_items = load_content(args.xml_file)
    return ContentSelector(provider=provider, content_items=content_items, top_n=args.top_n)


def display_result(result: SelectionResult) -> None:
    print("Persona:", result.persona)
    if not result.selections:
        print("No recommendations could be parsed from the provider response.\n")
        print("Raw response:\n" + result.raw_response)
        return
    print("Recommendations:")
    for index, selection in enumerate(result.selections, start=1):
        score_text = f" (score: {selection.score:.2f})" if selection.score is not None else ""
        print(f"  {index}. {selection.title}{score_text}")
        print(f"     Reason: {selection.reason}")
    print()


def interactive_loop(selector: ContentSelector, system_prompt: str) -> None:
    print("Interactive persona mode. Type 'exit' to quit.\n")
    while True:
        try:
            persona = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if persona.lower() in {"exit", "quit"}:
            break
        if not persona:
            continue
        result = selector.select_content(persona, system_prompt)
        display_result(result)


def run_once(selector: ContentSelector, persona: str, system_prompt: str) -> None:
    result = selector.select_content(persona, system_prompt)
    display_result(result)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    selector = create_selector(args)

    if args.interactive or not args.persona:
        interactive_loop(selector, args.system_prompt)
    else:
        run_once(selector, args.persona, args.system_prompt)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
