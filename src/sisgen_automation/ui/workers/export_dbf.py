from __future__ import annotations

import traceback
from pathlib import Path
from typing import Callable

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


VALID_EXPORT_FORMATS = {"ALL", "G1", "G2", "G7", "G8", "U2", "G11"}


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
        templates_dir: Path,
        format_key: str = "ALL",
        cenhid_catalog: Path,
        center_catalog: Path,
        u2_catalog: Path,
        g2_catalog: Path,
        g7_catalog: Path,
        g7_catalog_db: Path | None = None,
        g8_catalog: Path,
        g11_catalog: Path,
        g1_catalog_db: Path | None = None,
        g2_catalog_db: Path | None = None,
    ) -> None:
        super().__init__()
        self.period = period
        self.raw_dir = raw_dir
        self.output_dir = output_dir
        self.templates_dir_path = templates_dir
        self.format_key = format_key.upper().strip()
        self.cenhid_catalog = cenhid_catalog
        self.center_catalog = center_catalog
        self.u2_catalog = u2_catalog
        self.g2_catalog = g2_catalog
        self.g7_catalog = g7_catalog
        self.g7_catalog_db = g7_catalog_db
        self.g8_catalog = g8_catalog
        self.g11_catalog = g11_catalog
        self.g1_catalog_db = g1_catalog_db
        self.g2_catalog_db = g2_catalog_db

    @property
    def templates_dir(self) -> Path:
        return self.templates_dir_path

    @property
    def output_dbf_dir(self) -> Path:
        return self.output_dir

    @property
    def period_label(self) -> str:
        return self.period.replace("-", "_")

    def _selected_formats(self) -> list[str]:
        if self.format_key not in VALID_EXPORT_FORMATS:
            valid = ", ".join(sorted(VALID_EXPORT_FORMATS))
            raise ValueError(f"Formato de exportacion no soportado: {self.format_key}. Validos: {valid}")

        if self.format_key == "ALL":
            return ["G1", "G2", "G7", "G8", "U2", "G11"]

        return [self.format_key]

    def _template_path(self, name: str) -> Path:
        return self.templates_dir / f"{name}_{self.period_label}_template.xlsx"

    def _source_path(self, name: str) -> Path:
        return self.raw_dir / f"{name}.DBF"

    def _log_validation(self, name: str, result: object) -> None:
        error_count = getattr(result, "error_count", None)
        if error_count is None:
            error_count = len(getattr(result, "errors", ()))

        warning_count = getattr(result, "warning_count", None)
        if warning_count is None:
            warning_count = len(getattr(result, "warnings", ()))

        self.log.emit(f"{name} validacion: errores={error_count}, advertencias={warning_count}")

    def _has_errors(self, result: object) -> bool:
        has_errors = getattr(result, "has_errors", None)

        if has_errors is not None:
            return bool(has_errors)

        return bool(getattr(result, "errors", ()))

    def _iter_issues(self, result: object) -> list[object]:
        issues = getattr(result, "issues", None)
        if issues is not None:
            return list(issues)

        errors = getattr(result, "errors", None)
        if errors is not None:
            return list(errors)

        return []

    def _is_error_issue(self, issue: object) -> bool:
        severity = getattr(issue, "severity", None)
        value = getattr(severity, "value", severity)

        if value is None:
            return True

        return str(value) == "ERROR"

    def _issue_location(self, issue: object) -> str:
        row = getattr(issue, "row", None)
        return f"fila {row}" if row is not None else "general"

    def _issue_field(self, issue: object) -> str:
        return str(getattr(issue, "field", "") or "")

    def _issue_message(self, issue: object) -> str:
        return str(getattr(issue, "message", issue))

    def _issue_value(self, issue: object) -> str:
        value = getattr(issue, "value", "")
        return "" if value is None else str(value)

    def _emit_errors(self, name: str, result: object) -> None:
        for issue in self._iter_issues(result)[:10]:
            if self._is_error_issue(issue):
                self.log.emit(
                    f"ERROR {name} | {self._issue_location(issue)} | "
                    f"{self._issue_field(issue)} | {self._issue_message(issue)} | "
                    f"{self._issue_value(issue)}"
                )

    def _validate_result(self, name: str, result: object) -> bool:
        self._log_validation(name, result)

        if self._has_errors(result):
            self._emit_errors(name, result)
            return False

        return True

    def _export_result(self, name: str, export_call: Callable[[], object]) -> str:
        self.log.emit(f"Exportando {name}.DBF...")
        result = export_call()
        output_path = getattr(result, "output_path", "")
        appended = getattr(result, "appended_record_count", "")
        self.log.emit(f"{name} exportado: {output_path} ({appended} registros nuevos)")
        return name

    def _g1_catalog_db_or_none(self) -> Path | None:
        if self.g1_catalog_db is not None and self.g1_catalog_db.exists():
            return self.g1_catalog_db

        return None

    def _validate_g1(self) -> bool:
        g1_catalog_db = self._g1_catalog_db_or_none()

        for path in [
            self._source_path("CENHID"),
            self._source_path("CENTER"),
            self._source_path("DACOCE"),
            self._source_path("COMCEN"),
            self._template_path("CENHID"),
            self._template_path("CENTER"),
            self._template_path("DACOCE"),
            self._template_path("COMCEN"),
        ]:
            self._ensure_file(path)

        if g1_catalog_db is None:
            self._ensure_file(self.cenhid_catalog)
            self._ensure_file(self.center_catalog)
        else:
            self.log.emit(f"Catalogo G1 SQLite para CENHID/CENTER/COMCEN: {g1_catalog_db}")

        results = [
            ("CENHID", validate_cenhid_template(
                template_path=self._template_path("CENHID"),
                period=self.period,
                catalog_path=None if g1_catalog_db is not None else self.cenhid_catalog,
                catalog_db_path=g1_catalog_db,
            )),
            ("CENTER", validate_center_template(
                template_path=self._template_path("CENTER"),
                period=self.period,
                catalog_path=None if g1_catalog_db is not None else self.center_catalog,
                catalog_db_path=g1_catalog_db,
            )),
            ("DACOCE", validate_dacoce_template(
                template_path=self._template_path("DACOCE"),
                period=self.period,
            )),
            ("COMCEN", validate_comcen_template(
                template_path=self._template_path("COMCEN"),
                period=self.period,
                catalog_path=None if g1_catalog_db is not None else self.center_catalog,
                catalog_db_path=g1_catalog_db,
            )),
        ]

        return all(self._validate_result(name, result) for name, result in results)

    def _export_g1(self) -> list[str]:
        exported = []
        g1_catalog_db = self._g1_catalog_db_or_none()

        exported.append(self._export_result("CENHID", lambda: export_cenhid_dbf(
            source_dbf_path=self._source_path("CENHID"),
            template_path=self._template_path("CENHID"),
            period=self.period,
            catalog_path=None if g1_catalog_db is not None else self.cenhid_catalog,
            catalog_db_path=g1_catalog_db,
            output_path=self.output_dbf_dir / "CENHID.DBF",
        )))
        exported.append(self._export_result("CENTER", lambda: export_center_dbf(
            source_dbf_path=self._source_path("CENTER"),
            template_path=self._template_path("CENTER"),
            period=self.period,
            catalog_path=None if g1_catalog_db is not None else self.center_catalog,
            catalog_db_path=g1_catalog_db,
            output_path=self.output_dbf_dir / "CENTER.DBF",
        )))
        exported.append(self._export_result("DACOCE", lambda: export_dacoce_dbf(
            source_dbf_path=self._source_path("DACOCE"),
            template_path=self._template_path("DACOCE"),
            period=self.period,
            output_path=self.output_dbf_dir / "DACOCE.DBF",
        )))
        exported.append(self._export_result("COMCEN", lambda: export_comcen_dbf(
            source_dbf_path=self._source_path("COMCEN"),
            template_path=self._template_path("COMCEN"),
            period=self.period,
            catalog_path=None if g1_catalog_db is not None else self.center_catalog,
            catalog_db_path=g1_catalog_db,
            output_path=self.output_dbf_dir / "COMCEN.DBF",
        )))

        return exported

    def _g2_catalog_db_or_none(self) -> Path | None:
        if self.g2_catalog_db is not None and self.g2_catalog_db.exists():
            return self.g2_catalog_db

        return None

    def _validate_g2(self) -> bool:
        g2_catalog_db = self._g2_catalog_db_or_none()

        for path in [
            self._source_path("VEPOEN"),
            self._template_path("VEPOEN"),
        ]:
            self._ensure_file(path)

        if g2_catalog_db is None:
            self._ensure_file(self.g2_catalog)
        else:
            self.log.emit(f"Catalogo G2 SQLite para VEPOEN: {g2_catalog_db}")

        result = validate_vepoen_template(
            template_path=self._template_path("VEPOEN"),
            period=self.period,
            catalog_path=None if g2_catalog_db is not None else self.g2_catalog,
            catalog_db_path=g2_catalog_db,
        )

        return self._validate_result("VEPOEN", result)

    def _export_g2(self) -> list[str]:
        g2_catalog_db = self._g2_catalog_db_or_none()

        return [self._export_result("VEPOEN", lambda: export_vepoen_dbf(
            source_dbf_path=self._source_path("VEPOEN"),
            template_path=self._template_path("VEPOEN"),
            period=self.period,
            catalog_path=None if g2_catalog_db is not None else self.g2_catalog,
            catalog_db_path=g2_catalog_db,
            output_path=self.output_dbf_dir / "VEPOEN.DBF",
        ))]

    def _validate_g7(self) -> bool:
        for name in ["COMENE", "VENENE", "COMNET", "TRAENE", "VALENE"]:
            self._ensure_file(self._source_path(name))
            self._ensure_file(self._template_path(name))

        g7_catalog_db = (
            self.g7_catalog_db
            if self.g7_catalog_db is not None and self.g7_catalog_db.exists()
            else None
        )
        if g7_catalog_db is not None:
            self.log.emit(f"Catalogo G7 SQLite: {g7_catalog_db}")
        else:
            self._ensure_file(self.g7_catalog)
            self.log.emit(f"Catalogo G7 YAML: {self.g7_catalog}")

        results = [
            ("COMENE", validate_comene_template(
                template_path=self._template_path("COMENE"),
                period=self.period,
                catalog_path=None if g7_catalog_db is not None else self.g7_catalog,
                catalog_db_path=g7_catalog_db,
            )),
            ("VENENE", validate_venene_template(
                template_path=self._template_path("VENENE"),
                period=self.period,
                catalog_path=None if g7_catalog_db is not None else self.g7_catalog,
                catalog_db_path=g7_catalog_db,
            )),
            ("COMNET", validate_comnet_template(
                template_path=self._template_path("COMNET"),
                period=self.period,
                catalog_path=None if g7_catalog_db is not None else self.g7_catalog,
                catalog_db_path=g7_catalog_db,
            )),
            ("TRAENE", validate_traene_template(
                template_path=self._template_path("TRAENE"),
                period=self.period,
                catalog_path=None if g7_catalog_db is not None else self.g7_catalog,
                catalog_db_path=g7_catalog_db,
            )),
            ("VALENE", validate_valene_template(
                template_path=self._template_path("VALENE"),
                period=self.period,
                catalog_path=None if g7_catalog_db is not None else self.g7_catalog,
                catalog_db_path=g7_catalog_db,
            )),
        ]

        return all(self._validate_result(name, result) for name, result in results)

    def _export_g7(self) -> list[str]:
        g7_catalog_db = (
            self.g7_catalog_db
            if self.g7_catalog_db is not None and self.g7_catalog_db.exists()
            else None
        )
        if g7_catalog_db is not None:
            self.log.emit(f"Catalogo G7 SQLite: {g7_catalog_db}")
        else:
            self._ensure_file(self.g7_catalog)
            self.log.emit(f"Catalogo G7 YAML: {self.g7_catalog}")
        exported = []

        exported.append(self._export_result("COMENE", lambda: export_comene_dbf(
            source_dbf_path=self._source_path("COMENE"),
            template_path=self._template_path("COMENE"),
            period=self.period,
            catalog_path=None if g7_catalog_db is not None else self.g7_catalog,
                catalog_db_path=g7_catalog_db,
            output_path=self.output_dbf_dir / "COMENE.DBF",
        )))
        exported.append(self._export_result("VENENE", lambda: export_venene_dbf(
            source_dbf_path=self._source_path("VENENE"),
            template_path=self._template_path("VENENE"),
            period=self.period,
            catalog_path=None if g7_catalog_db is not None else self.g7_catalog,
                catalog_db_path=g7_catalog_db,
            output_path=self.output_dbf_dir / "VENENE.DBF",
        )))
        exported.append(self._export_result("COMNET", lambda: export_comnet_dbf(
            source_dbf_path=self._source_path("COMNET"),
            template_path=self._template_path("COMNET"),
            period=self.period,
            catalog_path=None if g7_catalog_db is not None else self.g7_catalog,
                catalog_db_path=g7_catalog_db,
            output_path=self.output_dbf_dir / "COMNET.DBF",
        )))
        exported.append(self._export_result("TRAENE", lambda: export_traene_dbf(
            source_dbf_path=self._source_path("TRAENE"),
            template_path=self._template_path("TRAENE"),
            period=self.period,
            catalog_path=None if g7_catalog_db is not None else self.g7_catalog,
                catalog_db_path=g7_catalog_db,
            output_path=self.output_dbf_dir / "TRAENE.DBF",
        )))
        exported.append(self._export_result("VALENE", lambda: export_valene_dbf(
            source_dbf_path=self._source_path("VALENE"),
            template_path=self._template_path("VALENE"),
            period=self.period,
            catalog_path=None if g7_catalog_db is not None else self.g7_catalog,
                catalog_db_path=g7_catalog_db,
            output_path=self.output_dbf_dir / "VALENE.DBF",
        )))

        return exported

    def _validate_g8(self) -> bool:
        for path in [
            self._source_path("VEFAME"),
            self._template_path("VEFAME"),
            self.g8_catalog,
        ]:
            self._ensure_file(path)

        result = validate_vefame_template(
            template_path=self._template_path("VEFAME"),
            period=self.period,
            catalog_path=self.g8_catalog,
        )

        return self._validate_result("VEFAME", result)

    def _export_g8(self) -> list[str]:
        return [self._export_result("VEFAME", lambda: export_vefame_dbf(
            source_dbf_path=self._source_path("VEFAME"),
            template_path=self._template_path("VEFAME"),
            period=self.period,
            catalog_path=self.g8_catalog,
            output_path=self.output_dbf_dir / "VEFAME.DBF",
        ))]

    def _validate_u2(self) -> bool:
        for path in [
            self._source_path("CIUGEN"),
            self._template_path("CIUGEN"),
            self.u2_catalog,
        ]:
            self._ensure_file(path)

        result = validate_ciugen_template(
            template_path=self._template_path("CIUGEN"),
            period=self.period,
            catalog_path=self.u2_catalog,
        )

        return self._validate_result("CIUGEN", result)

    def _export_u2(self) -> list[str]:
        return [self._export_result("CIUGEN", lambda: export_ciugen_dbf(
            source_dbf_path=self._source_path("CIUGEN"),
            template_path=self._template_path("CIUGEN"),
            period=self.period,
            catalog_path=self.u2_catalog,
            output_path=self.output_dbf_dir / "CIUGEN.DBF",
        ))]

    def _validate_g11(self) -> bool:
        for name in ["CACEHI", "CACETE"]:
            self._ensure_file(self._source_path(name))
            self._ensure_file(self._template_path(name))

        self._ensure_file(self.g11_catalog)

        results = [
            ("CACEHI", validate_cacehi_template(
                template_path=self._template_path("CACEHI"),
                period=self.period,
                catalog_path=self.g11_catalog,
            )),
            ("CACETE", validate_cacete_template(
                template_path=self._template_path("CACETE"),
                period=self.period,
                catalog_path=self.g11_catalog,
            )),
        ]

        return all(self._validate_result(name, result) for name, result in results)

    def _export_g11(self) -> list[str]:
        exported = []

        exported.append(self._export_result("CACEHI", lambda: export_cacehi_dbf(
            source_dbf_path=self._source_path("CACEHI"),
            template_path=self._template_path("CACEHI"),
            period=self.period,
            catalog_path=self.g11_catalog,
            output_path=self.output_dbf_dir / "CACEHI.DBF",
        )))
        exported.append(self._export_result("CACETE", lambda: export_cacete_dbf(
            source_dbf_path=self._source_path("CACETE"),
            template_path=self._template_path("CACETE"),
            period=self.period,
            catalog_path=self.g11_catalog,
            output_path=self.output_dbf_dir / "CACETE.DBF",
        )))

        return exported

    def _validate_format(self, format_key: str) -> bool:
        validators = {
            "G1": self._validate_g1,
            "G2": self._validate_g2,
            "G7": self._validate_g7,
            "G8": self._validate_g8,
            "U2": self._validate_u2,
            "G11": self._validate_g11,
        }

        self.log.emit(f"Validando plantillas {format_key}...")
        return validators[format_key]()

    def _export_format(self, format_key: str) -> list[str]:
        exporters = {
            "G1": self._export_g1,
            "G2": self._export_g2,
            "G7": self._export_g7,
            "G8": self._export_g8,
            "U2": self._export_u2,
            "G11": self._export_g11,
        }

        self.log.emit(f"Exportando DBF {format_key}...")
        return exporters[format_key]()

    def run(self) -> None:
        try:
            selected_formats = self._selected_formats()

            self.log.emit(f"Periodo: {self.period}")
            self.log.emit(f"Formato: {self.format_key}")
            self.log.emit(f"Carpeta DBF historicos: {self.raw_dir}")
            self.log.emit(f"Carpeta de plantillas: {self.templates_dir}")
            self.log.emit(f"Carpeta DBF exportados: {self.output_dbf_dir}")

            has_errors = False
            for format_key in selected_formats:
                if not self._validate_format(format_key):
                    has_errors = True

            if has_errors:
                raise ValueError(
                    "Una o mas plantillas del formato seleccionado tienen errores. "
                    "No se exporto ningun DBF para este proceso."
                )

            self.output_dbf_dir.mkdir(parents=True, exist_ok=True)

            exported: list[str] = []
            for format_key in selected_formats:
                exported.extend(self._export_format(format_key))

            self.exported_dir.emit(str(self.output_dbf_dir))

            exported_text = ", ".join(exported) if exported else "ninguno"
            self.finished.emit(
                f"DBF exportados correctamente en: {self.output_dbf_dir}. "
                f"Archivos: {exported_text}"
            )
        except Exception as error:  # noqa: BLE001
            details = traceback.format_exc()
            self.failed.emit(f"{error}\\n\\nDetalle tecnico:\\n{details}")
