from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QThread
from PySide6.QtWidgets import (
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from sisgen_automation.ui.workers.export_dbf import ExportDbfWorker
from sisgen_automation.ui.workers.g1 import G1Worker
from sisgen_automation.ui.workers.g11 import G11Worker
from sisgen_automation.ui.workers.g2 import G2Worker
from sisgen_automation.ui.workers.g7 import G7Worker
from sisgen_automation.ui.workers.g8 import G8Worker
from sisgen_automation.ui.workers.templates import TemplateWorker


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self.worker_thread: QThread | None = None
        self.worker: (
            G1Worker
            | TemplateWorker
            | ExportDbfWorker
            | G2Worker
            | G7Worker
            | G8Worker
            | G11Worker
            | None
        ) = None

        self.setWindowTitle("SISGEN Format Automation")
        self.resize(1180, 800)

        self.period_input = QLineEdit("2025-12")
        self.raw_dir_input = QLineEdit(str(Path("data/raw")))
        self.output_dir_input = QLineEdit(str(Path("reports")))
        self.cenhid_catalog_input = QLineEdit(str(Path("config/local/cenhid_units.yaml")))
        self.center_catalog_input = QLineEdit(str(Path("config/local/center_units.yaml")))
        self.g2_catalog_input = QLineEdit(str(Path("config/local/g2_distributors.yaml")))
        self.g7_catalog_input = QLineEdit(str(Path("config/local/g7_units.yaml")))
        self.g8_catalog_input = QLineEdit(str(Path("config/local/g8_clients.yaml")))
        self.g11_catalog_input = QLineEdit(str(Path("config/local/g11_units.yaml")))

        self.validate_g1_button = QPushButton("Validar fuentes G1")
        self.generate_g1_button = QPushButton("Generar TXT G1")
        self.validate_g2_button = QPushButton("Validar fuentes G2")
        self.generate_g2_button = QPushButton("Generar TXT G2")
        self.validate_g7_button = QPushButton("Validar fuentes G7")
        self.generate_g7_button = QPushButton("Generar TXT G7")
        self.validate_g8_button = QPushButton("Validar fuentes G8")
        self.generate_g8_button = QPushButton("Generar TXT G8")
        self.validate_g11_button = QPushButton("Validar fuentes G11")
        self.generate_g11_button = QPushButton("Generar TXT G11")
        self.generate_templates_button = QPushButton("Generar plantillas mensuales")
        self.export_dbf_button = QPushButton("Exportar DBF mensuales")
        self.clear_log_button = QPushButton("Limpiar logs")

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setMinimumHeight(320)

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)

        self._build_ui()
        self._connect_events()
        self._apply_visual_style()

    def _apply_visual_style(self) -> None:
        primary_buttons = [
            self.generate_templates_button,
            self.export_dbf_button,
            self.generate_g1_button,
            self.generate_g2_button,
            self.generate_g7_button,
            self.generate_g8_button,
            self.generate_g11_button,
        ]
        secondary_buttons = [
            self.validate_g1_button,
            self.validate_g2_button,
            self.validate_g7_button,
            self.validate_g8_button,
            self.validate_g11_button,
        ]

        for button in primary_buttons:
            button.setProperty("buttonRole", "primary")
            button.setMinimumHeight(34)

        for button in secondary_buttons:
            button.setProperty("buttonRole", "secondary")
            button.setMinimumHeight(34)

        self.clear_log_button.setProperty("buttonRole", "muted")
        self.clear_log_button.setMinimumHeight(32)

        self.setStyleSheet("""
            QMainWindow {
                background-color: #f6f7fb;
            }

            QLabel {
                font-size: 13px;
            }

            QLineEdit {
                min-height: 28px;
                padding: 4px 8px;
                border: 1px solid #cfd6e4;
                border-radius: 6px;
                background: #ffffff;
            }

            QLineEdit:focus {
                border: 1px solid #2f6fed;
            }

            QTabWidget::pane {
                border: 1px solid #d9deea;
                border-radius: 8px;
                background: #ffffff;
                top: -1px;
            }

            QTabBar::tab {
                padding: 8px 14px;
                margin-right: 2px;
                border: 1px solid #d9deea;
                border-bottom: none;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                background: #eef1f7;
            }

            QTabBar::tab:selected {
                background: #ffffff;
                font-weight: 600;
            }

            QGroupBox {
                margin-top: 12px;
                padding: 12px;
                border: 1px solid #d9deea;
                border-radius: 8px;
                background-color: #ffffff;
                font-weight: 600;
            }

            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 6px;
            }

            QPushButton {
                padding: 7px 14px;
                border-radius: 6px;
                border: 1px solid #b8c1d1;
                background: #ffffff;
            }

            QPushButton:hover {
                background: #f0f3f9;
            }

            QPushButton:disabled {
                color: #9aa4b2;
                background: #edf0f5;
                border-color: #d5dbe6;
            }

            QPushButton[buttonRole="primary"] {
                color: #ffffff;
                background: #1f6feb;
                border: 1px solid #1f6feb;
                font-weight: 600;
            }

            QPushButton[buttonRole="primary"]:hover {
                background: #195dc7;
            }

            QPushButton[buttonRole="secondary"] {
                color: #17324d;
                background: #eef5ff;
                border: 1px solid #9fc2f3;
                font-weight: 600;
            }

            QPushButton[buttonRole="secondary"]:hover {
                background: #deecff;
            }

            QPushButton[buttonRole="muted"] {
                color: #334155;
                background: #f8fafc;
                border: 1px solid #cbd5e1;
            }

            QTextEdit {
                border: 1px solid #d9deea;
                border-radius: 8px;
                background: #0f172a;
                color: #e2e8f0;
                font-family: Consolas, "Courier New", monospace;
                font-size: 12px;
                padding: 8px;
            }
        """)


    def _build_ui(self) -> None:
        root = QWidget()
        root_layout = QVBoxLayout(root)

        title = QLabel("Automatización de formatos SISGEN")
        title.setStyleSheet("font-size: 22px; font-weight: bold;")

        subtitle = QLabel(
            "Herramienta desktop para preparar DBF mensuales y generar formatos SISGEN."
        )
        subtitle.setStyleSheet("color: #555;")

        root_layout.addWidget(title)
        root_layout.addWidget(subtitle)
        root_layout.addWidget(self.tabs)

        self.tabs.addTab(self._build_config_tab(), "1. Configuración")
        self.tabs.addTab(self._build_templates_tab(), "2. Plantillas")
        self.tabs.addTab(self._build_export_tab(), "3. Exportar DBF")
        self.tabs.addTab(self._build_g1_tab(), "4. G1")
        self.tabs.addTab(self._build_g2_tab(), "5. G2")
        self.tabs.addTab(self._build_g7_tab(), "6. G7")
        self.tabs.addTab(self._build_g8_tab(), "7. G8")
        self.tabs.addTab(self._build_g11_tab(), "8. G11")
        self.tabs.addTab(self._build_logs_tab(), "Logs")

        self.setCentralWidget(root)

    def _build_config_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)

        config_group = QGroupBox("Configuración general")
        form = QFormLayout(config_group)

        form.addRow("Periodo YYYY-MM:", self.period_input)
        form.addRow(
            "Carpeta DBF base SISGEN:",
            self._path_row(self.raw_dir_input, self._select_raw_dir),
        )
        form.addRow(
            "Carpeta de salida:",
            self._path_row(self.output_dir_input, self._select_output_dir),
        )
        form.addRow(
            "Catálogo CENHID:",
            self._path_row(self.cenhid_catalog_input, self._select_cenhid_catalog),
        )
        form.addRow(
            "Catálogo CENTER:",
            self._path_row(self.center_catalog_input, self._select_center_catalog),
        )
        form.addRow(
            "Catálogo G2:",
            self._path_row(self.g2_catalog_input, self._select_g2_catalog),
        )
        form.addRow(
            "Catálogo G7:",
            self._path_row(self.g7_catalog_input, self._select_g7_catalog),
        )
        form.addRow(
            "Catálogo G8:",
            self._path_row(self.g8_catalog_input, self._select_g8_catalog),
        )
        form.addRow(
            "Catálogo G11:",
            self._path_row(self.g11_catalog_input, self._select_g11_catalog),
        )

        help_box = QLabel(
            "Configura el periodo, las rutas base y los catálogos locales. "
            "Usa data/raw para crear plantillas y exportar DBF. "
            "Luego usa reports/dbf/YYYY-MM para generar los TXT."
        )
        help_box.setWordWrap(True)
        help_box.setStyleSheet("color: #555;")

        layout.addWidget(config_group)
        layout.addWidget(help_box)
        layout.addStretch()

        return tab

    def _build_templates_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)

        title = QLabel("Plantillas mensuales")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")

        message = QLabel(
            "Genera todas las plantillas Excel del periodo configurado. "
            "Después completa manualmente los campos editables en Excel."
        )
        message.setWordWrap(True)

        actions_group = QGroupBox("Acciones")
        actions_layout = QHBoxLayout(actions_group)
        actions_layout.addWidget(self.generate_templates_button)
        actions_layout.addStretch()

        note = QLabel(
            "Salida: reports/templates. "
            "VEPOEN y VEFAME toman automáticamente el último periodo válido del DBF base."
        )
        note.setWordWrap(True)
        note.setStyleSheet("color: #555;")

        layout.addWidget(title)
        layout.addWidget(message)
        layout.addWidget(actions_group)
        layout.addWidget(note)
        layout.addStretch()

        return tab

    def _build_export_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)

        title = QLabel("Exportar DBF mensuales")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")

        message = QLabel(
            "Valida las plantillas Excel completadas y exporta los DBF mensuales del periodo."
        )
        message.setWordWrap(True)

        actions_group = QGroupBox("Acciones")
        actions_layout = QHBoxLayout(actions_group)
        actions_layout.addWidget(self.export_dbf_button)
        actions_layout.addStretch()

        note = QLabel(
            "Entrada: reports/templates. Salida: reports/dbf/YYYY-MM. "
            "Si una plantilla tiene errores, no se exporta ningún DBF."
        )
        note.setWordWrap(True)
        note.setStyleSheet("color: #555;")

        layout.addWidget(title)
        layout.addWidget(message)
        layout.addWidget(actions_group)
        layout.addWidget(note)
        layout.addStretch()

        return tab

    def _build_g1_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)

        title = QLabel("Formato G1")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")

        description = QLabel(
            "Valida CENHID + CENTER + DACOCE + COMCEN y genera el TXT del Formato G1."
        )
        description.setWordWrap(True)

        actions_group = QGroupBox("Acciones")
        actions_layout = QHBoxLayout(actions_group)

        actions_layout.addWidget(self.validate_g1_button)
        actions_layout.addWidget(self.generate_g1_button)
        actions_layout.addStretch()

        note = QLabel(
            "El TXT se generará en la carpeta de salida configurada. "
            "Si las fuentes tienen errores, la generación se bloquea."
        )
        note.setWordWrap(True)
        note.setStyleSheet("color: #555;")

        layout.addWidget(title)
        layout.addWidget(description)
        layout.addWidget(actions_group)
        layout.addWidget(note)
        layout.addStretch()

        return tab

    def _build_g2_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)

        title = QLabel("Reporte G2")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")

        description = QLabel(
            "Valida VEPOEN.DBF desde la carpeta DBF configurada y genera el TXT del Formato G2."
        )
        description.setWordWrap(True)

        actions_group = QGroupBox("Acciones")
        actions_layout = QHBoxLayout(actions_group)
        actions_layout.addWidget(self.validate_g2_button)
        actions_layout.addWidget(self.generate_g2_button)
        actions_layout.addStretch()

        note = QLabel(
            "Para crear VEPOEN.DBF mensual, usa primero Plantillas y Exportar DBF. "
            "Después la carpeta DBF se actualiza automáticamente y este reporte usa el VEPOEN exportado."
        )
        note.setWordWrap(True)
        note.setStyleSheet("color: #555;")

        layout.addWidget(title)
        layout.addWidget(description)
        layout.addWidget(actions_group)
        layout.addWidget(note)
        layout.addStretch()

        return tab


    def _build_g7_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)

        title = QLabel("Reporte G7")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")

        description = QLabel(
            "Valida COMENE.DBF + VENENE.DBF + COMNET.DBF + TRAENE.DBF + VALENE.DBF "
            "desde la carpeta DBF configurada y genera el TXT del Formato G7."
        )
        description.setWordWrap(True)

        actions_group = QGroupBox("Acciones")
        actions_layout = QHBoxLayout(actions_group)
        actions_layout.addWidget(self.validate_g7_button)
        actions_layout.addWidget(self.generate_g7_button)
        actions_layout.addStretch()

        note = QLabel(
            "Para crear los DBF mensuales de G7, usa primero Plantillas y Exportar DBF. "
            "Después la carpeta DBF se actualiza automáticamente y este reporte usa los DBF exportados."
        )
        note.setWordWrap(True)
        note.setStyleSheet("color: #555;")

        layout.addWidget(title)
        layout.addWidget(description)
        layout.addWidget(actions_group)
        layout.addWidget(note)
        layout.addStretch()

        return tab



    def _build_g8_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)

        title = QLabel("Reporte G8")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")

        description = QLabel(
            "Valida VEFAME.DBF desde la carpeta DBF configurada y genera el TXT del Formato G8."
        )
        description.setWordWrap(True)

        actions_group = QGroupBox("Acciones")
        actions_layout = QHBoxLayout(actions_group)
        actions_layout.addWidget(self.validate_g8_button)
        actions_layout.addWidget(self.generate_g8_button)
        actions_layout.addStretch()

        note = QLabel(
            "Para crear VEFAME.DBF mensual, usa primero Plantillas y Exportar DBF. "
            "Después la carpeta DBF se actualiza automáticamente y este reporte usa el VEFAME exportado."
        )
        note.setWordWrap(True)
        note.setStyleSheet("color: #555;")

        layout.addWidget(title)
        layout.addWidget(description)
        layout.addWidget(actions_group)
        layout.addWidget(note)
        layout.addStretch()

        return tab

    def _build_g11_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)

        title = QLabel("Reporte G11")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")

        description = QLabel(
            "Valida CACEHI.DBF + CACETE.DBF desde la carpeta DBF configurada y genera el TXT del Formato G11."
        )
        description.setWordWrap(True)

        actions_group = QGroupBox("Acciones")
        actions_layout = QHBoxLayout(actions_group)
        actions_layout.addWidget(self.validate_g11_button)
        actions_layout.addWidget(self.generate_g11_button)
        actions_layout.addStretch()

        note = QLabel(
            "Para crear CACEHI.DBF y CACETE.DBF mensuales, usa primero Plantillas y Exportar DBF. "
            "Después la carpeta DBF se actualiza automáticamente y este reporte usa los DBF exportados."
        )
        note.setWordWrap(True)
        note.setStyleSheet("color: #555;")

        layout.addWidget(title)
        layout.addWidget(description)
        layout.addWidget(actions_group)
        layout.addWidget(note)
        layout.addStretch()

        return tab

    def _build_logs_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)

        actions_layout = QHBoxLayout()
        actions_layout.addWidget(self.clear_log_button)
        actions_layout.addStretch()

        layout.addLayout(actions_layout)
        layout.addWidget(self.log_output)

        return tab

    def _path_row(self, line_edit: QLineEdit, callback) -> QWidget:
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)

        button = QPushButton("Seleccionar...")
        button.clicked.connect(callback)

        layout.addWidget(line_edit)
        layout.addWidget(button)

        return container

    def _handle_exported_dbf_dir(self, path: str) -> None:
        self.raw_dir_input.setText(path)
        self._append_log(f"Carpeta DBF actualizada automáticamente: {path}")
        self._append_log("Ahora puedes generar G1, G2, G7, G8 y G11 usando los DBF exportados.")


    def _connect_events(self) -> None:
        self.validate_g1_button.clicked.connect(lambda: self._start_worker("validate"))
        self.generate_g1_button.clicked.connect(lambda: self._start_worker("generate"))
        self.validate_g2_button.clicked.connect(lambda: self._start_g2_worker("validate"))
        self.generate_g2_button.clicked.connect(lambda: self._start_g2_worker("generate"))
        self.validate_g7_button.clicked.connect(lambda: self._start_g7_worker("validate"))
        self.generate_g7_button.clicked.connect(lambda: self._start_g7_worker("generate"))
        self.validate_g8_button.clicked.connect(lambda: self._start_g8_worker("validate"))
        self.generate_g8_button.clicked.connect(lambda: self._start_g8_worker("generate"))
        self.validate_g11_button.clicked.connect(lambda: self._start_g11_worker("validate"))
        self.generate_g11_button.clicked.connect(lambda: self._start_g11_worker("generate"))
        self.generate_templates_button.clicked.connect(self._start_template_worker)
        self.export_dbf_button.clicked.connect(self._start_export_dbf_worker)
        self.clear_log_button.clicked.connect(self.log_output.clear)

    def _select_raw_dir(self) -> None:
        self._select_directory(self.raw_dir_input)

    def _select_output_dir(self) -> None:
        self._select_directory(self.output_dir_input)

    def _select_cenhid_catalog(self) -> None:
        self._select_file(self.cenhid_catalog_input, "YAML (*.yaml *.yml)")

    def _select_center_catalog(self) -> None:
        self._select_file(self.center_catalog_input, "YAML (*.yaml *.yml)")


    def _select_g2_catalog(self) -> None:
        self._select_file(self.g2_catalog_input, "YAML (*.yaml *.yml)")

    def _select_g7_catalog(self) -> None:
        self._select_file(self.g7_catalog_input, "YAML (*.yaml *.yml)")

    def _select_g8_catalog(self) -> None:
        self._select_file(self.g8_catalog_input, "YAML (*.yaml *.yml)")

    def _select_g11_catalog(self) -> None:
        self._select_file(self.g11_catalog_input, "YAML (*.yaml *.yml)")

    def _select_directory(self, target: QLineEdit) -> None:
        selected = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta")

        if selected:
            target.setText(selected)

    def _select_file(self, target: QLineEdit, file_filter: str) -> None:
        selected, _ = QFileDialog.getOpenFileName(self, "Seleccionar archivo", "", file_filter)

        if selected:
            target.setText(selected)

    def _show_logs_tab(self) -> None:
        self.tabs.setCurrentIndex(self.tabs.count() - 1)

    def _start_template_worker(self) -> None:
        if self.worker_thread is not None:
            QMessageBox.warning(self, "Proceso en ejecución", "Ya hay un proceso ejecutándose.")
            return

        self._show_logs_tab()
        self._set_buttons_enabled(False)
        self._append_log("=" * 80)
        self._append_log("Iniciando generación de plantillas...")

        self.worker_thread = QThread()
        self.worker = TemplateWorker(
            period=self.period_input.text().strip(),
            raw_dir=Path(self.raw_dir_input.text().strip()),
            output_dir=Path(self.output_dir_input.text().strip()),
            cenhid_catalog=Path(self.cenhid_catalog_input.text().strip()),
            center_catalog=Path(self.center_catalog_input.text().strip()),
            g2_catalog=Path(self.g2_catalog_input.text().strip()),
            g7_catalog=Path(self.g7_catalog_input.text().strip()),
            g8_catalog=Path(self.g8_catalog_input.text().strip()),
            g11_catalog=Path(self.g11_catalog_input.text().strip()),
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

    def _start_export_dbf_worker(self) -> None:
        if self.worker_thread is not None:
            QMessageBox.warning(self, "Proceso en ejecución", "Ya hay un proceso ejecutándose.")
            return

        self._show_logs_tab()
        self._set_buttons_enabled(False)
        self._append_log("=" * 80)
        self._append_log("Iniciando exportación de DBF...")

        self.worker_thread = QThread()
        self.worker = ExportDbfWorker(
            period=self.period_input.text().strip(),
            raw_dir=Path(self.raw_dir_input.text().strip()),
            output_dir=Path(self.output_dir_input.text().strip()),
            cenhid_catalog=Path(self.cenhid_catalog_input.text().strip()),
            center_catalog=Path(self.center_catalog_input.text().strip()),
            g2_catalog=Path(self.g2_catalog_input.text().strip()),
            g7_catalog=Path(self.g7_catalog_input.text().strip()),
            g8_catalog=Path(self.g8_catalog_input.text().strip()),
            g11_catalog=Path(self.g11_catalog_input.text().strip()),
        )

        self.worker.moveToThread(self.worker_thread)

        self.worker_thread.started.connect(self.worker.run)
        self.worker.log.connect(self._append_log)
        self.worker.exported_dir.connect(self._handle_exported_dbf_dir)
        self.worker.finished.connect(self._handle_success)
        self.worker.failed.connect(self._handle_failure)
        self.worker.finished.connect(self.worker_thread.quit)
        self.worker.failed.connect(self.worker_thread.quit)
        self.worker_thread.finished.connect(self._cleanup_worker)

        self.worker_thread.start()

    def _start_worker(self, action: str) -> None:
        if self.worker_thread is not None:
            QMessageBox.warning(self, "Proceso en ejecución", "Ya hay un proceso ejecutándose.")
            return

        self._show_logs_tab()
        self._set_buttons_enabled(False)
        self._append_log("=" * 80)
        self._append_log("Iniciando proceso G1...")

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

    def _start_g2_worker(self, action: str) -> None:
        if self.worker_thread is not None:
            QMessageBox.warning(self, "Proceso en ejecución", "Ya hay un proceso ejecutándose.")
            return

        self._show_logs_tab()
        self._set_buttons_enabled(False)
        self._append_log("=" * 80)
        self._append_log("Iniciando proceso G2...")

        self.worker_thread = QThread()
        self.worker = G2Worker(
            action=action,
            period=self.period_input.text().strip(),
            vepoen_path=Path(self.raw_dir_input.text().strip()) / "VEPOEN.DBF",
            output_dir=Path(self.output_dir_input.text().strip()),
            g2_catalog=Path(self.g2_catalog_input.text().strip()),
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

    def _start_g7_worker(self, action: str) -> None:
        if self.worker_thread is not None:
            QMessageBox.warning(self, "Proceso en ejecución", "Ya hay un proceso ejecutándose.")
            return

        self._show_logs_tab()
        self._set_buttons_enabled(False)
        self._append_log("=" * 80)
        self._append_log("Iniciando proceso G7...")

        self.worker_thread = QThread()
        self.worker = G7Worker(
            action=action,
            period=self.period_input.text().strip(),
            raw_dir=Path(self.raw_dir_input.text().strip()),
            output_dir=Path(self.output_dir_input.text().strip()),
            g7_catalog=Path(self.g7_catalog_input.text().strip()),
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


    def _start_g8_worker(self, action: str) -> None:
        if self.worker_thread is not None:
            QMessageBox.warning(self, "Proceso en ejecución", "Ya hay un proceso ejecutándose.")
            return

        self._show_logs_tab()
        self._set_buttons_enabled(False)
        self._append_log("=" * 80)
        self._append_log("Iniciando proceso G8...")

        self.worker_thread = QThread()
        self.worker = G8Worker(
            action=action,
            period=self.period_input.text().strip(),
            raw_dir=Path(self.raw_dir_input.text().strip()),
            output_dir=Path(self.output_dir_input.text().strip()),
            g8_catalog=Path(self.g8_catalog_input.text().strip()),
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

    def _start_g11_worker(self, action: str) -> None:
        if self.worker_thread is not None:
            QMessageBox.warning(self, "Proceso en ejecución", "Ya hay un proceso ejecutándose.")
            return

        self._show_logs_tab()
        self._set_buttons_enabled(False)
        self._append_log("=" * 80)
        self._append_log("Iniciando proceso G11...")

        self.worker_thread = QThread()
        self.worker = G11Worker(
            action=action,
            period=self.period_input.text().strip(),
            raw_dir=Path(self.raw_dir_input.text().strip()),
            output_dir=Path(self.output_dir_input.text().strip()),
            g11_catalog=Path(self.g11_catalog_input.text().strip()),
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
        self.generate_templates_button.setEnabled(enabled)
        self.export_dbf_button.setEnabled(enabled)
        self.validate_g1_button.setEnabled(enabled)
        self.generate_g1_button.setEnabled(enabled)
        self.validate_g2_button.setEnabled(enabled)
        self.generate_g2_button.setEnabled(enabled)
        self.validate_g7_button.setEnabled(enabled)
        self.generate_g7_button.setEnabled(enabled)
        self.validate_g8_button.setEnabled(enabled)
        self.generate_g8_button.setEnabled(enabled)
        self.validate_g11_button.setEnabled(enabled)
        self.generate_g11_button.setEnabled(enabled)
        self.clear_log_button.setEnabled(enabled)

    def _append_log(self, message: str) -> None:
        self.log_output.append(message)