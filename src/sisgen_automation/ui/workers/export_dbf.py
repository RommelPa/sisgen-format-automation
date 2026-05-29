from __future__ import annotations

import traceback
from pathlib import Path

from PySide6.QtCore import QObject, Signal

from sisgen_automation.cacehi.export_dbf import export_cacehi_dbf
from sisgen_automation.cacehi.template_validation import validate_cacehi_template
from sisgen_automation.cacete.export_dbf import export_cacete_dbf
from sisgen_automation.cacete.template_validation import validate_cacete_template
from sisgen_automation.cenhid.export_dbf import export_cenhid_dbf
from sisgen_automation.cenhid.template_validation import validate_cenhid_template
from sisgen_automation.center.export_dbf import export_center_dbf
from sisgen_automation.center.template_validation import validate_center_template
from sisgen_automation.ciugen.export_dbf import export_ciugen_dbf
from sisgen_automation.ciugen.template_validation import validate_ciugen_template
from sisgen_automation.comcen.export_dbf import export_comcen_dbf
from sisgen_automation.comcen.template_validation import validate_comcen_template
from sisgen_automation.comene.export_dbf import export_comene_dbf
from sisgen_automation.comene.template_validation import validate_comene_template
from sisgen_automation.comnet.export_dbf import export_comnet_dbf
from sisgen_automation.comnet.template_validation import validate_comnet_template
from sisgen_automation.dacoce.export_dbf import export_dacoce_dbf
from sisgen_automation.dacoce.template_validation import validate_dacoce_template
from sisgen_automation.g2.export_dbf import export_vepoen_dbf
from sisgen_automation.g2.template_validation import validate_vepoen_template
from sisgen_automation.vefame.export_dbf import export_vefame_dbf
from sisgen_automation.vefame.template_validation import validate_vefame_template
from sisgen_automation.traene.export_dbf import export_traene_dbf
from sisgen_automation.traene.template_validation import validate_traene_template
from sisgen_automation.valene.export_dbf import export_valene_dbf
from sisgen_automation.valene.template_validation import validate_valene_template
from sisgen_automation.venene.export_dbf import export_venene_dbf
from sisgen_automation.venene.template_validation import validate_venene_template
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
        u2_catalog: Path,
        g2_catalog: Path,
        g7_catalog: Path,
        g8_catalog: Path,
        g11_catalog: Path,
    ) -> None:
        super().__init__()
        self.period = period
        self.raw_dir = raw_dir
        self.output_dir = output_dir
        self.cenhid_catalog = cenhid_catalog
        self.center_catalog = center_catalog
        self.u2_catalog = u2_catalog
        self.g2_catalog = g2_catalog
        self.g7_catalog = g7_catalog
        self.g8_catalog = g8_catalog
        self.g11_catalog = g11_catalog

    def _validate_all_templates(
        self,
        *,
        cenhid_template: Path,
        center_template: Path,
        dacoce_template: Path,
        comcen_template: Path,
        ciugen_template: Path,
        vepoen_template: Path,
        vefame_template: Path,
        comene_template: Path,
        venene_template: Path,
        comnet_template: Path,
        traene_template: Path,
        valene_template: Path,
        cacehi_template: Path,
        cacete_template: Path,
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

        ciugen_result = validate_ciugen_template(
            template_path=ciugen_template,
            period=self.period,
            catalog_path=self.u2_catalog,
        )
        self.log.emit(
            f"CIUGEN validación: errores={ciugen_result.error_count}, "
            f"advertencias={ciugen_result.warning_count}"
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

        vefame_result = validate_vefame_template(
            template_path=vefame_template,
            period=self.period,
            catalog_path=self.g8_catalog,
        )
        self.log.emit(
            f"VEFAME validación: errores={vefame_result.error_count}, "
            f"advertencias={vefame_result.warning_count}"
        )

        comene_result = validate_comene_template(
            template_path=comene_template,
            period=self.period,
            catalog_path=self.g7_catalog,
        )
        self.log.emit(
            f"COMENE validación: errores={comene_result.error_count}, "
            f"advertencias={comene_result.warning_count}"
        )

        venene_result = validate_venene_template(
            template_path=venene_template,
            period=self.period,
            catalog_path=self.g7_catalog,
        )
        self.log.emit(
            f"VENENE validación: errores={venene_result.error_count}, "
            f"advertencias={venene_result.warning_count}"
        )

        comnet_result = validate_comnet_template(
            template_path=comnet_template,
            period=self.period,
            catalog_path=self.g7_catalog,
        )
        self.log.emit(
            f"COMNET validación: errores={comnet_result.error_count}, "
            f"advertencias={comnet_result.warning_count}"
        )

        traene_result = validate_traene_template(
            template_path=traene_template,
            period=self.period,
            catalog_path=self.g7_catalog,
        )
        self.log.emit(
            f"TRAENE validación: errores={traene_result.error_count}, "
            f"advertencias={traene_result.warning_count}"
        )

        valene_result = validate_valene_template(
            template_path=valene_template,
            period=self.period,
            catalog_path=self.g7_catalog,
        )
        self.log.emit(
            f"VALENE validación: errores={valene_result.error_count}, "
            f"advertencias={valene_result.warning_count}"
        )

        cacehi_result = validate_cacehi_template(
            template_path=cacehi_template,
            period=self.period,
            catalog_path=self.g11_catalog,
        )
        self.log.emit(
            f"CACEHI validación: errores={cacehi_result.error_count}, "
            f"advertencias={cacehi_result.warning_count}"
        )

        cacete_result = validate_cacete_template(
            template_path=cacete_template,
            period=self.period,
            catalog_path=self.g11_catalog,
        )
        self.log.emit(
            f"CACETE validación: errores={cacete_result.error_count}, "
            f"advertencias={cacete_result.warning_count}"
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
            or ciugen_result.has_errors
            or vepoen_result.has_errors
            or vefame_result.has_errors
            or comene_result.has_errors
            or venene_result.has_errors
            or comnet_result.has_errors
            or traene_result.has_errors
            or valene_result.has_errors
            or cacehi_result.has_errors
            or cacete_result.has_errors
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

        for issue in ciugen_result.issues[:10]:
            if _is_error_issue(issue):
                self.log.emit(
                    f"ERROR CIUGEN | {_issue_location(issue)} | "
                    f"{_issue_field(issue)} | {_issue_message(issue)} | {_issue_value(issue)}"
                )

        for issue in vepoen_result.issues[:10]:
            if _is_error_issue(issue):
                self.log.emit(
                    f"ERROR VEPOEN | {_issue_location(issue)} | "
                    f"{_issue_field(issue)} | {_issue_message(issue)} | {_issue_value(issue)}"
                )

        for issue in vefame_result.issues[:10]:
            if _is_error_issue(issue):
                self.log.emit(
                    f"ERROR VEFAME | {_issue_location(issue)} | "
                    f"{_issue_field(issue)} | {_issue_message(issue)} | {_issue_value(issue)}"
                )

        for issue in comene_result.issues[:10]:
            if _is_error_issue(issue):
                self.log.emit(
                    f"ERROR COMENE | {_issue_location(issue)} | "
                    f"{_issue_field(issue)} | {_issue_message(issue)} | {_issue_value(issue)}"
                )

        for issue in venene_result.issues[:10]:
            if _is_error_issue(issue):
                self.log.emit(
                    f"ERROR VENENE | {_issue_location(issue)} | "
                    f"{_issue_field(issue)} | {_issue_message(issue)} | {_issue_value(issue)}"
                )

        for issue in comnet_result.issues[:10]:
            if _is_error_issue(issue):
                self.log.emit(
                    f"ERROR COMNET | {_issue_location(issue)} | "
                    f"{_issue_field(issue)} | {_issue_message(issue)} | {_issue_value(issue)}"
                )

        for issue in traene_result.issues[:10]:
            if _is_error_issue(issue):
                self.log.emit(
                    f"ERROR TRAENE | {_issue_location(issue)} | "
                    f"{_issue_field(issue)} | {_issue_message(issue)} | {_issue_value(issue)}"
                )

        for issue in valene_result.issues[:10]:
            if _is_error_issue(issue):
                self.log.emit(
                    f"ERROR VALENE | {_issue_location(issue)} | "
                    f"{_issue_field(issue)} | {_issue_message(issue)} | {_issue_value(issue)}"
                )

        for issue in cacehi_result.issues[:10]:
            if _is_error_issue(issue):
                self.log.emit(
                    f"ERROR CACEHI | {_issue_location(issue)} | "
                    f"{_issue_field(issue)} | {_issue_message(issue)} | {_issue_value(issue)}"
                )

        for issue in cacete_result.issues[:10]:
            if _is_error_issue(issue):
                self.log.emit(
                    f"ERROR CACETE | {_issue_location(issue)} | "
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
            source_ciugen = self.raw_dir / "CIUGEN.DBF"
            source_vepoen = self.raw_dir / "VEPOEN.DBF"
            source_vefame = self.raw_dir / "VEFAME.DBF"
            source_comene = self.raw_dir / "COMENE.DBF"
            source_venene = self.raw_dir / "VENENE.DBF"
            source_comnet = self.raw_dir / "COMNET.DBF"
            source_traene = self.raw_dir / "TRAENE.DBF"
            source_valene = self.raw_dir / "VALENE.DBF"
            source_cacehi = self.raw_dir / "CACEHI.DBF"
            source_cacete = self.raw_dir / "CACETE.DBF"

            templates_dir = self.output_dir / "templates"
            output_dbf_dir = self.output_dir / "dbf" / self.period

            cenhid_template = templates_dir / f"CENHID_{period_label}_template.xlsx"
            center_template = templates_dir / f"CENTER_{period_label}_template.xlsx"
            dacoce_template = templates_dir / f"DACOCE_{period_label}_template.xlsx"
            comcen_template = templates_dir / f"COMCEN_{period_label}_template.xlsx"
            ciugen_template = templates_dir / f"CIUGEN_{period_label}_template.xlsx"
            vepoen_template = templates_dir / f"VEPOEN_{period_label}_template.xlsx"
            vefame_template = templates_dir / f"VEFAME_{period_label}_template.xlsx"
            comene_template = templates_dir / f"COMENE_{period_label}_template.xlsx"
            venene_template = templates_dir / f"VENENE_{period_label}_template.xlsx"
            comnet_template = templates_dir / f"COMNET_{period_label}_template.xlsx"
            traene_template = templates_dir / f"TRAENE_{period_label}_template.xlsx"
            valene_template = templates_dir / f"VALENE_{period_label}_template.xlsx"
            cacehi_template = templates_dir / f"CACEHI_{period_label}_template.xlsx"
            cacete_template = templates_dir / f"CACETE_{period_label}_template.xlsx"

            for path in [
                source_cenhid,
                source_center,
                source_dacoce,
                source_comcen,
                source_ciugen,
                source_vepoen,
                source_vefame,
                source_comene,
                source_venene,
                source_comnet,
                source_traene,
                source_valene,
                source_cacehi,
                source_cacete,
                cenhid_template,
                center_template,
                dacoce_template,
                comcen_template,
                ciugen_template,
                vepoen_template,
                vefame_template,
                comene_template,
                venene_template,
                comnet_template,
                traene_template,
                valene_template,
                cacehi_template,
                cacete_template,
                self.cenhid_catalog,
                self.center_catalog,
                self.u2_catalog,
                self.g2_catalog,
                self.g7_catalog,
                self.g8_catalog,
                self.g11_catalog,
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
                ciugen_template=ciugen_template,
                vepoen_template=vepoen_template,
                vefame_template=vefame_template,
                comene_template=comene_template,
                venene_template=venene_template,
                comnet_template=comnet_template,
                traene_template=traene_template,
                valene_template=valene_template,
                cacehi_template=cacehi_template,
                cacete_template=cacete_template,
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

            self.log.emit("Exportando CIUGEN.DBF...")
            ciugen_result = export_ciugen_dbf(
                source_dbf_path=source_ciugen,
                template_path=ciugen_template,
                period=self.period,
                catalog_path=self.u2_catalog,
                output_path=output_dbf_dir / "CIUGEN.DBF",
            )
            self.log.emit(
                f"CIUGEN exportado: {ciugen_result.output_path} "
                f"({ciugen_result.appended_record_count} registros nuevos)"
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

            self.log.emit("Exportando VEFAME.DBF...")
            vefame_result = export_vefame_dbf(
                source_dbf_path=source_vefame,
                template_path=vefame_template,
                period=self.period,
                catalog_path=self.g8_catalog,
                output_path=output_dbf_dir / "VEFAME.DBF",
            )
            self.log.emit(
                f"VEFAME exportado: {vefame_result.output_path} "
                f"({vefame_result.appended_record_count} registros nuevos)"
            )

            self.log.emit("Exportando COMENE.DBF...")
            comene_result = export_comene_dbf(
                source_dbf_path=source_comene,
                template_path=comene_template,
                period=self.period,
                catalog_path=self.g7_catalog,
                output_path=output_dbf_dir / "COMENE.DBF",
            )
            self.log.emit(
                f"COMENE exportado: {comene_result.output_path} "
                f"({comene_result.appended_record_count} registros nuevos)"
            )

            self.log.emit("Exportando VENENE.DBF...")
            venene_result = export_venene_dbf(
                source_dbf_path=source_venene,
                template_path=venene_template,
                period=self.period,
                catalog_path=self.g7_catalog,
                output_path=output_dbf_dir / "VENENE.DBF",
            )
            self.log.emit(
                f"VENENE exportado: {venene_result.output_path} "
                f"({venene_result.appended_record_count} registros nuevos)"
            )

            self.log.emit("Exportando COMNET.DBF...")
            comnet_result = export_comnet_dbf(
                source_dbf_path=source_comnet,
                template_path=comnet_template,
                period=self.period,
                catalog_path=self.g7_catalog,
                output_path=output_dbf_dir / "COMNET.DBF",
            )
            self.log.emit(
                f"COMNET exportado: {comnet_result.output_path} "
                f"({comnet_result.appended_record_count} registros nuevos)"
            )

            self.log.emit("Exportando TRAENE.DBF...")
            traene_result = export_traene_dbf(
                source_dbf_path=source_traene,
                template_path=traene_template,
                period=self.period,
                catalog_path=self.g7_catalog,
                output_path=output_dbf_dir / "TRAENE.DBF",
            )
            self.log.emit(
                f"TRAENE exportado: {traene_result.output_path} "
                f"({traene_result.appended_record_count} registros nuevos)"
            )

            self.log.emit("Exportando VALENE.DBF...")
            valene_result = export_valene_dbf(
                source_dbf_path=source_valene,
                template_path=valene_template,
                period=self.period,
                catalog_path=self.g7_catalog,
                output_path=output_dbf_dir / "VALENE.DBF",
            )
            self.log.emit(
                f"VALENE exportado: {valene_result.output_path} "
                f"({valene_result.appended_record_count} registros nuevos)"
            )

            self.log.emit("Exportando CACEHI.DBF...")
            cacehi_result = export_cacehi_dbf(
                source_dbf_path=source_cacehi,
                template_path=cacehi_template,
                period=self.period,
                catalog_path=self.g11_catalog,
                output_path=output_dbf_dir / "CACEHI.DBF",
            )
            self.log.emit(
                f"CACEHI exportado: {cacehi_result.output_path} "
                f"({cacehi_result.appended_record_count} registros nuevos)"
            )

            self.log.emit("Exportando CACETE.DBF...")
            cacete_result = export_cacete_dbf(
                source_dbf_path=source_cacete,
                template_path=cacete_template,
                period=self.period,
                catalog_path=self.g11_catalog,
                output_path=output_dbf_dir / "CACETE.DBF",
            )
            self.log.emit(
                f"CACETE exportado: {cacete_result.output_path} "
                f"({cacete_result.appended_record_count} registros nuevos)"
            )

            self.exported_dir.emit(str(output_dbf_dir))

            self.finished.emit(f"DBF exportados correctamente en: {output_dbf_dir}")
        except Exception as error:  # noqa: BLE001
            details = traceback.format_exc()
            self.failed.emit(f"{error}\n\nDetalle técnico:\n{details}")