# EbayViews Desktop

A PyQt6 desktop app for controlled eBay listing request experiments with seller-page discovery, selectable items, bounded concurrency, optional proxies, and real-time status logging.

I built this as the desktop evolution of a small Python networking script. The interesting engineering work is in turning an unbounded single-item request loop into a testable desktop application: settings are validated and persisted, seller listings are parsed into structured records, request generation is capped through a worker pool, and the UI stays responsive through Qt signals.

Use this responsibly. Automated marketplace traffic can violate terms of service, distort analytics, or trigger rate limits; the app is intended as a local learning and inspection tool.

## Features

- **Seller-page item discovery** — paste a public eBay seller URL and fetch item IDs, titles, prices, and item links through best-effort HTML parsing.
- **Selectable item table** — choose which retrieved listings should receive request-generation runs.
- **Bounded request generation** — configure concurrency, delay between submissions, timeouts, retry counts, and user-agent rotation.
- **Optional proxy rotation** — load a newline-delimited proxy file and rotate proxies across generated requests.
- **Real-time progress and logs** — track generated request progress and see status/error messages in a console-style UI panel.
- **Persistent settings** — save validated preferences to `~/.ebayviews/config.json`.
- **CLI compatibility** — run single-item request experiments without opening the desktop UI.
- **Automated coverage** — unit, CLI, parser, generator, UI smoke, and optional live seller-page tests cover the core behavior.

## Tech Stack

- **Language**: Python 3.10+
- **Desktop UI**: PyQt6 `>=6.6`
- **HTTP client**: requests `>=2.31`
- **HTML parsing**: BeautifulSoup `>=4.12`
- **User-agent generation**: user_agent `>=0.1.10`
- **Testing**: pytest `>=8.0`

## Getting Started

### Prerequisites

- Python 3.10 or newer
- `pip`
- macOS, Windows, or Linux with PyQt6-compatible desktop support

### Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Usage

```bash
# Launch the desktop app
python -m ebayviews --desktop

# Run the compatibility CLI for one item
python EbayViewBot.py --item-id 123456789012 --views 3
```

The desktop workflow is:

1. Paste a public seller page URL.
2. Fetch listings into the item table.
3. Select the items to include.
4. Adjust settings if needed.
5. Run a small, throttled generation job and watch the log/progress area.

## Development

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run deterministic tests
pytest

# Optional live seller-page parser check
EBAYVIEWS_LIVE_TESTS=1 pytest tests/test_live_ebay.py -q
```

The live test uses a public seller URL and is skipped unless `EBAYVIEWS_LIVE_TESTS=1` is set, so the default suite remains deterministic and does not depend on eBay availability.

## Project Structure

```text
EbayViews-Desktop/
├── EbayViewBot.py       # Compatibility launcher for CLI usage
├── ebayviews/
│   ├── app.py           # PyQt6 desktop window, settings dialog, progress/log UI
│   ├── cli.py           # Argument parsing and single-item CLI execution
│   ├── config.py        # JSON settings load/save and validation
│   ├── fetcher.py       # Seller listing retrieval and HTML parsing
│   ├── generator.py     # ThreadPoolExecutor request generation
│   └── models.py        # Shared dataclasses and request status types
├── tests/               # Unit, CLI, UI smoke, and optional live tests
└── .portfolio/          # Portfolio documentation and preview assets
```

## Limitations

- Seller parsing is best-effort HTML parsing, not an official eBay API integration.
- Live eBay view counts are not shown because they are not reliably exposed in listing HTML.
- Proxy health and marketplace policy compliance are the user's responsibility.
- The app deliberately favors visible controls and conservative defaults over maximum request throughput.

## License

Unlicensed (personal project)

## Author

Jacob Kanfer — [GitHub](https://github.com/Technical-1)
