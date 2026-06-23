from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QThread
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from sisgen_automation.catalogs.g1_repository import (
    list_g1_units,
    set_g1_unit_active,
)
from sisgen_automation.catalogs.g2_repository import (
    create_g2_distributor,
    list_g2_distributors,
    set_g2_distributor_active,
    update_g2_distributor,
)
from sisgen_automation.ui.workers.export_dbf import ExportDbfWorker
from sisgen_automation.ui.workers.g1 import G1Worker
from sisgen_automation.ui.workers.g11 import G11Worker
from sisgen_automation.ui.workers.g2 import G2Worker
from sisgen_automation.ui.workers.g7 import G7Worker
from sisgen_automation.ui.workers.g8 import G8Worker
from sisgen_automation.ui.workers.u2 import U2Worker
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
            | U2Worker
            | G11Worker
            | None
        ) = None

        self.setWindowTitle("SISGEN Format Automation")
        self.resize(1180, 800)

        self.period_input = QLineEdit("2025-12")
        self.raw_dir_input = QLineEdit(str(Path("data/raw")))
        self.templates_dir_input = QLineEdit(str(Path("reports/templates")))
        self.report_dbf_dir_input = QLineEdit(str(Path("reports/dbf/2025-12")))
        self.output_dir_input = QLineEdit(str(Path("reports/txt/2025-12")))
        self.u2_catalog_input = QLineEdit(str(Path("config/local/u2_ciiu.yaml")))
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
        self.validate_u2_button = QPushButton("Validar fuentes U2")
        self.generate_u2_button = QPushButton("Generar TXT U2")
        self.validate_g11_button = QPushButton("Validar fuentes G11")
        self.generate_g11_button = QPushButton("Generar TXT G11")
        self.generate_g1_templates_button = QPushButton("Generar G1")
        self.generate_g2_templates_button = QPushButton("Generar G2")
        self.generate_g7_templates_button = QPushButton("Generar G7")
        self.generate_g8_templates_button = QPushButton("Generar G8")
        self.generate_u2_templates_button = QPushButton("Generar U2")
        self.generate_g11_templates_button = QPushButton("Generar G11")
        self.generate_templates_button = QPushButton("Generar todas")
        self.activate_g1_unit_button = QPushButton("Activar")
        self.deactivate_g1_unit_button = QPushButton("Desactivar")
        self.new_g2_distributor_button = QPushButton("Nuevo")
        self.edit_g2_distributor_button = QPushButton("Editar")
        self.activate_g2_distributor_button = QPushButton("Activar")
        self.deactivate_g2_distributor_button = QPushButton("Desactivar")
        self.export_g1_dbf_button = QPushButton("Exportar G1")
        self.export_g2_dbf_button = QPushButton("Exportar G2")
        self.export_g7_dbf_button = QPushButton("Exportar G7")
        self.export_g8_dbf_button = QPushButton("Exportar G8")
        self.export_u2_dbf_button = QPushButton("Exportar U2")
        self.export_g11_dbf_button = QPushButton("Exportar G11")
        self.export_dbf_button = QPushButton("Exportar todo")
        self.clear_log_button = QPushButton("Limpiar logs")

        self.g1_catalog_table = QTableWidget(0, 9)
        self.g1_catalog_table.setHorizontalHeaderLabels([
            "ID",
            "Fuente",
            "Central",
            "CCODCON",
            "Tipo",
            "Unidad",
            "NPOTINS",
            "NPOTEFE",
            "Activo",
        ])
        self.g1_catalog_table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )

        self.g2_catalog_table = QTableWidget(0, 5)
        self.g2_catalog_table.setHorizontalHeaderLabels([
            "ID",
            "Codigo",
            "Distribuidora",
            "Activo",
            "Notas",
        ])
        self.g2_catalog_table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )

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
            self.generate_g1_templates_button,
            self.generate_g2_templates_button,
            self.generate_g7_templates_button,
            self.generate_g8_templates_button,
            self.generate_u2_templates_button,
            self.generate_g11_templates_button,
            self.generate_templates_button,
            self.export_g1_dbf_button,
            self.export_g2_dbf_button,
            self.export_g7_dbf_button,
            self.export_g8_dbf_button,
            self.export_u2_dbf_button,
            self.export_g11_dbf_button,
            self.export_dbf_button,
            self.generate_g1_button,
            self.generate_g2_button,
            self.generate_g7_button,
            self.generate_g8_button,
            self.generate_u2_button,
            self.generate_g11_button,
        ]
        secondary_buttons = [
            self.validate_g1_button,
            self.validate_g2_button,
            self.validate_g7_button,
            self.validate_g8_button,
            self.validate_u2_button,
            self.validate_g11_button,
            self.activate_g1_unit_button,
            self.deactivate_g1_unit_button,
            self.new_g2_distributor_button,
            self.edit_g2_distributor_button,
            self.activate_g2_distributor_button,
            self.deactivate_g2_distributor_button,
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
        self.tabs.addTab(self._build_prepare_dbf_tab(), "2. Preparar DBF")
        self.tabs.addTab(self._build_txt_tab(), "3. Generar TXT")
        self.tabs.addTab(self._build_g1_catalog_tab(), "4. Catalogo G1")
        self.tabs.addTab(self._build_g2_catalog_tab(), "5. Catalogo G2")
        self.tabs.addTab(self._build_logs_tab(), "Logs")

        self.setCentralWidget(root)

    def _build_config_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)

        config_group = QGroupBox("Configuración general")
        form = QFormLayout(config_group)

        form.addRow("Periodo YYYY-MM:", self.period_input)
        form.addRow(
            "Carpeta DBF historicos:",
            self._path_row(self.raw_dir_input, self._select_raw_dir),
        )
        form.addRow(
            "Carpeta plantillas Excel:",
            self._path_row(self.templates_dir_input, self._select_templates_dir),
        )
        form.addRow(
            "Carpeta DBF generados:",
            self._path_row(self.report_dbf_dir_input, self._select_report_dbf_dir),
        )
        form.addRow(
            "Carpeta TXT generados:",
            self._path_row(self.output_dir_input, self._select_output_dir),
        )
        # Catalogo G1 usa SQLite interno.
        # Las rutas YAML CENHID/CENTER se mantienen solo como respaldo tecnico.
        form.addRow(
            "Catálogo U2:",
            self._path_row(self.u2_catalog_input, self._select_u2_catalog),
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
            "Configura el periodo, las cuatro rutas operativas y los catálogos locales. "
            "Las carpetas DBF historicos y DBF generados pueden ser la misma ruta. "
            "Si usas la misma ruta, conserva una copia de seguridad de los DBF base."
        )
        help_box.setWordWrap(True)
        help_box.setStyleSheet("color: #555;")

        layout.addWidget(config_group)
        layout.addWidget(help_box)
        layout.addStretch()

        return tab

    def _build_prepare_dbf_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)

        title = QLabel("Preparar DBF")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")

        description = QLabel(
            "Genera plantillas Excel y exporta DBF mensuales por formato. "
            "Trabaja un formato a la vez para evitar que un error bloquee todo el flujo."
        )
        description.setWordWrap(True)

        templates_group = QGroupBox("1. Generar plantillas Excel")
        templates_layout = QHBoxLayout(templates_group)
        templates_layout.addWidget(self.generate_g1_templates_button)
        templates_layout.addWidget(self.generate_g2_templates_button)
        templates_layout.addWidget(self.generate_g7_templates_button)
        templates_layout.addWidget(self.generate_g8_templates_button)
        templates_layout.addWidget(self.generate_u2_templates_button)
        templates_layout.addWidget(self.generate_g11_templates_button)
        templates_layout.addWidget(self.generate_templates_button)
        templates_layout.addStretch()

        export_group = QGroupBox("2. Exportar DBF")
        export_layout = QHBoxLayout(export_group)
        export_layout.addWidget(self.export_g1_dbf_button)
        export_layout.addWidget(self.export_g2_dbf_button)
        export_layout.addWidget(self.export_g7_dbf_button)
        export_layout.addWidget(self.export_g8_dbf_button)
        export_layout.addWidget(self.export_u2_dbf_button)
        export_layout.addWidget(self.export_g11_dbf_button)
        export_layout.addWidget(self.export_dbf_button)
        export_layout.addStretch()

        note = QLabel(
            "Entrada: carpeta DBF historicos y carpeta plantillas Excel. "
            "Salida: carpeta DBF generados."
        )
        note.setWordWrap(True)
        note.setStyleSheet("color: #555;")

        layout.addWidget(title)
        layout.addWidget(description)
        layout.addWidget(templates_group)
        layout.addWidget(export_group)
        layout.addWidget(note)
        layout.addStretch()

        return tab

    def _build_txt_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)

        title = QLabel("Generar TXT")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")

        description = QLabel(
            "Valida fuentes desde la carpeta DBF generados y crea los TXT finales "
            "en la carpeta TXT generados."
        )
        description.setWordWrap(True)

        g1_group = QGroupBox("G1")
        g1_layout = QHBoxLayout(g1_group)
        g1_layout.addWidget(QLabel("CENHID + CENTER + DACOCE + COMCEN"))
        g1_layout.addStretch()
        g1_layout.addWidget(self.validate_g1_button)
        g1_layout.addWidget(self.generate_g1_button)

        g2_group = QGroupBox("G2")
        g2_layout = QHBoxLayout(g2_group)
        g2_layout.addWidget(QLabel("VEPOEN"))
        g2_layout.addStretch()
        g2_layout.addWidget(self.validate_g2_button)
        g2_layout.addWidget(self.generate_g2_button)

        g7_group = QGroupBox("G7")
        g7_layout = QHBoxLayout(g7_group)
        g7_layout.addWidget(QLabel("COMENE + VENENE + COMNET + TRAENE + VALENE"))
        g7_layout.addStretch()
        g7_layout.addWidget(self.validate_g7_button)
        g7_layout.addWidget(self.generate_g7_button)

        g8_group = QGroupBox("G8")
        g8_layout = QHBoxLayout(g8_group)
        g8_layout.addWidget(QLabel("VEFAME"))
        g8_layout.addStretch()
        g8_layout.addWidget(self.validate_g8_button)
        g8_layout.addWidget(self.generate_g8_button)

        u2_group = QGroupBox("U2")
        u2_layout = QHBoxLayout(u2_group)
        u2_layout.addWidget(QLabel("CIUGEN"))
        u2_layout.addStretch()
        u2_layout.addWidget(self.validate_u2_button)
        u2_layout.addWidget(self.generate_u2_button)

        g11_group = QGroupBox("G11")
        g11_layout = QHBoxLayout(g11_group)
        g11_layout.addWidget(QLabel("CACEHI + CACETE"))
        g11_layout.addStretch()
        g11_layout.addWidget(self.validate_g11_button)
        g11_layout.addWidget(self.generate_g11_button)

        note = QLabel(
            "Antes de generar TXT, exporta los DBF del formato correspondiente. "
            "La validacion debe quedar sin errores."
        )
        note.setWordWrap(True)
        note.setStyleSheet("color: #555;")

        layout.addWidget(title)
        layout.addWidget(description)
        layout.addWidget(g1_group)
        layout.addWidget(g2_group)
        layout.addWidget(g7_group)
        layout.addWidget(g8_group)
        layout.addWidget(u2_group)
        layout.addWidget(g11_group)
        layout.addWidget(note)
        layout.addStretch()

        return tab

    def _build_g1_catalog_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)

        title = QLabel("Catalogo G1")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")

        description = QLabel(
            "Gestiona las unidades CENHID y CENTER cargadas en el catalogo local SQLite. "
            "Usa Activar/Desactivar para controlar si una unidad participa en la generacion."
        )
        description.setWordWrap(True)

        actions = QHBoxLayout()
        actions.addWidget(self.activate_g1_unit_button)
        actions.addWidget(self.deactivate_g1_unit_button)
        actions.addStretch()

        layout.addWidget(title)
        layout.addWidget(description)
        layout.addLayout(actions)
        layout.addWidget(self.g1_catalog_table)

        self._refresh_g1_catalog_table()

        return tab

    def _refresh_g1_catalog_table(self) -> None:
        catalog_db = Path("data/catalogs/sisgen_catalogs.db")
        self.g1_catalog_table.setRowCount(0)

        if not catalog_db.exists():
            self._append_log(
                "Catalogo G1 SQLite no encontrado. Ejecuta primero la migracion YAML -> SQLite."
            )
            return

        rows = list_g1_units(catalog_db)
        self.g1_catalog_table.setRowCount(len(rows))

        for row_index, row in enumerate(rows):
            values = [
                row["id"],
                row["source_format"],
                row["central"],
                row["ccodcon"],
                row["ctipgru"] or "-",
                row["cnomnum"],
                row["npotins"],
                row["npotefe"],
                "si" if row["active"] else "no",
            ]

            for column_index, value in enumerate(values):
                self.g1_catalog_table.setItem(
                    row_index,
                    column_index,
                    QTableWidgetItem(str(value)),
                )

        self.g1_catalog_table.resizeColumnsToContents()
        self._append_log(f"Catalogo G1 cargado: {len(rows)} unidades.")

    def _selected_g1_catalog_id(self) -> int | None:
        row = self.g1_catalog_table.currentRow()
        if row < 0:
            self._append_log("Selecciona una unidad del Catalogo G1.")
            return None

        item = self.g1_catalog_table.item(row, 0)
        if item is None:
            self._append_log("No se pudo leer el ID de la unidad seleccionada.")
            return None

        try:
            return int(item.text())
        except ValueError:
            self._append_log(f"ID de unidad invalido: {item.text()}")
            return None

    def _set_selected_g1_active(self, active: bool) -> None:
        unit_id = self._selected_g1_catalog_id()
        if unit_id is None:
            return

        catalog_db = Path("data/catalogs/sisgen_catalogs.db")
        if not catalog_db.exists():
            self._append_log("Catalogo G1 SQLite no encontrado.")
            return

        unit = set_g1_unit_active(catalog_db, unit_id=unit_id, active=active)
        action = "activada" if active else "desactivada"
        self._append_log(
            f"Unidad {action}: id={unit['id']} {unit['source_format']} "
            f"{unit['central']} {unit['cnomnum']}"
        )
        self._refresh_g1_catalog_table()

    def _build_g2_catalog_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)

        title = QLabel("Catalogo G2")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")

        description = QLabel(
            "Gestiona las distribuidoras VEPOEN cargadas en el catalogo local SQLite. "
            "Usa Activar/Desactivar para controlar si una distribuidora participa en la generacion."
        )
        description.setWordWrap(True)

        actions = QHBoxLayout()
        actions.addWidget(self.new_g2_distributor_button)
        actions.addWidget(self.edit_g2_distributor_button)
        actions.addWidget(self.activate_g2_distributor_button)
        actions.addWidget(self.deactivate_g2_distributor_button)
        actions.addStretch()

        layout.addWidget(title)
        layout.addWidget(description)
        layout.addLayout(actions)
        layout.addWidget(self.g2_catalog_table)

        self._refresh_g2_catalog_table()

        return tab

    def _refresh_g2_catalog_table(self) -> None:
        catalog_db = Path("data/catalogs/sisgen_catalogs.db")
        self.g2_catalog_table.setRowCount(0)

        if not catalog_db.exists():
            self._append_log(
                "Catalogo G2 SQLite no encontrado. Ejecuta primero la migracion YAML -> SQLite."
            )
            return

        rows = list_g2_distributors(catalog_db)
        self.g2_catalog_table.setRowCount(len(rows))

        for row_index, row in enumerate(rows):
            values = [
                row["id"],
                row["ccoddis"],
                row["display_name"],
                "si" if row["active"] else "no",
                row["notes"] or "",
            ]

            for column_index, value in enumerate(values):
                self.g2_catalog_table.setItem(
                    row_index,
                    column_index,
                    QTableWidgetItem(str(value)),
                )

        self.g2_catalog_table.resizeColumnsToContents()
        self._append_log(f"Catalogo G2 cargado: {len(rows)} distribuidoras.")

    def _selected_g2_distributor_id(self) -> int | None:
        row = self.g2_catalog_table.currentRow()
        if row < 0:
            self._append_log("Selecciona una distribuidora del Catalogo G2.")
            return None

        item = self.g2_catalog_table.item(row, 0)
        if item is None:
            self._append_log("No se pudo leer el ID de la distribuidora seleccionada.")
            return None

        try:
            return int(item.text())
        except ValueError:
            self._append_log(f"ID de distribuidora invalido: {item.text()}")
            return None

    def _prompt_g2_distributor_values(
        self,
        *,
        title: str,
        ccoddis: str = "",
        display_name: str = "",
        notes: str = "",
    ) -> tuple[str, str, str] | None:
        code, ok = QInputDialog.getText(
            self,
            title,
            "Codigo CCODDIS:",
            QLineEdit.EchoMode.Normal,
            ccoddis,
        )
        if not ok:
            return None

        name, ok = QInputDialog.getText(
            self,
            title,
            "Nombre distribuidora:",
            QLineEdit.EchoMode.Normal,
            display_name,
        )
        if not ok:
            return None

        clean_notes, ok = QInputDialog.getText(
            self,
            title,
            "Notas:",
            QLineEdit.EchoMode.Normal,
            notes,
        )
        if not ok:
            return None

        code = code.strip().upper()
        name = name.strip()
        clean_notes = clean_notes.strip()

        if not code or not name:
            QMessageBox.warning(
                self,
                "Catalogo G2",
                "Codigo CCODDIS y nombre son obligatorios.",
            )
            return None

        return code, name, clean_notes

    def _create_g2_distributor(self) -> None:
        values = self._prompt_g2_distributor_values(title="Nueva distribuidora G2")
        if values is None:
            return

        code, name, notes = values
        catalog_db = Path("data/catalogs/sisgen_catalogs.db")

        try:
            distributor = create_g2_distributor(
                catalog_db,
                ccoddis=code,
                display_name=name,
                notes=notes,
                active=True,
            )
        except (FileNotFoundError, ValueError) as error:
            QMessageBox.warning(self, "Catalogo G2", str(error))
            self._append_log(f"No se pudo crear distribuidora G2: {error}")
            return

        self._append_log(
            f"Distribuidora creada: id={distributor['id']} "
            f"{distributor['ccoddis']} {distributor['display_name']}"
        )
        self._refresh_g2_catalog_table()

    def _edit_selected_g2_distributor(self) -> None:
        distributor_id = self._selected_g2_distributor_id()
        if distributor_id is None:
            return

        row = self.g2_catalog_table.currentRow()
        code_item = self.g2_catalog_table.item(row, 1)
        name_item = self.g2_catalog_table.item(row, 2)
        notes_item = self.g2_catalog_table.item(row, 4)

        current_code = code_item.text() if code_item is not None else ""
        current_name = name_item.text() if name_item is not None else ""
        current_notes = notes_item.text() if notes_item is not None else ""

        values = self._prompt_g2_distributor_values(
            title="Editar distribuidora G2",
            ccoddis=current_code,
            display_name=current_name,
            notes=current_notes,
        )
        if values is None:
            return

        code, name, notes = values
        catalog_db = Path("data/catalogs/sisgen_catalogs.db")

        try:
            distributor = update_g2_distributor(
                catalog_db,
                distributor_id=distributor_id,
                ccoddis=code,
                display_name=name,
                notes=notes,
            )
        except (FileNotFoundError, ValueError) as error:
            QMessageBox.warning(self, "Catalogo G2", str(error))
            self._append_log(f"No se pudo editar distribuidora G2: {error}")
            return

        self._append_log(
            f"Distribuidora editada: id={distributor['id']} "
            f"{distributor['ccoddis']} {distributor['display_name']}"
        )
        self._refresh_g2_catalog_table()

    def _set_selected_g2_active(self, active: bool) -> None:
        distributor_id = self._selected_g2_distributor_id()
        if distributor_id is None:
            return

        catalog_db = Path("data/catalogs/sisgen_catalogs.db")
        if not catalog_db.exists():
            self._append_log("Catalogo G2 SQLite no encontrado.")
            return

        distributor = set_g2_distributor_active(
            catalog_db,
            distributor_id=distributor_id,
            active=active,
        )
        action = "activada" if active else "desactivada"
        self._append_log(
            f"Distribuidora {action}: id={distributor['id']} "
            f"{distributor['ccoddis']} {distributor['display_name']}"
        )
        self._refresh_g2_catalog_table()

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
        self.report_dbf_dir_input.setText(path)
        self._append_log(f"Carpeta DBF generados actualizada automáticamente: {path}")
        self._append_log("Ahora puedes generar G1, G2, G7, G8, U2 y G11 usando los DBF exportados.")

    def _connect_events(self) -> None:
        self.validate_g1_button.clicked.connect(lambda: self._start_worker("validate"))
        self.generate_g1_button.clicked.connect(lambda: self._start_worker("generate"))
        self.validate_g2_button.clicked.connect(lambda: self._start_g2_worker("validate"))
        self.generate_g2_button.clicked.connect(lambda: self._start_g2_worker("generate"))
        self.validate_g7_button.clicked.connect(lambda: self._start_g7_worker("validate"))
        self.generate_g7_button.clicked.connect(lambda: self._start_g7_worker("generate"))
        self.validate_g8_button.clicked.connect(lambda: self._start_g8_worker("validate"))
        self.generate_g8_button.clicked.connect(lambda: self._start_g8_worker("generate"))
        self.validate_u2_button.clicked.connect(lambda: self._start_u2_worker("validate"))
        self.generate_u2_button.clicked.connect(lambda: self._start_u2_worker("generate"))
        self.validate_g11_button.clicked.connect(lambda: self._start_g11_worker("validate"))
        self.generate_g11_button.clicked.connect(lambda: self._start_g11_worker("generate"))
        self.generate_g1_templates_button.clicked.connect(lambda: self._start_template_worker("G1"))
        self.generate_g2_templates_button.clicked.connect(lambda: self._start_template_worker("G2"))
        self.generate_g7_templates_button.clicked.connect(lambda: self._start_template_worker("G7"))
        self.generate_g8_templates_button.clicked.connect(lambda: self._start_template_worker("G8"))
        self.generate_u2_templates_button.clicked.connect(lambda: self._start_template_worker("U2"))
        self.generate_g11_templates_button.clicked.connect(lambda: self._start_template_worker("G11"))
        self.generate_templates_button.clicked.connect(lambda: self._start_template_worker("ALL"))
        self.activate_g1_unit_button.clicked.connect(lambda: self._set_selected_g1_active(True))
        self.deactivate_g1_unit_button.clicked.connect(lambda: self._set_selected_g1_active(False))
        self.new_g2_distributor_button.clicked.connect(self._create_g2_distributor)
        self.edit_g2_distributor_button.clicked.connect(self._edit_selected_g2_distributor)
        self.activate_g2_distributor_button.clicked.connect(lambda: self._set_selected_g2_active(True))
        self.deactivate_g2_distributor_button.clicked.connect(lambda: self._set_selected_g2_active(False))
        self.export_g1_dbf_button.clicked.connect(lambda: self._start_export_dbf_worker("G1"))
        self.export_g2_dbf_button.clicked.connect(lambda: self._start_export_dbf_worker("G2"))
        self.export_g7_dbf_button.clicked.connect(lambda: self._start_export_dbf_worker("G7"))
        self.export_g8_dbf_button.clicked.connect(lambda: self._start_export_dbf_worker("G8"))
        self.export_u2_dbf_button.clicked.connect(lambda: self._start_export_dbf_worker("U2"))
        self.export_g11_dbf_button.clicked.connect(lambda: self._start_export_dbf_worker("G11"))
        self.export_dbf_button.clicked.connect(lambda: self._start_export_dbf_worker("ALL"))
        self.clear_log_button.clicked.connect(self.log_output.clear)

    def _select_raw_dir(self) -> None:
        self._select_directory(self.raw_dir_input)

    def _select_output_dir(self) -> None:
        self._select_directory(self.output_dir_input)

    def _select_templates_dir(self) -> None:
        self._select_directory(self.templates_dir_input)

    def _select_report_dbf_dir(self) -> None:
        self._select_directory(self.report_dbf_dir_input)

    def _select_u2_catalog(self) -> None:
        self._select_file(self.u2_catalog_input, "YAML (*.yaml *.yml)")

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

    def _start_template_worker(self, format_key: str = "ALL") -> None:
        if self.worker_thread is not None:
            QMessageBox.warning(self, "Proceso en ejecución", "Ya hay un proceso ejecutándose.")
            return

        self._show_logs_tab()
        self._set_buttons_enabled(False)
        self._append_log("=" * 80)
        self._append_log(f"Iniciando generación de plantillas ({format_key})...")

        self.worker_thread = QThread()
        self.worker = TemplateWorker(
            period=self.period_input.text().strip(),
            raw_dir=Path(self.raw_dir_input.text().strip()),
            output_dir=Path(self.templates_dir_input.text().strip()),
            format_key=format_key,
            cenhid_catalog=Path("config/local/cenhid_units.yaml"),
            center_catalog=Path("config/local/center_units.yaml"),
            g1_catalog_db=Path("data/catalogs/sisgen_catalogs.db"),
            g2_catalog_db=Path("data/catalogs/sisgen_catalogs.db"),
            u2_catalog=Path(self.u2_catalog_input.text().strip()),
            g2_catalog=Path("config/local/g2_distributors.yaml"),
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

    def _start_export_dbf_worker(self, format_key: str = "ALL") -> None:
        if self.worker_thread is not None:
            QMessageBox.warning(self, "Proceso en ejecución", "Ya hay un proceso ejecutándose.")
            return

        self._show_logs_tab()
        self._set_buttons_enabled(False)
        self._append_log("=" * 80)
        self._append_log(f"Iniciando exportacion de DBF ({format_key})...")

        self.worker_thread = QThread()
        self.worker = ExportDbfWorker(
            period=self.period_input.text().strip(),
            raw_dir=Path(self.raw_dir_input.text().strip()),
            output_dir=Path(self.report_dbf_dir_input.text().strip()),
            templates_dir=Path(self.templates_dir_input.text().strip()),
            format_key=format_key,
            cenhid_catalog=Path("config/local/cenhid_units.yaml"),
            center_catalog=Path("config/local/center_units.yaml"),
            u2_catalog=Path(self.u2_catalog_input.text().strip()),
            g2_catalog=Path("config/local/g2_distributors.yaml"),
            g7_catalog=Path(self.g7_catalog_input.text().strip()),
            g8_catalog=Path(self.g8_catalog_input.text().strip()),
            g11_catalog=Path(self.g11_catalog_input.text().strip()),
            g1_catalog_db=Path("data/catalogs/sisgen_catalogs.db"),
            g2_catalog_db=Path("data/catalogs/sisgen_catalogs.db"),
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
            raw_dir=Path(self.report_dbf_dir_input.text().strip()),
            output_dir=Path(self.output_dir_input.text().strip()),
            cenhid_catalog=Path("config/local/cenhid_units.yaml"),
            center_catalog=Path("config/local/center_units.yaml"),
            g1_catalog_db=Path("data/catalogs/sisgen_catalogs.db"),
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
            vepoen_path=Path(self.report_dbf_dir_input.text().strip()) / "VEPOEN.DBF",
            output_dir=Path(self.output_dir_input.text().strip()),
            g2_catalog=Path("config/local/g2_distributors.yaml"),
            g2_catalog_db=Path("data/catalogs/sisgen_catalogs.db"),
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
            raw_dir=Path(self.report_dbf_dir_input.text().strip()),
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
            raw_dir=Path(self.report_dbf_dir_input.text().strip()),
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


    def _start_u2_worker(self, action: str) -> None:
        if self.worker_thread is not None:
            QMessageBox.warning(self, "Proceso en ejecución", "Ya hay un proceso ejecutándose.")
            return

        self._show_logs_tab()
        self._set_buttons_enabled(False)
        self._append_log("=" * 80)
        self._append_log("Iniciando proceso U2...")

        self.worker_thread = QThread()
        self.worker = U2Worker(
            action=action,
            period=self.period_input.text().strip(),
            raw_dir=Path(self.report_dbf_dir_input.text().strip()),
            output_dir=Path(self.output_dir_input.text().strip()),
            u2_catalog=Path(self.u2_catalog_input.text().strip()),
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
            raw_dir=Path(self.report_dbf_dir_input.text().strip()),
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
        self.generate_g1_templates_button.setEnabled(enabled)
        self.generate_g2_templates_button.setEnabled(enabled)
        self.generate_g7_templates_button.setEnabled(enabled)
        self.generate_g8_templates_button.setEnabled(enabled)
        self.generate_u2_templates_button.setEnabled(enabled)
        self.generate_g11_templates_button.setEnabled(enabled)
        self.generate_templates_button.setEnabled(enabled)
        self.export_g1_dbf_button.setEnabled(enabled)
        self.export_g2_dbf_button.setEnabled(enabled)
        self.export_g7_dbf_button.setEnabled(enabled)
        self.export_g8_dbf_button.setEnabled(enabled)
        self.export_u2_dbf_button.setEnabled(enabled)
        self.export_g11_dbf_button.setEnabled(enabled)
        self.export_dbf_button.setEnabled(enabled)
        self.validate_g1_button.setEnabled(enabled)
        self.generate_g1_button.setEnabled(enabled)
        self.validate_g2_button.setEnabled(enabled)
        self.generate_g2_button.setEnabled(enabled)
        self.validate_g7_button.setEnabled(enabled)
        self.generate_g7_button.setEnabled(enabled)
        self.validate_g8_button.setEnabled(enabled)
        self.generate_g8_button.setEnabled(enabled)
        self.validate_u2_button.setEnabled(enabled)
        self.generate_u2_button.setEnabled(enabled)
        self.validate_g11_button.setEnabled(enabled)
        self.generate_g11_button.setEnabled(enabled)
        self.clear_log_button.setEnabled(enabled)

    def _append_log(self, message: str) -> None:
        self.log_output.append(message)