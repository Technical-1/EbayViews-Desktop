import json
from pathlib import Path

from ebayviews.config import AppConfig, load_config, load_proxies, save_config


def test_config_validation_clamps_values():
    config = AppConfig(concurrency=99, interval_seconds=-1, timeout_seconds=0, retries=-5, max_seller_pages=0).validate()
    assert config.concurrency == 25
    assert config.interval_seconds == 0
    assert config.timeout_seconds == 1
    assert config.retries == 0
    assert config.max_seller_pages == 1


def test_config_validation_normalizes_types():
    config = AppConfig.from_dict({
        "concurrency": "7",
        "interval_seconds": "0.5",
        "timeout_seconds": "12.5",
        "retries": "3",
        "max_seller_pages": "4",
        "rotate_user_agents": 0,
        "proxy_file": None,
        "unknown": "ignored",
    })
    assert config.concurrency == 7
    assert config.interval_seconds == 0.5
    assert config.timeout_seconds == 12.5
    assert config.retries == 3
    assert config.max_seller_pages == 4
    assert config.rotate_user_agents is False
    assert config.proxy_file == ""


def test_config_round_trip(tmp_path: Path):
    path = tmp_path / "config.json"
    save_config(AppConfig(concurrency=3, proxy_file="proxies.txt"), path)
    loaded = load_config(path)
    assert loaded.concurrency == 3
    assert loaded.proxy_file == "proxies.txt"
    assert json.loads(path.read_text())["concurrency"] == 3


def test_load_config_returns_defaults_for_missing_or_invalid_file(tmp_path: Path):
    assert load_config(tmp_path / "missing.json") == AppConfig()
    invalid = tmp_path / "config.json"
    invalid.write_text("not json")
    assert load_config(invalid) == AppConfig()


def test_load_proxies_skips_blanks_and_comments(tmp_path: Path):
    proxy_file = tmp_path / "proxies.txt"
    proxy_file.write_text("\n# comment\nhttp://one\nhttp://two\n")
    assert load_proxies(str(proxy_file)) == ["http://one", "http://two"]


def test_load_proxies_returns_empty_for_missing_file(tmp_path: Path):
    assert load_proxies(str(tmp_path / "missing.txt")) == []
