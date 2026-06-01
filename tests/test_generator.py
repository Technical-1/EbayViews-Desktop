import requests
import pytest

from ebayviews.config import AppConfig
from ebayviews.generator import ViewGenerator
from ebayviews.models import RequestStatus, SellerItem


class Response:
    def __init__(self, status_code=200):
        self.status_code = status_code


class RecordingSession:
    def __init__(self, outcomes):
        self.outcomes = outcomes
        self.calls = []

    def get(self, url, **kwargs):
        self.calls.append((url, kwargs))
        outcome = self.outcomes.pop(0) if self.outcomes else Response()
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


def test_generator_reports_progress_and_success():
    session = RecordingSession([Response(), Response()])
    events = []
    logs = []
    generator = ViewGenerator(AppConfig(concurrency=1, interval_seconds=0, retries=0), session_factory=lambda: session)
    results = generator.generate([SellerItem("123456789012", "Item")], 2, progress_callback=events.append, log_callback=logs.append)
    assert [result.status for result in results] == [RequestStatus.SUCCESS, RequestStatus.SUCCESS]
    assert len(events) == 2
    assert events[-1].completed == 2
    assert session.calls[0][0] == "https://www.ebay.com/itm/123456789012"
    assert logs[0] == "Starting 2 requests across 1 item(s)."
    assert logs[-1] == "View generation finished."


def test_generator_uses_item_url_when_present():
    session = RecordingSession([Response()])
    item = SellerItem("123456789012", "Item", url="https://example.com/item")
    ViewGenerator(AppConfig(concurrency=1, interval_seconds=0, retries=0), session_factory=lambda: session).generate([item], 1)
    assert session.calls[0][0] == "https://example.com/item"


def test_generator_returns_failure_for_http_error_status():
    session = RecordingSession([Response(500)])
    result = ViewGenerator(AppConfig(concurrency=1, interval_seconds=0, retries=0), session_factory=lambda: session).generate([SellerItem("123", "Item")], 1)[0]
    assert result.status == RequestStatus.FAILED
    assert result.error == "HTTP 500"


def test_generator_retries_transient_request_errors(monkeypatch):
    monkeypatch.setattr("ebayviews.generator.time.sleep", lambda _: None)
    session = RecordingSession([requests.Timeout("slow"), Response(200)])
    result = ViewGenerator(AppConfig(concurrency=1, interval_seconds=0, retries=1), session_factory=lambda: session).generate([SellerItem("123", "Item")], 1)[0]
    assert result.status == RequestStatus.SUCCESS
    assert len(session.calls) == 2


def test_generator_uses_fixed_user_agent_when_rotation_disabled():
    session = RecordingSession([Response()])
    ViewGenerator(AppConfig(concurrency=1, interval_seconds=0, retries=0, rotate_user_agents=False), session_factory=lambda: session).generate([SellerItem("123", "Item")], 1)
    assert session.calls[0][1]["headers"]["User-Agent"] == "Mozilla/5.0 EbayViewsDesktop/0.1"


def test_generator_passes_rotated_proxies(tmp_path):
    proxy_file = tmp_path / "proxies.txt"
    proxy_file.write_text("http://one\nhttp://two\n")
    session = RecordingSession([Response(), Response(), Response()])
    config = AppConfig(concurrency=1, interval_seconds=0, retries=0, proxy_file=str(proxy_file))
    ViewGenerator(config, session_factory=lambda: session).generate([SellerItem("123", "Item")], 3)
    proxies = [call[1]["proxies"]["http"] for call in session.calls]
    assert proxies == ["http://one", "http://two", "http://one"]


def test_generator_multiple_items_progress_is_per_item():
    session = RecordingSession([Response(), Response(), Response(), Response()])
    events = []
    items = [SellerItem("111", "One"), SellerItem("222", "Two")]
    ViewGenerator(AppConfig(concurrency=1, interval_seconds=0, retries=0), session_factory=lambda: session).generate(items, 2, progress_callback=events.append)
    totals = {(event.item_id, event.completed, event.total) for event in events}
    assert ("111", 2, 2) in totals
    assert ("222", 2, 2) in totals


def test_generator_rejects_empty_selection_and_invalid_count():
    generator = ViewGenerator(AppConfig())
    with pytest.raises(ValueError, match="Select at least one"):
        generator.generate([], 1)
    with pytest.raises(ValueError, match="at least 1"):
        generator.generate([SellerItem("123", "Item")], 0)
