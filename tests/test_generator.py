from ebayviews.config import AppConfig
from ebayviews.generator import ViewGenerator
from ebayviews.models import RequestStatus, SellerItem


class Response:
    status_code = 200


class Session:
    calls = []
    def get(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return Response()


def test_generator_reports_progress_and_success():
    session = Session()
    events = []
    logs = []
    generator = ViewGenerator(AppConfig(concurrency=1, interval_seconds=0, retries=0), session_factory=lambda: session)
    results = generator.generate([SellerItem("123456789012", "Item")], 2, progress_callback=events.append, log_callback=logs.append)
    assert [result.status for result in results] == [RequestStatus.SUCCESS, RequestStatus.SUCCESS]
    assert len(events) == 2
    assert events[-1].completed == 2
    assert session.calls[0][0] == "https://www.ebay.com/itm/123456789012"


def test_generator_raises_without_selection():
    generator = ViewGenerator(AppConfig())
    try:
        generator.generate([], 1)
    except ValueError as exc:
        assert "Select at least one" in str(exc)
    else:
        raise AssertionError("expected ValueError")
