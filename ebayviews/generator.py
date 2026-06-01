from __future__ import annotations

import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from itertools import cycle
from threading import Lock
from typing import Callable, Iterable

import requests
from user_agent import generate_user_agent

from .config import AppConfig, load_proxies
from .models import ProgressEvent, RequestResult, RequestStatus, SellerItem

LOGGER = logging.getLogger(__name__)
LogCallback = Callable[[str], None]
ProgressCallback = Callable[[ProgressEvent], None]


@dataclass
class ViewGenerator:
    config: AppConfig
    session_factory: Callable[[], requests.Session] = requests.Session

    def generate(
        self,
        items: Iterable[SellerItem],
        views_per_item: int,
        progress_callback: ProgressCallback | None = None,
        log_callback: LogCallback | None = None,
    ) -> list[RequestResult]:
        selected = list(items)
        if not selected:
            raise ValueError("Select at least one item before generating views.")
        views_per_item = int(views_per_item)
        if views_per_item < 1:
            raise ValueError("Views per item must be at least 1.")

        config = self.config.validate()
        proxies = load_proxies(config.proxy_file)
        proxy_cycle = cycle(proxies) if proxies else None
        proxy_lock = Lock()
        progress: dict[str, int] = {item.item_id: 0 for item in selected}
        total_by_item = views_per_item
        results: list[RequestResult] = []

        def next_proxy() -> str | None:
            if proxy_cycle is None:
                return None
            with proxy_lock:
                return next(proxy_cycle)

        jobs = [(item, number) for item in selected for number in range(1, views_per_item + 1)]
        self._log(log_callback, f"Starting {len(jobs)} requests across {len(selected)} item(s).")
        with ThreadPoolExecutor(max_workers=config.concurrency) as executor:
            futures = []
            for item, number in jobs:
                futures.append(executor.submit(self._request_item, item, number, next_proxy()))
                if config.interval_seconds:
                    time.sleep(config.interval_seconds)
            for future in as_completed(futures):
                result = future.result()
                results.append(result)
                progress[result.item_id] += 1
                if progress_callback:
                    progress_callback(ProgressEvent(result.item_id, progress[result.item_id], total_by_item, result))
                if result.status is RequestStatus.SUCCESS:
                    self._log(log_callback, f"{result.item_id}: request {result.request_number} succeeded ({result.status_code}).")
                else:
                    self._log(log_callback, f"{result.item_id}: request {result.request_number} failed: {result.error}")
        self._log(log_callback, "View generation finished.")
        return results

    def _request_item(self, item: SellerItem, request_number: int, proxy: str | None) -> RequestResult:
        url = item.url or f"https://www.ebay.com/itm/{item.item_id}"
        headers = {"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"}
        if self.config.rotate_user_agents:
            headers["User-Agent"] = generate_user_agent()
        else:
            headers["User-Agent"] = "Mozilla/5.0 EbayViewsDesktop/0.1"
        proxies = {"http": proxy, "https": proxy} if proxy else None
        last_error: str | None = None
        for attempt in range(self.config.retries + 1):
            session = self.session_factory()
            try:
                response = session.get(url, headers=headers, timeout=self.config.timeout_seconds, proxies=proxies)
                if 200 <= response.status_code < 400:
                    return RequestResult(item.item_id, request_number, RequestStatus.SUCCESS, response.status_code)
                last_error = f"HTTP {response.status_code}"
            except requests.RequestException as exc:
                LOGGER.exception("Request failed for item %s", item.item_id)
                last_error = str(exc)
            if attempt < self.config.retries:
                time.sleep(min(0.25 * (attempt + 1), 2.0))
        return RequestResult(item.item_id, request_number, RequestStatus.FAILED, error=last_error or "Unknown error")

    @staticmethod
    def _log(callback: LogCallback | None, message: str) -> None:
        LOGGER.info(message)
        if callback:
            callback(message)
