from __future__ import annotations

import sys
import traceback
from pathlib import Path

from PySide6.QtCore import QObject, QThread, Signal
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from sisgen_automation.g1.sources import validate_g1_sources
from sisgen_automation.g1.txt import create_g1_txt


class G1Worker(QObject):
    finished = Signal(str)
    failed = Signal(str)
    log = Signal(str)

    def __init__(
        self,
        *,
        action: str,
        period: str,
        raw_dir: Path,
        output_dir: Path,
        cenhid_catalog: Path,
        center_catalog: Path,
    ) -> None:
        super().__init__()
        self.action = action
        self.period = period
        self.raw_dir = raw_dir
        self.output_dir = output_dir
        self.cenhid_catalog = cenhid_catalog
        self.center_catalog = center_catalog

    def run(self) -> None:
        try:
            cenhid_path = self.raw_dir / "CENHID.DBF"
            center_path = self.raw_dir / "CENTER.DBF"
            dacoce_path = self.raw_dir / "DACOCE.DBF"

            self._ensure_file(cenhid_path)
            self._ensure_file(center_path)
            self._ensure_file(dacoce_path)
            self._ensure_file(self.cenhid_catalog)
            self._ensure_file(self.center_catalog)

            self.log.emit(f"Periodo: {self.period}")
            self.log.emit(f"CENHID: {cenhid_path}")
            self.log.emit(f"CENTER: {center_path}")
            self.log.emit(f"DACOCE: {dacoce_path}")
            self.log.emit("Validando fuentes G1...")

            validation = validate_g1_sources(
                cenhid_path=cenhid_path,
                center_path=center_path,
                dacoce_path=dacoce_path,
                period=self.period,
                cenhid_catalog_path=self.cenhid_catalog,
                center_catalog_path=self.center_catalog,
            )

            self.log.emit(f"Grupos hidro: {validation.hydro_group_count}")
            self.log.emit(f"Centrales hidro: {len(validation.hydro_blocks)}")
            self.log.emit(f"Grupos termo: {validation.thermal_group_count}")
            self.log.emit(f"Centrales termo: {len(validation.thermal_blocks)}")
            self.log.emit(f"Errores: {len(validation.errors)}")
            self.log.emit(f"Advertencias: {len(validation.warnings)}")

            if validation.has_errors:
                for issue in validation.errors[:20]:
                    self.log.emit(
                        f"ERROR | {issue.section} | {issue.source} | "
                        f"{issue.field or ''} | {issue.message} | {issue.value or ''}"
                    )

                raise ValueError(
                    "Las fuentes tienen errores. Revisa los logs antes de generar G1."
                )

            for issue in validation.warnings[:20]:
                self.log.emit(
                    f"WARNING | {issue.section} | {issue.source} | "
                    f"{issue.field or ''} | {issue.message} | {issue.value or ''}"
                )

            if self.action == "validate":
                self.finished.emit("Validación G1 completada.")
                return

            self.output_dir.mkdir(parents=True, exist_ok=True)
            output_path = self.output_dir / f"G1_{self.period.replace('-', '_')}.txt"

            self.log.emit("Generando TXT G1...")

            result = create_g1_txt(
                cenhid_path=cenhid_path,
                center_path=center_path,
                dacoce_path=dacoce_path,
                period=self.period,
                cenhid_catalog_path=self.cenhid_catalog,
                center_catalog_path=self.center_catalog,
                output_path=output_path,
            )

            self.finished.emit(f"TXT G1 generado correctamente: {result.output_path}")
        except Exception as error:  # noqa: BLE001
            details = traceback.format_exc()
            self.failed.emit(f"{error}\n\nDetalle técnico:\n{details}")

    @staticmethod
    def _ensure_file(path: Path) -> None:
        if not path.exists():
            raise FileNotFoundError(f"No existe el archivo requerido: {path}")


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self.worker_thread: QThread | None = None
        self.worker: G1Worker | None = None

        self.setWindowTitle("SISGEN Format Automation")
        self.resize(980, 680)

        self.period_input = QLineEdit("2025-12")
        self.raw_dir_input = QLineEdit(str(Path("data/raw")))
        self.output_dir_input = QLineEdit(str(Path("reports")))
        self.cenhid_catalog_input = QLineEdit(str(Path("config/local/cenhid_units.yaml")))
        self.center_catalog_input = QLineEdit(str(Path("config/local/center_units.yaml")))

        self.validate_button = QPushButton("Validar fuentes G1")
        self.generate_button = QPushButton("Generar TXT G1")
        self.clear_log_button = QPushButton("Limpiar logs")

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)

        self._build_ui()
        self._connect_events()

    def _build_ui(self) -> None:
        root = QWidget()
        root_layout = QVBoxLayout(root)

        title = QLabel("Automatización de formatos SISGEN")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")

        subtitle = QLabel(
            "MVP desktop para validar fuentes CENHID, CENTER, DACOCE y generar Formato G1 TXT."
        )
        subtitle.setStyleSheet("color: #555;")

        root_layout.addWidget(title)
        root_layout.addWidget(subtitle)

        config_group = QGroupBox("Configuración")
        form = QFormLayout(config_group)

        form.addRow("Periodo YYYY-MM:", self.period_input)
        form.addRow("Carpeta DBF históricos:", self._path_row(self.raw_dir_input, self._select_raw_dir))
        form.addRow("Carpeta de salida:", self._path_row(self.output_dir_input, self._select_output_dir))
        form.addRow(
            "Catálogo CENHID:",
            self._path_row(self.cenhid_catalog_input, self._select_cenhid_catalog),
        )
        form.addRow(
            "Catálogo CENTER:",
            self._path_row(self.center_catalog_input, self._select_center_catalog),
        )

        root_layout.addWidget(config_group)

        actions_layout = QHBoxLayout()
        actions_layout.addWidget(self.validate_button)
        actions_layout.addWidget(self.generate_button)
        actions_layout.addWidget(self.clear_log_button)
        actions_layout.addStretch()

        root_layout.addLayout(actions_layout)

        log_group = QGroupBox("Logs")
        log_layout = QVBoxLayout(log_group)
        log_layout.addWidget(self.log_output)

        root_layout.addWidget(log_group)

        self.setCentralWidget(root)

    def _path_row(self, line_edit: QLineEdit, callback) -> QWidget:
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)

        button = QPushButton("Seleccionar...")
        button.clicked.connect(callback)

        layout.addWidget(line_edit)
        layout.addWidget(button)

        return container

    def _connect_events(self) -> None:
        self.validate_button.clicked.connect(lambda: self._start_worker("validate"))
        self.generate_button.clicked.connect(lambda: self._start_worker("generate"))
        self.clear_log_button.clicked.connect(self.log_output.clear)

    def _select_raw_dir(self) -> None:
        self._select_directory(self.raw_dir_input)

    def _select_output_dir(self) -> None:
        self._select_directory(self.output_dir_input)

    def _select_cenhid_catalog(self) -> None:
        self._select_file(self.cenhid_catalog_input, "YAML (*.yaml *.yml)")

    def _select_center_catalog(self) -> None:
        self._select_file(self.center_catalog_input, "YAML (*.yaml *.yml)")

    def _select_directory(self, target: QLineEdit) -> None:
        selected = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta")

        if selected:
            target.setText(selected)

    def _select_file(self, target: QLineEdit, file_filter: str) -> None:
        selected, _ = QFileDialog.getOpenFileName(self, "Seleccionar archivo", "", file_filter)

        if selected:
            target.setText(selected)

    def _start_worker(self, action: str) -> None:
        if self.worker_thread is not None:
            QMessageBox.warning(self, "Proceso en ejecución", "Ya hay un proceso ejecutándose.")
            return

        self._set_buttons_enabled(False)
        self._append_log("=" * 80)
        self._append_log("Iniciando proceso...")

        self.worker_thread = QThread()
        self.worker = G1Worker(
            action=action,
            period=self.period_input.text().strip(),
            raw_dir=Path(self.raw_dir_input.text().strip()),
            output_dir=Path(self.output_dir_input.text().strip()),
            cenhid_catalog=Path(self.cenhid_catalog_input.text().strip()),
            center_catalog=Path(self.center_catalog_input.text().strip()),
        )

        self.worker.moveToThread(self.worker_thread)

        self.worker_thread.started.connect(self.worker.run)
        self.worker.log.connect(self._append_log)
        self.worker.finished.connect(self._handle_success)
        self.worker.failed.connect(self._handle_failure)
        self.worker.finished.connect(self.worker_thread.quit)
        self.worker.failed.connect(self.worker_thread.quit)
        self.worker_thread.finished.connect(self._cleanup_worker)

        self.worker_thread.start()

    def _handle_success(self, message: str) -> None:
        self._append_log(message)
        QMessageBox.information(self, "Proceso completado", message)

    def _handle_failure(self, message: str) -> None:
        self._append_log("ERROR:")
        self._append_log(message)
        QMessageBox.critical(self, "Error", message.split("\n\n")[0])

    def _cleanup_worker(self) -> None:
        self.worker = None
        self.worker_thread = None
        self._set_buttons_enabled(True)

    def _set_buttons_enabled(self, enabled: bool) -> None:
        self.validate_button.setEnabled(enabled)
        self.generate_button.setEnabled(enabled)
        self.clear_log_button.setEnabled(enabled)

    def _append_log(self, message: str) -> None:
        self.log_output.append(message)


def run_desktop_app() -> None:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    run_desktop_app()