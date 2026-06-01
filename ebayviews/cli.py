from __future__ import annotations

import argparse
import logging

from .config import AppConfig, load_config
from .generator import ViewGenerator
from .models import SellerItem


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="EbayViews Desktop compatibility CLI")
    parser.add_argument("--item-id", help="eBay item ID to request")
    parser.add_argument("--views", type=int, help="Number of requests to send")
    parser.add_argument("--desktop", action="store_true", help="Launch the PyQt desktop app")
    return parser


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    args = build_parser().parse_args()
    if args.desktop:
        from .app import run_app
        run_app()
        return
    item_id = args.item_id or input("What is your item ID? ").strip()
    views = args.views or int(input("How many views do you want? ").strip())
    config = load_config()
    generator = ViewGenerator(config)
    item = SellerItem(item_id=item_id, title=f"eBay item {item_id}", url=f"https://www.ebay.com/itm/{item_id}")
    generator.generate([item], views, log_callback=print)


if __name__ == "__main__":
    main()
