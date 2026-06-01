# Tech Stack

## Core Technologies

| Category | Technology | Version | Why this choice |
|----------|------------|---------|-----------------|
| Language | Python | 3.10+ | Simple packaging for a local desktop/networking tool. |
| Desktop UI | PyQt6 | `>=6.6` | Mature native desktop widgets and thread-safe signals. |
| HTTP | requests | `>=2.31` | Straightforward synchronous request API for worker threads. |
| Parsing | BeautifulSoup | `>=4.12` | Resilient enough for best-effort marketplace HTML parsing. |
| User agents | user_agent | `>=0.1.10` | Generates browser-like user-agent strings per request. |
| Tests | pytest | `>=8.0` | Lightweight unit and smoke testing. |

## Runtime Configuration

- Settings path: `~/.ebayviews/config.json`
- Defaults: concurrency `5`, max concurrency `25`, interval `0.25s`, timeout `10s`, retries `2`, max seller pages `5`
- Optional proxy input: newline-delimited text file
