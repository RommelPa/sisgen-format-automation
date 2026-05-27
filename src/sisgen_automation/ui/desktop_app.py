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
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from sisgen_automation.cenhid.export_dbf import export_cenhid_dbf
from sisgen_automation.cenhid.template import create_cenhid_template
from sisgen_automation.center.export_dbf import export_center_dbf
from sisgen_automation.center.template import create_center_template
from sisgen_automation.comcen.export_dbf import export_comcen_dbf
from sisgen_automation.comcen.template import create_comcen_template
from sisgen_automation.dacoce.export_dbf import export_dacoce_dbf
from sisgen_automation.dacoce.template import create_dacoce_template
from sisgen_automation.g1.sources import validate_g1_sources
from sisgen_automation.g1.txt import create_g1_txt
from sisgen_automation.g2.sources import validate_g2_sources
from sisgen_automation.g2.txt import create_g2_txt
from sisgen_automation.g2.template import create_vepoen_template
from sisgen_automation.g2.export_dbf import export_vepoen_dbf
from sisgen_automation.cenhid.template_validation import validate_cenhid_template
from sisgen_automation.center.template_validation import validate_center_template
from sisgen_automation.dacoce.template_validation import validate_dacoce_template
from sisgen_automation.comcen.template_validation import validate_comcen_template
from sisgen_automation.g2.template_validation import validate_vepoen_template


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
            comcen_path = self.raw_dir / "COMCEN.DBF"

            self._ensure_file(cenhid_path)
            self._ensure_file(center_path)
            self._ensure_file(dacoce_path)
            self._ensure_file(comcen_path)
            self._ensure_file(self.cenhid_catalog)
            self._ensure_file(self.center_catalog)

            self.log.emit(f"Periodo: {self.period}")
            self.log.emit(f"CENHID: {cenhid_path}")
            self.log.emit(f"CENTER: {center_path}")
            self.log.emit(f"DACOCE: {dacoce_path}")
            self.log.emit(f"COMCEN: {comcen_path}")
            self.log.emit("Validando fuentes G1...")

            validation = validate_g1_sources(
                cenhid_path=cenhid_path,
                center_path=center_path,
                dacoce_path=dacoce_path,
                comcen_path=comcen_path,
                period=self.period,
                cenhid_catalog_path=self.cenhid_catalog,
                center_catalog_path=self.center_catalog,
            )

            self.log.emit(f"Grupos hidro: {validation.hydro_group_count}")
            self.log.emit(f"Centrales hidro: {len(validation.hydro_blocks)}")
            self.log.emit(f"Grupos termo: {validation.thermal_group_count}")
            self.log.emit(f"Centrales termo: {len(validation.thermal_blocks)}")
            self.log.emit(f"COMCEN termo: {validation.comcen_record_count}")
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

            g1_dir = self.output_dir / "g1"
            g1_dir.mkdir(parents=True, exist_ok=True)
            output_path = g1_dir / f"G1_{self.period.replace('-', '_')}.txt"

            self.log.emit("Generando TXT G1...")

            result = create_g1_txt(
                cenhid_path=cenhid_path,
                center_path=center_path,
                dacoce_path=dacoce_path,
                comcen_path=comcen_path,
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


class TemplateWorker(QObject):
    finished = Signal(str)
    failed = Signal(str)
    log = Signal(str)

    def __init__(
        self,
        *,
        period: str,
        raw_dir: Path,
        output_dir: Path,
        cenhid_catalog: Path,
        center_catalog: Path,
        g2_catalog: Path,
    ) -> None:
        super().__init__()
        self.period = period
        self.raw_dir = raw_dir
        self.output_dir = output_dir
        self.cenhid_catalog = cenhid_catalog
        self.center_catalog = center_catalog
        self.g2_catalog = g2_catalog

    def run(self) -> None:
        try:
            self._ensure_file(self.cenhid_catalog)
            self._ensure_file(self.center_catalog)
            self._ensure_file(self.g2_catalog)

            dacoce_path = self.raw_dir / "DACOCE.DBF"
            vepoen_path = self.raw_dir / "VEPOEN.DBF"
            self._ensure_file(dacoce_path)
            self._ensure_file(vepoen_path)

            templates_dir = self.output_dir / "templates"
            templates_dir.mkdir(parents=True, exist_ok=True)

            period_label = self.period.replace("-", "_")

            self.log.emit(f"Periodo: {self.period}")
            self.log.emit(f"Carpeta de plantillas: {templates_dir}")

            self.log.emit("Generando plantilla CENHID...")
            cenhid_output = create_cenhid_template(
                period=self.period,
                catalog_path=self.cenhid_catalog,
                output_path=templates_dir / f"CENHID_{period_label}_template.xlsx",
            )
            self.log.emit(f"CENHID: {cenhid_output}")

            self.log.emit("Generando plantilla CENTER...")
            center_output = create_center_template(
                period=self.period,
                catalog_path=self.center_catalog,
                output_path=templates_dir / f"CENTER_{period_label}_template.xlsx",
            )
            self.log.emit(f"CENTER: {center_output}")

            self.log.emit("Generando plantilla DACOCE desde catálogos locales...")
            dacoce_output = create_dacoce_template(
                period=self.period,
                source_dbf_path=dacoce_path,
                output_path=templates_dir / f"DACOCE_{period_label}_template.xlsx",
                cenhid_catalog_path=self.cenhid_catalog,
                center_catalog_path=self.center_catalog,
            )
            self.log.emit(f"DACOCE: {dacoce_output.output_path}")

            self.log.emit("Generando plantilla COMCEN...")
            comcen_output = create_comcen_template(
                period=self.period,
                catalog_path=self.center_catalog,
                output_path=templates_dir / f"COMCEN_{period_label}_template.xlsx",
            )
            self.log.emit(f"COMCEN: {comcen_output.output_path}")

            self.log.emit("Generando plantilla VEPOEN...")
            vepoen_output = create_vepoen_template(
                period=self.period,
                source_dbf_path=vepoen_path,
                catalog_path=self.g2_catalog,
                base_period=None,
                output_path=templates_dir / f"VEPOEN_{period_label}_template.xlsx",
            )
            self.log.emit(f"VEPOEN: {vepoen_output.output_path}")

            self.finished.emit(f"Plantillas generadas correctamente en: {templates_dir}")
        except Exception as error:  # noqa: BLE001
            details = traceback.format_exc()
            self.failed.emit(f"{error}\n\nDetalle técnico:\n{details}")

    @staticmethod
    def _ensure_file(path: Path) -> None:
        if not path.exists():
            raise FileNotFoundError(f"No existe el archivo requerido: {path}")


class ExportDbfWorker(QObject):
    finished = Signal(str)
    failed = Signal(str)
    log = Signal(str)
    exported_dir = Signal(str)

    def __init__(
        self,
        *,
        period: str,
        raw_dir: Path,
        output_dir: Path,
        cenhid_catalog: Path,
        center_catalog: Path,
        g2_catalog: Path,
    ) -> None:
        super().__init__()
        self.period = period
        self.raw_dir = raw_dir
        self.output_dir = output_dir
        self.cenhid_catalog = cenhid_catalog
        self.center_catalog = center_catalog
        self.g2_catalog = g2_catalog

    def _validate_all_templates(
        self,
        *,
        cenhid_template: Path,
        center_template: Path,
        dacoce_template: Path,
        comcen_template: Path,
        vepoen_template: Path,
    ) -> None:
        self.log.emit("Validando todas las plantillas antes de exportar DBF...")

        cenhid_result = validate_cenhid_template(
            template_path=cenhid_template,
            period=self.period,
            catalog_path=self.cenhid_catalog,
        )
        self.log.emit(
            f"CENHID validación: errores={len(cenhid_result.errors)}, "
            f"advertencias={len(cenhid_result.warnings)}"
        )

        center_result = validate_center_template(
            template_path=center_template,
            period=self.period,
            catalog_path=self.center_catalog,
        )
        self.log.emit(
            f"CENTER validación: errores={len(center_result.errors)}, "
            f"advertencias={len(center_result.warnings)}"
        )

        dacoce_result = validate_dacoce_template(
            template_path=dacoce_template,
            period=self.period,
        )
        self.log.emit(
            f"DACOCE validación: errores={len(dacoce_result.errors)}, "
            f"advertencias={len(dacoce_result.warnings)}"
        )

        comcen_result = validate_comcen_template(
            template_path=comcen_template,
            period=self.period,
            catalog_path=self.center_catalog,
        )
        self.log.emit(
            f"COMCEN validación: errores={comcen_result.error_count}, "
            f"advertencias={comcen_result.warning_count}"
        )

        vepoen_result = validate_vepoen_template(
            template_path=vepoen_template,
            period=self.period,
            catalog_path=self.g2_catalog,
        )
        self.log.emit(
            f"VEPOEN validación: errores={vepoen_result.error_count}, "
            f"advertencias={vepoen_result.warning_count}"
        )

        def _issue_location(issue: object) -> str:
            row = getattr(issue, "row", None)
            return f"fila {row}" if row is not None else "general"

        def _issue_field(issue: object) -> str:
            return str(getattr(issue, "field", "") or "")

        def _issue_message(issue: object) -> str:
            return str(getattr(issue, "message", issue))

        def _issue_value(issue: object) -> str:
            value = getattr(issue, "value", "")
            return "" if value is None else str(value)

        def _is_error_issue(issue: object) -> bool:
            severity = getattr(issue, "severity", None)
            value = getattr(severity, "value", severity)
            return str(value) == "ERROR"


        has_errors = (
            cenhid_result.has_errors
            or center_result.has_errors
            or dacoce_result.has_errors
            or comcen_result.has_errors
            or vepoen_result.has_errors
        )

        if not has_errors:
            self.log.emit("Todas las plantillas están listas para exportar.")
            return

        for issue in cenhid_result.errors[:10]:
            self.log.emit(
                f"ERROR CENHID | {_issue_location(issue)} | "
                f"{_issue_field(issue)} | {_issue_message(issue)} | {_issue_value(issue)}"
            )

        for issue in center_result.errors[:10]:
            self.log.emit(
                f"ERROR CENTER | {_issue_location(issue)} | "
                f"{_issue_field(issue)} | {_issue_message(issue)} | {_issue_value(issue)}"
            )

        for issue in dacoce_result.errors[:10]:
            self.log.emit(
                f"ERROR DACOCE | {_issue_location(issue)} | "
                f"{_issue_field(issue)} | {_issue_message(issue)} | {_issue_value(issue)}"
            )

        for issue in comcen_result.issues[:10]:
            if _is_error_issue(issue):
                self.log.emit(
                    f"ERROR COMCEN | {_issue_location(issue)} | "
                    f"{_issue_field(issue)} | {_issue_message(issue)} | {_issue_value(issue)}"
                )

        for issue in vepoen_result.issues[:10]:
            if _is_error_issue(issue):
                self.log.emit(
                    f"ERROR VEPOEN | {_issue_location(issue)} | "
                    f"{_issue_field(issue)} | {_issue_message(issue)} | {_issue_value(issue)}"
                )

        raise ValueError(
            "Una o más plantillas tienen errores. No se exportó ningún DBF."
        )

    def run(self) -> None:
        try:
            period_label = self.period.replace("-", "_")

            source_cenhid = self.raw_dir / "CENHID.DBF"
            source_center = self.raw_dir / "CENTER.DBF"
            source_dacoce = self.raw_dir / "DACOCE.DBF"
            source_comcen = self.raw_dir / "COMCEN.DBF"
            source_vepoen = self.raw_dir / "VEPOEN.DBF"

            templates_dir = self.output_dir / "templates"
            output_dbf_dir = self.output_dir / "dbf" / self.period

            cenhid_template = templates_dir / f"CENHID_{period_label}_template.xlsx"
            center_template = templates_dir / f"CENTER_{period_label}_template.xlsx"
            dacoce_template = templates_dir / f"DACOCE_{period_label}_template.xlsx"
            comcen_template = templates_dir / f"COMCEN_{period_label}_template.xlsx"
            vepoen_template = templates_dir / f"VEPOEN_{period_label}_template.xlsx"

            for path in [
                source_cenhid,
                source_center,
                source_dacoce,
                source_comcen,
                source_vepoen,
                cenhid_template,
                center_template,
                dacoce_template,
                comcen_template,
                vepoen_template,
                self.cenhid_catalog,
                self.center_catalog,
                self.g2_catalog,
            ]:
                self._ensure_file(path)

            self.log.emit(f"Periodo: {self.period}")
            self.log.emit(f"Carpeta de plantillas: {templates_dir}")
            self.log.emit(f"Carpeta DBF exportados: {output_dbf_dir}")

            self._validate_all_templates(
                cenhid_template=cenhid_template,
                center_template=center_template,
                dacoce_template=dacoce_template,
                comcen_template=comcen_template,
                vepoen_template=vepoen_template,
            )

            output_dbf_dir.mkdir(parents=True, exist_ok=True)

            self.log.emit("Exportando CENHID.DBF...")
            cenhid_result = export_cenhid_dbf(
                source_dbf_path=source_cenhid,
                template_path=cenhid_template,
                period=self.period,
                catalog_path=self.cenhid_catalog,
                output_path=output_dbf_dir / "CENHID.DBF",
            )
            self.log.emit(
                f"CENHID exportado: {cenhid_result.output_path} "
                f"({cenhid_result.appended_record_count} registros nuevos)"
            )

            self.log.emit("Exportando CENTER.DBF...")
            center_result = export_center_dbf(
                source_dbf_path=source_center,
                template_path=center_template,
                period=self.period,
                catalog_path=self.center_catalog,
                output_path=output_dbf_dir / "CENTER.DBF",
            )
            self.log.emit(
                f"CENTER exportado: {center_result.output_path} "
                f"({center_result.appended_record_count} registros nuevos)"
            )

            self.log.emit("Exportando DACOCE.DBF...")
            dacoce_result = export_dacoce_dbf(
                source_dbf_path=source_dacoce,
                template_path=dacoce_template,
                period=self.period,
                output_path=output_dbf_dir / "DACOCE.DBF",
            )
            self.log.emit(
                f"DACOCE exportado: {dacoce_result.output_path} "
                f"({dacoce_result.appended_record_count} registros nuevos)"
            )

            self.log.emit("Exportando COMCEN.DBF...")
            comcen_result = export_comcen_dbf(
                source_dbf_path=source_comcen,
                template_path=comcen_template,
                period=self.period,
                catalog_path=self.center_catalog,
                output_path=output_dbf_dir / "COMCEN.DBF",
            )
            self.log.emit(
                f"COMCEN exportado: {comcen_result.output_path} "
                f"({comcen_result.appended_record_count} registros nuevos)"
            )

            self.log.emit("Exportando VEPOEN.DBF...")
            vepoen_result = export_vepoen_dbf(
                source_dbf_path=source_vepoen,
                template_path=vepoen_template,
                period=self.period,
                catalog_path=self.g2_catalog,
                output_path=output_dbf_dir / "VEPOEN.DBF",
            )
            self.log.emit(
                f"VEPOEN exportado: {vepoen_result.output_path} "
                f"({vepoen_result.appended_record_count} registros nuevos)"
            )

            self.exported_dir.emit(str(output_dbf_dir))

            self.finished.emit(f"DBF exportados correctamente en: {output_dbf_dir}")
        except Exception as error:  # noqa: BLE001
            details = traceback.format_exc()
            self.failed.emit(f"{error}\n\nDetalle técnico:\n{details}")

    @staticmethod
    def _ensure_file(path: Path) -> None:
        if not path.exists():
            raise FileNotFoundError(f"No existe el archivo requerido: {path}")


class G2Worker(QObject):
    finished = Signal(str)
    failed = Signal(str)
    log = Signal(str)

    def __init__(
        self,
        *,
        action: str,
        period: str,
        vepoen_path: Path,
        output_dir: Path,
        g2_catalog: Path,
    ) -> None:
        super().__init__()
        self.action = action
        self.period = period
        self.vepoen_path = vepoen_path
        self.output_dir = output_dir
        self.g2_catalog = g2_catalog

    def run(self) -> None:
        try:
            self._ensure_file(self.vepoen_path)
            self._ensure_file(self.g2_catalog)

            self.log.emit(f"Periodo: {self.period}")
            self.log.emit(f"VEPOEN: {self.vepoen_path}")
            self.log.emit(f"Catálogo G2: {self.g2_catalog}")
            self.log.emit("Validando fuentes G2...")

            validation = validate_g2_sources(
                vepoen_path=self.vepoen_path,
                catalog_path=self.g2_catalog,
                period=self.period,
            )

            self.log.emit(f"Registros VEPOEN: {len(validation.rows)}")
            self.log.emit(f"Errores: {len(validation.errors)}")
            self.log.emit(f"Advertencias: {len(validation.warnings)}")

            if validation.has_errors:
                for issue in validation.errors[:20]:
                    self.log.emit(
                        f"ERROR | {issue.source} | {issue.field or ''} | "
                        f"{issue.message} | {issue.value or ''}"
                    )

                raise ValueError(
                    "Las fuentes G2 tienen errores. Revisa los logs antes de generar G2."
                )

            for issue in validation.warnings[:20]:
                self.log.emit(
                    f"WARNING | {issue.source} | {issue.field or ''} | "
                    f"{issue.message} | {issue.value or ''}"
                )

            if self.action == "validate":
                self.finished.emit("Validación G2 completada.")
                return

            g2_dir = self.output_dir / "g2"
            g2_dir.mkdir(parents=True, exist_ok=True)
            output_path = g2_dir / f"G2_{self.period.replace('-', '_')}.txt"

            self.log.emit("Generando TXT G2...")

            result = create_g2_txt(
                vepoen_path=self.vepoen_path,
                period=self.period,
                catalog_path=self.g2_catalog,
                output_path=output_path,
            )

            self.finished.emit(f"TXT G2 generado correctamente: {result.output_path}")
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
        self.worker: G1Worker | TemplateWorker | ExportDbfWorker | G2Worker | None = None

        self.setWindowTitle("SISGEN Format Automation")
        self.resize(1100, 760)

        self.period_input = QLineEdit("2025-12")
        self.raw_dir_input = QLineEdit(str(Path("data/raw")))
        self.output_dir_input = QLineEdit(str(Path("reports")))
        self.cenhid_catalog_input = QLineEdit(str(Path("config/local/cenhid_units.yaml")))
        self.center_catalog_input = QLineEdit(str(Path("config/local/center_units.yaml")))
        self.g2_catalog_input = QLineEdit(str(Path("config/local/g2_distributors.yaml")))

        self.validate_g1_button = QPushButton("Validar fuentes G1")
        self.generate_g1_button = QPushButton("Generar TXT G1")
        self.validate_g2_button = QPushButton("Validar fuentes G2")
        self.generate_g2_button = QPushButton("Generar TXT G2")
        self.generate_templates_button = QPushButton("Generar plantillas mensuales")
        self.export_dbf_button = QPushButton("Exportar DBF mensuales")
        self.clear_log_button = QPushButton("Limpiar logs")

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)

        self.tabs = QTabWidget()

        self._build_ui()
        self._connect_events()

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

        self.tabs.addTab(self._build_config_tab(), "Configuración")
        self.tabs.addTab(self._build_templates_tab(), "Plantillas")
        self.tabs.addTab(self._build_export_tab(), "Exportar DBF")
        self.tabs.addTab(self._build_g1_tab(), "Reporte G1")
        self.tabs.addTab(self._build_g2_tab(), "Reporte G2")
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

        help_box = QLabel(
            "El periodo configurado se usa para generar plantillas, exportar DBF y crear reportes. "
            "La carpeta DBF base debe contener CENHID.DBF, CENTER.DBF, DACOCE.DBF, COMCEN.DBF y VEPOEN.DBF. "
            "Para VEPOEN, la plantilla toma automáticamente el último periodo válido del DBF base."
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
            "Genera las plantillas Excel de CENHID, CENTER, DACOCE, COMCEN y VEPOEN usando el periodo "
            "y los catálogos configurados. Las plantillas se guardan en la carpeta de salida."
        )
        message.setWordWrap(True)

        actions_group = QGroupBox("Acciones")
        actions_layout = QHBoxLayout(actions_group)
        actions_layout.addWidget(self.generate_templates_button)
        actions_layout.addStretch()

        note = QLabel(
            "DACOCE se genera desde los catálogos CENHID y CENTER. "
            "VEPOEN se genera desde el VEPOEN.DBF base usando automáticamente el último periodo válido."
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
            "Valida las plantillas Excel llenas y genera nuevos archivos CENHID.DBF, "
            "CENTER.DBF, DACOCE.DBF, COMCEN.DBF y VEPOEN.DBF para el periodo configurado."
        )
        message.setWordWrap(True)

        actions_group = QGroupBox("Acciones")
        actions_layout = QHBoxLayout(actions_group)
        actions_layout.addWidget(self.export_dbf_button)
        actions_layout.addStretch()

        note = QLabel(
            "Las plantillas deben existir en la carpeta de salida, dentro de la subcarpeta "
            "'templates'. Los DBF exportados se guardarán en 'dbf/YYYY-MM'."
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
        self._append_log("Ahora puedes generar G1 y G2 usando los DBF exportados.")


    def _connect_events(self) -> None:
        self.validate_g1_button.clicked.connect(lambda: self._start_worker("validate"))
        self.generate_g1_button.clicked.connect(lambda: self._start_worker("generate"))
        self.validate_g2_button.clicked.connect(lambda: self._start_g2_worker("validate"))
        self.generate_g2_button.clicked.connect(lambda: self._start_g2_worker("generate"))
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
        self.clear_log_button.setEnabled(enabled)

    def _append_log(self, message: str) -> None:
        self.log_output.append(message)


# ----------------------------------------------------------------------------
# Public entry point
# ----------------------------------------------------------------------------


def run_desktop_app() -> None:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    run_desktop_app()
