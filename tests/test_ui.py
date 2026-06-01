from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QMessageBox

from ebayviews import app as app_module
from ebayviews.app import MainWindow, SettingsDialog
from ebayviews.config import AppConfig
from ebayviews.models import ProgressEvent, RequestResult, RequestStatus, SellerItem


class SyncThread:
    def __init__(self, target, daemon=False):
        self.target = target
        self.daemon = daemon

    def start(self):
        self.target()


class FakeFetcher:
    def __init__(self, timeout_seconds, max_pages):
        self.timeout_seconds = timeout_seconds
        self.max_pages = max_pages

    def fetch(self, url):
        assert url == "https://ebay.us/m/5YVabM"
        return [SellerItem("123456789012", "Camera", "$42", "https://www.ebay.com/itm/123456789012")]


class FakeGenerator:
    instances = []

    def __init__(self, config):
        self.config = config
        self.calls = []
        self.__class__.instances.append(self)

    def generate(self, items, views_per_item, progress_callback=None, log_callback=None):
        self.calls.append((items, views_per_item))
        if log_callback:
            log_callback("fake generation started")
        if progress_callback:
            progress_callback(ProgressEvent(items[0].item_id, 1, views_per_item, RequestResult(items[0].item_id, 1, RequestStatus.SUCCESS, 200)))
        return []


def make_window(monkeypatch):
    monkeypatch.setattr(app_module, "load_config", lambda: AppConfig(concurrency=2, interval_seconds=0, retries=0))
    monkeypatch.setattr(QMessageBox, "warning", lambda *args, **kwargs: None)
    return MainWindow()


def test_settings_dialog_returns_validated_config(qapp):
    dialog = SettingsDialog(AppConfig(concurrency=5, proxy_file="old.txt"))
    dialog.concurrency.setValue(25)
    dialog.interval.setValue(0.5)
    dialog.proxy_file.setText("new.txt")
    config = dialog.config()
    assert config.concurrency == 25
    assert config.interval_seconds == 0.5
    assert config.proxy_file == "new.txt"


def test_settings_dialog_browse_updates_proxy_file(qapp, monkeypatch):
    monkeypatch.setattr(app_module.QFileDialog, "getOpenFileName", lambda *args, **kwargs: ("/tmp/proxies.txt", ""))
    dialog = SettingsDialog(AppConfig())
    dialog.choose_proxy_file()
    assert dialog.proxy_file.text() == "/tmp/proxies.txt"


def test_main_window_populates_selects_and_unselects_items(qapp, monkeypatch):
    window = make_window(monkeypatch)
    window.on_items_fetched([SellerItem("123456789012", "Camera", "$42", "https://www.ebay.com/itm/123456789012")])
    assert window.table.rowCount() == 1
    assert window.selected_items()[0].item_id == "123456789012"
    window.table.item(0, 0).setCheckState(Qt.CheckState.Unchecked)
    assert window.selected_items() == []


def test_main_window_fetch_items_success_runs_in_background_path(qapp, monkeypatch):
    monkeypatch.setattr(app_module, "Thread", SyncThread)
    monkeypatch.setattr(app_module, "SellerItemFetcher", FakeFetcher)
    window = make_window(monkeypatch)
    window.seller_url.setText("https://ebay.us/m/5YVabM")
    window.fetch_items()
    assert window.table.rowCount() == 1
    assert "Loaded 1 item" in window.log.toPlainText()


def test_main_window_fetch_items_error_logs_message(qapp, monkeypatch):
    class FailingFetcher(FakeFetcher):
        def fetch(self, url):
            raise app_module.SellerFetchError("nope")

    monkeypatch.setattr(app_module, "Thread", SyncThread)
    monkeypatch.setattr(app_module, "SellerItemFetcher", FailingFetcher)
    window = make_window(monkeypatch)
    window.seller_url.setText("https://ebay.us/m/5YVabM")
    window.fetch_items()
    assert "Error: nope" in window.log.toPlainText()


def test_main_window_generate_views_success_updates_progress_and_logs(qapp, monkeypatch):
    FakeGenerator.instances = []
    monkeypatch.setattr(app_module, "Thread", SyncThread)
    monkeypatch.setattr(app_module, "ViewGenerator", FakeGenerator)
    window = make_window(monkeypatch)
    window.on_items_fetched([SellerItem("123456789012", "Camera", "$42", "https://www.ebay.com/itm/123456789012")])
    window.views_per_item.setValue(3)
    window.generate_views()
    assert FakeGenerator.instances[0].calls[0][1] == 3
    assert window.progress.value() == 33
    assert "fake generation started" in window.log.toPlainText()


def test_main_window_generate_views_error_logs_message(qapp, monkeypatch):
    class FailingGenerator:
        def __init__(self, config):
            pass
        def generate(self, *args, **kwargs):
            raise ValueError("bad generation")

    monkeypatch.setattr(app_module, "Thread", SyncThread)
    monkeypatch.setattr(app_module, "ViewGenerator", FailingGenerator)
    window = make_window(monkeypatch)
    window.on_items_fetched([SellerItem("123456789012", "Camera")])
    window.generate_views()
    assert "Error: bad generation" in window.log.toPlainText()


def test_append_log_and_progress_are_user_visible(qapp, monkeypatch):
    window = make_window(monkeypatch)
    window._total = 4
    window._completed = 0
    window.append_log("hello")
    window.on_progress(ProgressEvent("123", 1, 4, RequestResult("123", 1, RequestStatus.SUCCESS, 200)))
    assert "hello" in window.log.toPlainText()
    assert window.progress.value() == 25
