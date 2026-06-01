from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from html import unescape
from typing import Iterable
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from .models import SellerItem

LOGGER = logging.getLogger(__name__)
ITEM_ID_RE = re.compile(r"/(?:itm|p)/(?:[^/?#]+/)?(\d{9,})|itm/(\d{9,})")


class SellerFetchError(RuntimeError):
    """Raised when seller listings cannot be retrieved."""


@dataclass
class SellerItemFetcher:
    timeout_seconds: float = 10.0
    max_pages: int = 5
    session: requests.Session | None = None

    def __post_init__(self) -> None:
        if self.session is None:
            self.session = requests.Session()

    def fetch(self, seller_url: str) -> list[SellerItem]:
        seller_url = seller_url.strip()
        if not seller_url:
            raise SellerFetchError("Enter a seller URL before fetching items.")
        found: dict[str, SellerItem] = {}
        next_url: str | None = seller_url
        pages_read = 0
        while next_url and pages_read < self.max_pages:
            pages_read += 1
            html = self._get(next_url)
            for item in self.parse_items(html, next_url):
                found[item.item_id] = item
            next_url = self.parse_next_page(html, next_url)
        if not found:
            raise SellerFetchError("No item listings were found on that seller page.")
        return list(found.values())

    def _get(self, url: str) -> str:
        assert self.session is not None
        headers = {"User-Agent": "Mozilla/5.0 EbayViewsDesktop/0.1", "Accept": "text/html,application/xhtml+xml"}
        try:
            response = self.session.get(url, headers=headers, timeout=self.timeout_seconds)
            response.raise_for_status()
            return response.text
        except requests.RequestException as exc:
            LOGGER.exception("Failed to fetch seller page %s", url)
            raise SellerFetchError(f"Could not fetch seller page: {exc}") from exc

    @staticmethod
    def parse_items(html: str, base_url: str = "https://www.ebay.com") -> list[SellerItem]:
        soup = BeautifulSoup(html, "html.parser")
        items: dict[str, SellerItem] = {}
        for link in soup.find_all("a", href=True):
            href = str(link.get("href", ""))
            item_id = extract_item_id(href)
            if not item_id:
                continue
            url = urljoin(base_url, href.split("?")[0])
            title = normalize_text(link.get_text(" "))
            container = link.find_parent(["li", "div", "article"]) or link.parent
            if not title and container is not None:
                title = extract_title(container)
            price = extract_price(container) if container is not None else ""
            if not title or title.lower() in {"shop now", "view item", "details"}:
                title = f"eBay item {item_id}"
            items[item_id] = SellerItem(item_id=item_id, title=title, price=price, url=url)
        return list(items.values())

    @staticmethod
    def parse_next_page(html: str, base_url: str) -> str | None:
        soup = BeautifulSoup(html, "html.parser")
        candidates: Iterable = soup.select('a[rel="next"], a.pagination__next, a[type="next"]')
        for link in candidates:
            href = link.get("href")
            if href:
                return urljoin(base_url, str(href))
        return None


def extract_item_id(url: str) -> str | None:
    match = ITEM_ID_RE.search(url)
    if not match:
        return None
    return next(group for group in match.groups() if group)


def normalize_text(value: str) -> str:
    return " ".join(unescape(value or "").split())


def extract_title(container) -> str:
    selectors = [".s-item__title", "[class*=title]", "h3", "h2"]
    for selector in selectors:
        node = container.select_one(selector) if hasattr(container, "select_one") else None
        if node:
            text = normalize_text(node.get_text(" "))
            if text:
                return text
    return ""


def extract_price(container) -> str:
    selectors = [".s-item__price", "[class*=price]", "[aria-label*=price i]"]
    for selector in selectors:
        node = container.select_one(selector) if hasattr(container, "select_one") else None
        if node:
            text = normalize_text(node.get_text(" ") or node.get("aria-label", ""))
            if text:
                return text
    text = normalize_text(container.get_text(" "))
    match = re.search(r"[$£€]\s?\d[\d,.]*(?:\s?to\s?[$£€]?\d[\d,.]*)?", text)
    return match.group(0) if match else ""
