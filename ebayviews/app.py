from __future__ import annotations

import sys
from datetime import datetime
from threading import Thread

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QProgressBar,
    QSpinBox,
    QDoubleSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from .config import AppConfig, load_config, save_config
from .fetcher import SellerFetchError, SellerItemFetcher
from .generator import ViewGenerator
from .models import ProgressEvent, SellerItem


class SettingsDialog(QDialog):
    def __init__(self, config: AppConfig, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.concurrency = QSpinBox(); self.concurrency.setRange(1, 25); self.concurrency.setValue(config.concurrency)
        self.interval = QDoubleSpinBox(); self.interval.setRange(0, 60); self.interval.setDecimals(2); self.interval.setValue(config.interval_seconds)
        self.timeout = QDoubleSpinBox(); self.timeout.setRange(1, 120); self.timeout.setDecimals(1); self.timeout.setValue(config.timeout_seconds)
        self.retries = QSpinBox(); self.retries.setRange(0, 10); self.retries.setValue(config.retries)
        self.max_pages = QSpinBox(); self.max_pages.setRange(1, 25); self.max_pages.setValue(config.max_seller_pages)
        self.rotate = QCheckBox("Rotate user agents"); self.rotate.setChecked(config.rotate_user_agents)
        self.proxy_file = QLineEdit(config.proxy_file)
        browse = QPushButton("Browse…"); browse.clicked.connect(self.choose_proxy_file)
        proxy_row = QHBoxLayout(); proxy_row.addWidget(self.proxy_file); proxy_row.addWidget(browse)
        save = QPushButton("Save"); save.clicked.connect(self.accept)
        cancel = QPushButton("Cancel"); cancel.clicked.connect(self.reject)
        actions = QHBoxLayout(); actions.addStretch(); actions.addWidget(cancel); actions.addWidget(save)
        layout = QFormLayout(self)
        layout.addRow("Concurrency", self.concurrency)
        layout.addRow("Interval seconds", self.interval)
        layout.addRow("Timeout seconds", self.timeout)
        layout.addRow("Retries", self.retries)
        layout.addRow("Max seller pages", self.max_pages)
        layout.addRow("User agents", self.rotate)
        layout.addRow("Proxy file", proxy_row)
        layout.addRow(actions)

    def choose_proxy_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Choose proxy list")
        if path:
            self.proxy_file.setText(path)

    def config(self) -> AppConfig:
        return AppConfig(
            concurrency=self.concurrency.value(),
            interval_seconds=self.interval.value(),
            timeout_seconds=self.timeout.value(),
            retries=self.retries.value(),
            max_seller_pages=self.max_pages.value(),
            rotate_user_agents=self.rotate.isChecked(),
            proxy_file=self.proxy_file.text().strip(),
        ).validate()


class MainWindow(QMainWindow):
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(object)
    fetched_signal = pyqtSignal(object)
    error_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.config = load_config()
        self.items: list[SellerItem] = []
        self.setWindowTitle("EbayViews Desktop")
        self.resize(980, 720)
        self._build_ui()
        self.log_signal.connect(self.append_log)
        self.progress_signal.connect(self.on_progress)
        self.fetched_signal.connect(self.on_items_fetched)
        self.error_signal.connect(self.show_error)
        self.append_log("Use responsibly. Automated traffic may violate marketplace terms or trigger rate limits.")

    def _build_ui(self) -> None:
        root = QWidget(); layout = QVBoxLayout(root)
        warning = QLabel("Responsible-use notice: keep concurrency and request counts low; avoid affecting real marketplace activity.")
        warning.setWordWrap(True); layout.addWidget(warning)
        seller_row = QHBoxLayout()
        self.seller_url = QLineEdit(); self.seller_url.setPlaceholderText("Paste seller page URL…")
        fetch_button = QPushButton("Fetch Items"); fetch_button.clicked.connect(self.fetch_items)
        settings_button = QPushButton("Settings"); settings_button.clicked.connect(self.open_settings)
        seller_row.addWidget(self.seller_url); seller_row.addWidget(fetch_button); seller_row.addWidget(settings_button)
        layout.addLayout(seller_row)
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Select", "Title", "Item ID", "Price"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)
        controls = QHBoxLayout()
        controls.addWidget(QLabel("Views per selected item"))
        self.views_per_item = QSpinBox(); self.views_per_item.setRange(1, 10000); self.views_per_item.setValue(1)
        generate = QPushButton("Generate Views"); generate.clicked.connect(self.generate_views)
        controls.addWidget(self.views_per_item); controls.addWidget(generate); controls.addStretch()
        layout.addLayout(controls)
        self.progress = QProgressBar(); self.progress.setValue(0); layout.addWidget(self.progress)
        self.log = QTextEdit(); self.log.setReadOnly(True); layout.addWidget(self.log)
        self.setCentralWidget(root)

    def open_settings(self) -> None:
        dialog = SettingsDialog(self.config, self)
        if dialog.exec():
            self.config = dialog.config()
            save_config(self.config)
            self.append_log("Settings saved.")

    def fetch_items(self) -> None:
        url = self.seller_url.text().strip()
        self.append_log("Fetching seller items…")
        def worker():
            try:
                fetcher = SellerItemFetcher(timeout_seconds=self.config.timeout_seconds, max_pages=self.config.max_seller_pages)
                self.fetched_signal.emit(fetcher.fetch(url))
            except SellerFetchError as exc:
                self.error_signal.emit(str(exc))
        Thread(target=worker, daemon=True).start()

    def on_items_fetched(self, items: list[SellerItem]) -> None:
        self.items = items
        self.table.setRowCount(len(items))
        for row, item in enumerate(items):
            select = QTableWidgetItem()
            select.setFlags(select.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            select.setCheckState(Qt.CheckState.Checked)
            self.table.setItem(row, 0, select)
            self.table.setItem(row, 1, QTableWidgetItem(item.title))
            self.table.setItem(row, 2, QTableWidgetItem(item.item_id))
            self.table.setItem(row, 3, QTableWidgetItem(item.price))
        self.progress.setValue(0)
        self.append_log(f"Loaded {len(items)} item(s).")

    def selected_items(self) -> list[SellerItem]:
        selected = []
        for row, item in enumerate(self.items):
            cell = self.table.item(row, 0)
            if cell and cell.checkState() == Qt.CheckState.Checked:
                selected.append(item)
        return selected

    def generate_views(self) -> None:
        selected = self.selected_items()
        views = self.views_per_item.value()
        total = max(len(selected) * views, 1)
        self.progress.setValue(0)
        self._completed = 0
        self._total = total
        self.append_log(f"Generating {total} request(s)…")
        def worker():
            try:
                ViewGenerator(self.config).generate(selected, views, progress_callback=self.progress_signal.emit, log_callback=self.log_signal.emit)
            except Exception as exc:
                self.error_signal.emit(str(exc))
        Thread(target=worker, daemon=True).start()

    def on_progress(self, event: ProgressEvent) -> None:
        self._completed = getattr(self, "_completed", 0) + 1
        self.progress.setValue(int((self._completed / max(getattr(self, "_total", 1), 1)) * 100))

    def append_log(self, message: str) -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log.append(f"[{timestamp}] {message}")

    def show_error(self, message: str) -> None:
        self.append_log(f"Error: {message}")
        QMessageBox.warning(self, "EbayViews", message)


def run_app() -> int:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(run_app())
