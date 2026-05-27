from __future__ import annotations

import traceback
from pathlib import Path

from PySide6.QtCore import QObject, Signal

from sisgen_automation.cenhid.export_dbf import export_cenhid_dbf
from sisgen_automation.cenhid.template_validation import validate_cenhid_template
from sisgen_automation.center.export_dbf import export_center_dbf
from sisgen_automation.center.template_validation import validate_center_template
from sisgen_automation.comcen.export_dbf import export_comcen_dbf
from sisgen_automation.comcen.template_validation import validate_comcen_template
from sisgen_automation.dacoce.export_dbf import export_dacoce_dbf
from sisgen_automation.dacoce.template_validation import validate_dacoce_template
from sisgen_automation.g2.export_dbf import export_vepoen_dbf
from sisgen_automation.g2.template_validation import validate_vepoen_template
from sisgen_automation.ui.workers.base import WorkerFileMixin


class ExportDbfWorker(QObject, WorkerFileMixin):
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