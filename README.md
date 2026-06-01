# EbayViews Desktop

A PyQt6 desktop app for learning-oriented eBay item request experiments with seller-item discovery, selectable listings, controlled concurrency, optional proxies, real-time logging, and persistent settings.

This project preserves the original CLI workflow while adding a desktop UI. Use it responsibly: automated marketplace traffic can violate terms of service, distort analytics, or trigger rate limits.

## Features

- **Desktop seller workflow** — paste a seller page, fetch listings, and select items in a table.
- **Controlled request generation** — configure concurrency, intervals, timeouts, retries, and user-agent rotation.
- **Optional proxy support** — load newline-delimited proxies from a local file.
- **Real-time feedback** — see progress and status/errors in a console-style log area.
- **CLI compatibility** — run single-item request experiments without opening the UI.

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

```bash
# Launch desktop app
python -m ebayviews --desktop

# Compatibility CLI
python EbayViewBot.py --item-id 123456789012 --views 3
```

Settings are stored at `~/.ebayviews/config.json`.

## Development

```bash
pip install -r requirements-dev.txt
pytest

# Optional live check against the public seller URL used for integration testing
EBAYVIEWS_LIVE_TESTS=1 pytest tests/test_live_ebay.py -q
```

## Project Structure

```text
ebayviews/
├── app.py        # PyQt6 desktop UI
├── cli.py        # CLI compatibility launcher
├── config.py     # JSON settings load/save and validation
├── fetcher.py    # Seller listing retrieval and parsing
├── generator.py  # ThreadPoolExecutor request generation
└── models.py     # Shared dataclasses
```

## Limitations

- Seller parsing is best-effort HTML parsing, not an official eBay API integration.
- Live eBay view counts are not shown because they are not reliably exposed in listing HTML.
- Proxy health and marketplace policy compliance are the user's responsibility.

## License

Unlicensed (personal project)
