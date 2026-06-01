import os

import pytest

from ebayviews.fetcher import SellerItemFetcher

EBAY_ACCOUNT_URL = "https://ebay.us/m/5YVabM"


@pytest.mark.live
def test_live_ebay_account_url_fetches_items_when_enabled():
    if os.environ.get("EBAYVIEWS_LIVE_TESTS") != "1":
        pytest.skip("Set EBAYVIEWS_LIVE_TESTS=1 to run live eBay seller-page test")
    items = SellerItemFetcher(max_pages=1, timeout_seconds=20).fetch(EBAY_ACCOUNT_URL)
    assert items
    assert all(item.item_id for item in items)
    assert all(item.url for item in items)
