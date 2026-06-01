# Project Q&A

## Overview

EbayViews Desktop is a local PyQt6 app for controlled, learning-oriented eBay item request experiments. It expands the original one-file CLI into a desktop workflow with seller item retrieval, selectable listings, settings, progress, logging, and safer concurrency limits.

## Problem Solved

The original script could send repeated requests to one item, but it had no UI, no selection workflow, no settings, and minimal error handling. The desktop version turns that experiment into a more inspectable tool with visible state and bounded execution.

## Target Users

- **Python desktop learners** — can study a compact PyQt6 app with background network work.
- **Engineers reviewing automation trade-offs** — can inspect bounded concurrency, retry handling, and HTML parsing limitations.

## Technical Highlights

### Seller listing parsing

`SellerItemFetcher` uses BeautifulSoup to discover item links, titles, prices, and pagination from seller listing HTML. The parser deduplicates by item ID and raises user-friendly failures when no listings are found.

### Bounded request generation

`ViewGenerator` uses `ThreadPoolExecutor` instead of unbounded raw threads. Settings clamp concurrency, timeouts, retries, intervals, and page limits to avoid runaway behavior.

### UI-safe progress reporting

The PyQt UI runs fetching and generation in background threads, then emits Qt signals for logs, errors, and progress updates. This keeps the interface responsive during network work.

## Frequently Asked Questions

### Does it use the official eBay API?

No. It uses best-effort HTML parsing because no API credentials are required. That means selectors may need updates if eBay changes page markup.

### Does it show live eBay view counts?

No. The app tracks generated request progress only, because live listing view counts are not reliably exposed in page HTML.

### Can I still use the CLI?

Yes. `python EbayViewBot.py --item-id 123456789012 --views 3` keeps the old single-item workflow available.

### How are proxies configured?

The settings dialog accepts a path to a newline-delimited proxy file. Each non-empty, non-comment line is used as a proxy candidate during generation.

### What are the safety defaults?

The app defaults to concurrency `5`, interval `0.25s`, timeout `10s`, retries `2`, and max seller pages `5`, with a visible responsible-use warning.
