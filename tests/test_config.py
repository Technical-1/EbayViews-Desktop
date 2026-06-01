from pathlib import Path

from ebayviews.config import AppConfig, load_config, load_proxies, save_config


def test_config_validation_clamps_values():
    config = AppConfig(concurrency=99, interval_seconds=-1, timeout_seconds=0, retries=-5, max_seller_pages=0).validate()
    assert config.concurrency == 25
    assert config.interval_seconds == 0
    assert config.timeout_seconds == 1
    assert config.retries == 0
    assert config.max_seller_pages == 1


def test_config_round_trip(tmp_path: Path):
    path = tmp_path / "config.json"
    save_config(AppConfig(concurrency=3, proxy_file="proxies.txt"), path)
    loaded = load_config(path)
    assert loaded.concurrency == 3
    assert loaded.proxy_file == "proxies.txt"


def test_load_proxies_skips_blanks_and_comments(tmp_path: Path):
    proxy_file = tmp_path / "proxies.txt"
    proxy_file.write_text("\n# comment\nhttp://one\nhttp://two\n")
    assert load_proxies(str(proxy_file)) == ["http://one", "http://two"]
