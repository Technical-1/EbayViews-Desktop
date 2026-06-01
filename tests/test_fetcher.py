import pytest

from ebayviews.fetcher import SellerFetchError, SellerItemFetcher, extract_item_id

HTML = '\n<html><body>\n  <li class="s-item">\n    <a href="https://www.ebay.com/itm/Example-title/123456789012?hash=x"><span class="s-item__title">Vintage Camera</span></a>\n    <span class="s-item__price">$42.00</span>\n  </li>\n  <a rel="next" href="/sch/i.html?_pgn=2">Next</a>\n</body></html>\n'


def test_extract_item_id():
    assert extract_item_id("https://www.ebay.com/itm/name/123456789012?x=1") == "123456789012"


def test_parse_items_extracts_title_price_and_url():
    items = SellerItemFetcher.parse_items(HTML, "https://www.ebay.com/sch/test")
    assert len(items) == 1
    assert items[0].item_id == "123456789012"
    assert items[0].title == "Vintage Camera"
    assert items[0].price == "$42.00"


def test_parse_next_page():
    assert SellerItemFetcher.parse_next_page(HTML, "https://www.ebay.com/sch/test") == "https://www.ebay.com/sch/i.html?_pgn=2"


def test_fetch_raises_when_no_items(monkeypatch):
    class Session:
        def get(self, *args, **kwargs):
            class Response:
                text = "<html></html>"
                def raise_for_status(self): pass
            return Response()
    fetcher = SellerItemFetcher(session=Session())
    with pytest.raises(SellerFetchError):
        fetcher.fetch("https://example.com")
