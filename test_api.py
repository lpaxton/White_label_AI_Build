import io
import json
from typing import List, Tuple

from wsgiref.util import setup_testing_defaults

import web_service
from xml_parser import ContentItem


class DummyProvider:
    def __init__(self, response: str):
        self.response = response
        self.model = "dummy-model"
        self.prompts: List[str] = []

    def generate(self, prompt: str, **_: str) -> str:
        self.prompts.append(prompt)
        return self.response


def _build_resources() -> web_service.SelectorResources:
    items = (
        ContentItem(title="Budget Foundations Workshop", description="Learn budgeting"),
        ContentItem(title="Cash Flow", description="Cash flow fundamentals"),
    )
    response = json.dumps(
        {
            "recommendations": [
                {"title": "Budget Foundations Workshop", "reason": "Covers budgeting", "score": 0.9},
                {"title": "Cash Flow", "reason": "Focuses on liquidity", "score": 0.8},
            ]
        }
    )
    provider = DummyProvider(response)
    return web_service.SelectorResources(
        provider=provider,
        top_n=2,
        system_prompt="System",
        content_items=items,
    )


def _call_app(method: str, path: str, body: str | None = None) -> Tuple[str, bytes]:
    environ = {}
    setup_testing_defaults(environ)
    environ["REQUEST_METHOD"] = method
    environ["PATH_INFO"] = path
    payload = (body or "").encode("utf-8")
    environ["CONTENT_LENGTH"] = str(len(payload))
    environ["wsgi.input"] = io.BytesIO(payload)

    captured: dict[str, object] = {}

    def start_response(status: str, headers):
        captured["status"] = status
        captured["headers"] = dict(headers)

    body_chunks = web_service.application(environ, start_response)
    response_body = b"".join(body_chunks)
    return captured["status"], response_body


def test_service_recommendations(monkeypatch):
    resources = _build_resources()
    monkeypatch.setattr(web_service, "get_resources", lambda: resources)
    service = web_service.SelectorService(resources)
    result = service.recommend("Operations manager overseeing budgets")
    assert result["persona"] == "Operations manager overseeing budgets"
    assert len(result["recommendations"]) == 2
    assert result["recommendations"][0]["title"] == "Budget Foundations Workshop"


def test_wsgi_recommendations(monkeypatch):
    resources = _build_resources()
    monkeypatch.setattr(web_service, "get_resources", lambda: resources)
    status, body = _call_app(
        "POST",
        "/api/recommendations",
        body=json.dumps({"persona": "Finance lead guiding teams", "top_n": 2}),
    )
    assert status == "200 OK"
    data = json.loads(body.decode("utf-8"))
    assert data["persona"] == "Finance lead guiding teams"
    assert data["recommendations"][0]["title"] == "Budget Foundations Workshop"


def test_wsgi_content_listing(monkeypatch):
    resources = _build_resources()
    monkeypatch.setattr(web_service, "get_resources", lambda: resources)
    status, body = _call_app("GET", "/api/content")
    assert status == "200 OK"
    items = json.loads(body.decode("utf-8"))
    assert len(items) == 2
    assert items[0]["title"] == "Budget Foundations Workshop"


def test_render_index(monkeypatch):
    resources = _build_resources()
    monkeypatch.setattr(web_service, "get_resources", lambda: resources)
    service = web_service.SelectorService(resources)
    html = service.render_index()
    assert "Financial Literacy Persona Selector" in html
    assert "Budget Foundations Workshop" in html
