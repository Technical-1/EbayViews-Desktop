import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication

_QAPP = None

from ebayviews.app import MainWindow, SettingsDialog
from ebayviews.config import AppConfig
from ebayviews.models import SellerItem


def app():
    global _QAPP
    _QAPP = QApplication.instance() or _QAPP or QApplication([])
    return _QAPP


def test_settings_dialog_returns_validated_config():
    app()
    dialog = SettingsDialog(AppConfig(concurrency=5))
    dialog.concurrency.setValue(25)
    dialog.interval.setValue(0.5)
    config = dialog.config()
    assert config.concurrency == 25
    assert config.interval_seconds == 0.5


def test_main_window_populates_and_selects_items():
    app()
    window = MainWindow()
    window.on_items_fetched([SellerItem("123456789012", "Camera", "$42", "https://www.ebay.com/itm/123456789012")])
    assert window.table.rowCount() == 1
    assert window.selected_items()[0].item_id == "123456789012"
