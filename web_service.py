"""Minimal web service exposing persona recommendations and a browser UI."""
from __future__ import annotations

import io
import json
import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Dict, List, Sequence
from wsgiref.simple_server import make_server
from wsgiref.util import setup_testing_defaults

from content_selector import ContentSelector
from llm_providers import LLMProvider, create_provider
from xml_parser import ContentItem, XMLContentError, parse_content_xml


@dataclass(frozen=True)
class SelectorResources:
    """Reusable configuration and catalog data for the service."""

    provider: LLMProvider
    top_n: int
    system_prompt: str
    content_items: Sequence[ContentItem]

    def build_selector(self, top_n: int | None = None) -> ContentSelector:
        return ContentSelector(
            provider=self.provider,
            content_items=self.content_items,
            top_n=top_n or self.top_n,
        )


@lru_cache(maxsize=1)
def get_resources() -> SelectorResources:
    provider_name = os.getenv("LLM_PROVIDER", "openai")
    provider_model = os.getenv("LLM_MODEL")
    provider_api_key = os.getenv("API_KEY")
    temperature = float(os.getenv("LLM_TEMPERATURE", "0.2"))
    max_tokens = int(os.getenv("LLM_MAX_TOKENS", "1024"))
    top_n = int(os.getenv("DEFAULT_TOP_N", "3"))
    system_prompt = os.getenv(
        "DEFAULT_SYSTEM_PROMPT",
        "You are a financial literacy specialist who tailors financial education journeys for diverse personas.",
    )
    xml_file = os.getenv("CONTENT_XML_FILE", "sample_content.xml")

    try:
        items = parse_content_xml(xml_file)
    except XMLContentError as exc:  # pragma: no cover - fails fast during startup
        raise RuntimeError(str(exc)) from exc

    provider = create_provider(
        provider_name,
        model=provider_model,
        api_key=provider_api_key,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return SelectorResources(
        provider=provider,
        top_n=top_n,
        system_prompt=system_prompt,
        content_items=tuple(items),
    )


class SelectorService:
    """Implements recommendation logic for both UI and API consumers."""

    def __init__(self, resources: SelectorResources):
        self.resources = resources

    def recommend(self, persona: str, *, top_n: int | None = None, system_prompt: str | None = None) -> Dict[str, object]:
        persona_text = (persona or "").strip()
        if not persona_text:
            raise ValueError("Persona description cannot be empty.")

        if top_n is None:
            requested_top_n = self.resources.top_n
        else:
            try:
                requested_top_n = int(top_n)
            except (TypeError, ValueError) as exc:
                raise ValueError("top_n must be an integer between 1 and 10.") from exc

        if requested_top_n < 1 or requested_top_n > 10:
            raise ValueError("top_n must be between 1 and 10.")

        selector = self.resources.build_selector(top_n=requested_top_n)
        prompt = system_prompt or self.resources.system_prompt
        result = selector.select_content(persona_text, system_prompt=prompt)
        return {
            "persona": result.persona,
            "raw_response": result.raw_response,
            "recommendations": [
                {"title": sel.title, "reason": sel.reason, "score": sel.score}
                for sel in result.selections
            ],
        }

    def content_catalog(self) -> List[Dict[str, object]]:
        catalog: List[Dict[str, object]] = []
        for item in self.resources.content_items:
            catalog.append(
                {
                    "title": item.title,
                    "description": item.description,
                    "category": item.category,
                    "difficulty": item.difficulty,
                    "duration": item.duration,
                    "tags": list(item.tags),
                }
            )
        return catalog

    def render_index(self) -> str:
        preview = [
            {
                "title": item.title,
                "category": item.category,
                "difficulty": item.difficulty,
                "tags": list(item.tags),
            }
            for item in self.resources.content_items[:5]
        ]
        preview_json = json.dumps(preview, indent=2)
        return f"""
        <html>
          <head>
            <title>Financial Literacy Persona Selector</title>
            <style>
              body {{ font-family: Arial, sans-serif; margin: 2rem; background-color: #f8fafc; }}
              h1 {{ color: #0f172a; }}
              textarea {{ width: 100%; min-height: 120px; padding: 0.5rem; font-size: 1rem; }}
              button {{ margin-top: 1rem; padding: 0.75rem 1.5rem; background-color: #2563eb; color: white; border: none; border-radius: 4px; cursor: pointer; }}
              button:disabled {{ background-color: #94a3b8; cursor: not-allowed; }}
              pre {{ background: #0f172a; color: #e2e8f0; padding: 1rem; border-radius: 6px; overflow-x: auto; }}
              .results {{ margin-top: 2rem; }}
            </style>
          </head>
          <body>
            <h1>Financial Literacy Persona Selector</h1>
            <p>Describe the audience persona below to receive tailored financial education recommendations.</p>
            <form id="persona-form">
              <label for="persona">Persona description</label>
              <textarea id="persona" name="persona" placeholder="e.g. Newly promoted operations manager overseeing budgets"></textarea>
              <label for="top_n">Recommendations to return (1-10)</label>
              <input id="top_n" name="top_n" type="number" min="1" max="10" value="{self.resources.top_n}" />
              <button type="submit">Generate recommendations</button>
            </form>
            <div class="results">
              <h2>Recommendations</h2>
              <pre id="output">Awaiting input...</pre>
            </div>
            <div class="results">
              <h2>Sample content library</h2>
              <pre>{preview_json}</pre>
            </div>
            <script>
              const form = document.getElementById('persona-form');
              const output = document.getElementById('output');
              form.addEventListener('submit', async (event) => {{
                event.preventDefault();
                output.textContent = 'Requesting recommendations...';
                const persona = document.getElementById('persona').value;
                const topN = parseInt(document.getElementById('top_n').value, 10);
                const payload = {{ persona }};
                if (!Number.isNaN(topN)) {{
                  payload.top_n = topN;
                }}
                try {{
                  const response = await fetch('/api/recommendations', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify(payload)
                  }});
                  if (!response.ok) {{
                    const errorText = await response.text();
                    output.textContent = `Error: ${{errorText}}`;
                    return;
                  }}
                  const data = await response.json();
                  output.textContent = JSON.stringify(data, null, 2);
                }} catch (error) {{
                  output.textContent = `Request failed: ${{error}}`;
                }}
              }});
            </script>
          </body>
        </html>
        """


def _encode_json(data: object, status: str = "200 OK") -> tuple[str, List[tuple[str, str]], List[bytes]]:
    body = json.dumps(data, indent=2).encode("utf-8")
    headers = [
        ("Content-Type", "application/json; charset=utf-8"),
        ("Content-Length", str(len(body))),
    ]
    return status, headers, [body]


def _encode_html(html: str, status: str = "200 OK") -> tuple[str, List[tuple[str, str]], List[bytes]]:
    body = html.encode("utf-8")
    headers = [
        ("Content-Type", "text/html; charset=utf-8"),
        ("Content-Length", str(len(body))),
    ]
    return status, headers, [body]


def application(environ: Dict[str, object], start_response):
    setup_testing_defaults(environ)
    method = environ.get("REQUEST_METHOD", "GET").upper()
    path = environ.get("PATH_INFO", "")
    service = SelectorService(get_resources())

    if method == "GET" and path in {"", "/"}:
        status, headers, body = _encode_html(service.render_index())
    elif method == "GET" and path == "/api/content":
        status, headers, body = _encode_json(service.content_catalog())
    elif method == "POST" and path == "/api/recommendations":
        length = int(environ.get("CONTENT_LENGTH") or 0)
        raw_body = environ.get("wsgi.input")
        payload_bytes = b""
        if isinstance(raw_body, io.BytesIO):
            payload_bytes = raw_body.read(length)
        elif hasattr(raw_body, "read"):
            payload_bytes = raw_body.read(length)
        try:
            payload = json.loads(payload_bytes.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            status, headers, body = _encode_json({"error": "Invalid JSON"}, "400 Bad Request")
        else:
            persona = payload.get("persona", "")
            top_n = payload.get("top_n")
            system_prompt = payload.get("system_prompt")
            try:
                data = service.recommend(persona, top_n=top_n, system_prompt=system_prompt)
            except ValueError as exc:
                status, headers, body = _encode_json({"error": str(exc)}, "422 Unprocessable Entity")
            else:
                status, headers, body = _encode_json(data)
    else:
        status, headers, body = _encode_json({"error": "Not found"}, "404 Not Found")

    start_response(status, headers)
    return body


def serve(host: str = "127.0.0.1", port: int = 8000) -> None:  # pragma: no cover - manual execution helper
    with make_server(host, port, application) as httpd:
        print(f"Serving on http://{host}:{port}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server")


__all__ = [
    "SelectorResources",
    "SelectorService",
    "application",
    "get_resources",
    "serve",
]


if __name__ == "__main__":  # pragma: no cover
    serve()
