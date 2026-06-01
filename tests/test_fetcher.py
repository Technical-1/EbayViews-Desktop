import requests
import pytest

from ebayviews.fetcher import SellerFetchError, SellerItemFetcher, extract_item_id

HTML_PAGE_1 = """
<html><body>
  <li class="s-item">
    <a href="https://www.ebay.com/itm/Example-title/123456789012?hash=x"><span class="s-item__title">Vintage Camera</span></a>
    <span class="s-item__price">$42.00</span>
  </li>
  <li class="s-item">
    <a href="/itm/Another-title/234567890123"><span class="s-item__title">Film Lens</span></a>
    <span class="s-item__price">$19.99 to $29.99</span>
  </li>
  <a rel="next" href="/sch/i.html?_pgn=2">Next</a>
</body></html>
"""

HTML_PAGE_2 = """
<html><body>
  <article>
    <h3>Tripod</h3>
    <a href="/itm/345678901234">View item</a>
    <span data-testid="x-price">$12.50</span>
  </article>
</body></html>
"""


class Response:
    def __init__(self, text="", status_error=None):
        self.text = text
        self.status_error = status_error

    def raise_for_status(self):
        if self.status_error:
            raise self.status_error


class SequencedSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def get(self, url, **kwargs):
        self.calls.append((url, kwargs))
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


def test_extract_item_id_patterns():
    assert extract_item_id("https://www.ebay.com/itm/name/123456789012?x=1") == "123456789012"
    assert extract_item_id("https://www.ebay.com/itm/123456789012") == "123456789012"
    assert extract_item_id("https://www.ebay.com/p/123456789012") == "123456789012"
    assert extract_item_id("https://example.com/not-an-item") is None


def test_parse_items_extracts_title_price_and_absolute_url():
    items = SellerItemFetcher.parse_items(HTML_PAGE_1, "https://www.ebay.com/sch/test")
    assert [item.item_id for item in items] == ["123456789012", "234567890123"]
    assert items[0].title == "Vintage Camera"
    assert items[0].price == "$42.00"
    assert items[1].url == "https://www.ebay.com/itm/Another-title/234567890123"


def test_parse_items_uses_container_title_when_link_text_is_generic():
    items = SellerItemFetcher.parse_items(HTML_PAGE_2, "https://www.ebay.com/sch/test")
    assert items[0].item_id == "345678901234"
    assert items[0].title == "Tripod"
    assert items[0].price == "$12.50"


def test_parse_items_deduplicates_by_item_id_with_last_seen_data():
    html = """
    <li><a href="/itm/123456789012">First</a><span class="s-item__price">$1</span></li>
    <li><a href="/itm/123456789012">Second</a><span class="s-item__price">$2</span></li>
    """
    items = SellerItemFetcher.parse_items(html)
    assert len(items) == 1
    assert items[0].title == "Second"
    assert items[0].price == "$2"


def test_parse_next_page_resolves_relative_url():
    assert SellerItemFetcher.parse_next_page(HTML_PAGE_1, "https://www.ebay.com/sch/test") == "https://www.ebay.com/sch/i.html?_pgn=2"
    assert SellerItemFetcher.parse_next_page("<html></html>", "https://www.ebay.com") is None


def test_fetch_follows_pagination_and_respects_page_limit():
    session = SequencedSession([Response(HTML_PAGE_1), Response(HTML_PAGE_2)])
    fetcher = SellerItemFetcher(session=session, max_pages=2)
    items = fetcher.fetch("https://ebay.us/m/5YVabM")
    assert [item.item_id for item in items] == ["123456789012", "234567890123", "345678901234"]
    assert len(session.calls) == 2
    assert session.calls[0][0] == "https://ebay.us/m/5YVabM"


def test_fetch_raises_when_no_items():
    fetcher = SellerItemFetcher(session=SequencedSession([Response("<html></html>")]))
    with pytest.raises(SellerFetchError, match="No item listings"):
        fetcher.fetch("https://example.com")


def test_fetch_wraps_request_errors():
    fetcher = SellerItemFetcher(session=SequencedSession([requests.Timeout("too slow")]))
    with pytest.raises(SellerFetchError, match="Could not fetch seller page"):
        fetcher.fetch("https://example.com")


def test_fetch_wraps_http_errors():
    fetcher = SellerItemFetcher(session=SequencedSession([Response(status_error=requests.HTTPError("403"))]))
    with pytest.raises(SellerFetchError, match="403"):
        fetcher.fetch("https://example.com")


def test_fetch_requires_url():
    with pytest.raises(SellerFetchError, match="Enter a seller URL"):
        SellerItemFetcher().fetch("   ")
