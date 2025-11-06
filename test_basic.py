import argparse
import json
from pathlib import Path
from textwrap import dedent
from typing import List

import pytest

import main
import xml_parser
from content_selector import ContentSelector
from llm_providers import create_provider


class DummyProvider:
    def __init__(self, response: str):
        self.response = response
        self.model = "dummy-model"
        self.prompts: List[str] = []

    def generate(self, prompt: str, **_: str) -> str:
        self.prompts.append(prompt)
        return self.response


def test_parse_content_xml(tmp_path: Path) -> None:
    xml = dedent(
        """
        <content>
          <item>
            <title>Sample</title>
            <description>Desc</description>
            <tags><tag>a</tag></tags>
          </item>
        </content>
        """
    )
    path = tmp_path / "content.xml"
    path.write_text(xml)
    items = xml_parser.parse_content_xml(path)
    assert len(items) == 1
    assert items[0].title == "Sample"
    assert items[0].tags == ["a"]


def test_parse_content_xml_invalid(tmp_path: Path) -> None:
    path = tmp_path / "missing.xml"
    with pytest.raises(xml_parser.XMLContentError):
        xml_parser.parse_content_xml(path)


def test_content_selector_parses_json(tmp_path: Path) -> None:
    response = json.dumps(
        {
            "recommendations": [
                {"title": "First", "reason": "Relevant", "score": 0.9},
                {"title": "Second", "reason": "Also relevant", "score": 0.7},
            ]
        }
    )
    provider = DummyProvider(response)
    items = [xml_parser.ContentItem(title="X", description="Y")]
    selector = ContentSelector(provider, items, top_n=2)
    result = selector.select_content("Persona")
    assert len(result.selections) == 2
    assert result.selections[0].title == "First"
    assert provider.prompts


def test_content_selector_numbered_list(tmp_path: Path) -> None:
    response = "1) First - because\n2) Second - reason"
    provider = DummyProvider(response)
    items = [xml_parser.ContentItem(title="X", description="Y")]
    selector = ContentSelector(provider, items, top_n=2)
    result = selector.select_content("Persona")
    assert [selection.title for selection in result.selections] == ["First", "Second"]


def test_cli_single_run(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    items = [xml_parser.ContentItem(title="X", description="Y")]
    provider = DummyProvider(
        json.dumps({"recommendations": [{"title": "X", "reason": "Fits", "score": 0.5}]})
    )

    monkeypatch.setattr(
        main,
        "create_selector",
        lambda args: ContentSelector(provider, items),
    )

    args = argparse.Namespace(
        provider="openai",
        model=None,
        xml_file="",
        persona="Persona",
        top_n=1,
        temperature=0.2,
        max_tokens=512,
        interactive=False,
        system_prompt="",
    )

    monkeypatch.setattr(main, "parse_args", lambda _: args)

    main.main(["--provider", "openai"])
    captured = capsys.readouterr()
    assert "Persona:" in captured.out
    assert "Recommendations" in captured.out


def test_create_provider_invalid() -> None:
    with pytest.raises(ValueError):
        create_provider("unknown", model="x")
