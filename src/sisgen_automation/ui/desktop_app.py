from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from sisgen_automation.ui.main_window import MainWindow


def run_desktop_app() -> None:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    run_desktop_app()
