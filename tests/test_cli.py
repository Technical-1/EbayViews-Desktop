from types import SimpleNamespace

from ebayviews import cli
from ebayviews.config import AppConfig
from ebayviews.models import SellerItem


class FakeGenerator:
    calls = []
    def __init__(self, config):
        self.config = config
    def generate(self, items, views, log_callback=None):
        self.__class__.calls.append((items, views, log_callback))


def test_cli_item_id_and_views_use_generator(monkeypatch):
    FakeGenerator.calls = []
    monkeypatch.setattr(cli, "load_config", lambda: AppConfig())
    monkeypatch.setattr(cli, "ViewGenerator", FakeGenerator)
    monkeypatch.setattr("sys.argv", ["ebayviews", "--item-id", "123456789012", "--views", "2"])
    cli.main()
    items, views, _ = FakeGenerator.calls[0]
    assert views == 2
    assert items == [SellerItem("123456789012", "eBay item 123456789012", url="https://www.ebay.com/itm/123456789012")]


def test_cli_desktop_flag_launches_app(monkeypatch):
    launched = []
    monkeypatch.setattr("sys.argv", ["ebayviews", "--desktop"])
    monkeypatch.setitem(__import__("sys").modules, "ebayviews.app", SimpleNamespace(run_app=lambda: launched.append(True)))
    cli.main()
    assert launched == [True]
