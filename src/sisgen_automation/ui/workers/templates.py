from __future__ import annotations

import traceback
from pathlib import Path

from PySide6.QtCore import QObject, Signal

from sisgen_automation.cacehi.template import create_cacehi_template
from sisgen_automation.cacete.template import create_cacete_template
from sisgen_automation.cenhid.template import create_cenhid_template
from sisgen_automation.center.template import create_center_template
from sisgen_automation.ciugen.template import create_ciugen_template
from sisgen_automation.comcen.template import create_comcen_template
from sisgen_automation.comene.template import create_comene_template
from sisgen_automation.comnet.template import create_comnet_template
from sisgen_automation.dacoce.template import create_dacoce_template
from sisgen_automation.g2.template import create_vepoen_template
from sisgen_automation.vefame.template import create_vefame_template
from sisgen_automation.traene.template import create_traene_template
from sisgen_automation.valene.template import create_valene_template
from sisgen_automation.venene.template import create_venene_template
from sisgen_automation.ui.workers.base import WorkerFileMixin


VALID_TEMPLATE_FORMATS = {"ALL", "G1", "G2", "G7", "G8", "U2", "G11"}


class TemplateWorker(QObject, WorkerFileMixin):
    finished = Signal(str)
    failed = Signal(str)
    log = Signal(str)

    def __init__(
        self,
        *,
        period: str,
        raw_dir: Path,
        output_dir: Path,
        format_key: str = "ALL",
        cenhid_catalog: Path,
        center_catalog: Path,
        u2_catalog: Path,
        g2_catalog: Path,
        g7_catalog: Path,
        g8_catalog: Path,
        g11_catalog: Path,
        g1_catalog_db: Path | None = None,
        g2_catalog_db: Path | None = None,
    ) -> None:
        super().__init__()
        self.period = period
        self.raw_dir = raw_dir
        self.output_dir = output_dir
        self.format_key = format_key.upper().strip()
        self.cenhid_catalog = cenhid_catalog
        self.center_catalog = center_catalog
        self.u2_catalog = u2_catalog
        self.g2_catalog = g2_catalog
        self.g7_catalog = g7_catalog
        self.g8_catalog = g8_catalog
        self.g11_catalog = g11_catalog
        self.g1_catalog_db = g1_catalog_db
        self.g2_catalog_db = g2_catalog_db

    def _wants(self, format_key: str) -> bool:
        return self.format_key == "ALL" or self.format_key == format_key

    def _validate_format_key(self) -> None:
        if self.format_key not in VALID_TEMPLATE_FORMATS:
            valid = ", ".join(sorted(VALID_TEMPLATE_FORMATS))
            raise ValueError(f"Formato de plantilla no soportado: {self.format_key}. Válidos: {valid}")

    def run(self) -> None:
        try:
            self._validate_format_key()

            templates_dir = self.output_dir
            templates_dir.mkdir(parents=True, exist_ok=True)

            period_label = self.period.replace("-", "_")

            dacoce_path = self.raw_dir / "DACOCE.DBF"
            ciugen_path = self.raw_dir / "CIUGEN.DBF"
            vepoen_path = self.raw_dir / "VEPOEN.DBF"
            vefame_path = self.raw_dir / "VEFAME.DBF"

            self.log.emit(f"Periodo: {self.period}")
            self.log.emit(f"Formato: {self.format_key}")
            self.log.emit(f"Carpeta DBF historicos: {self.raw_dir}")
            self.log.emit(f"Carpeta de plantillas: {templates_dir}")

            generated: list[str] = []

            g1_catalog_db = None
            if self.g1_catalog_db is not None and self.g1_catalog_db.exists():
                g1_catalog_db = self.g1_catalog_db

            if self._wants("G1"):
                if g1_catalog_db is None:
                    self._ensure_file(self.cenhid_catalog)
                    self._ensure_file(self.center_catalog)
                    self._ensure_file(dacoce_path)

                self.log.emit("Generando plantillas G1...")

                if g1_catalog_db is not None:
                    self.log.emit(f"Catalogo G1 SQLite: {g1_catalog_db}")
                elif self.g1_catalog_db is not None:
                    self.log.emit(
                        "Catalogo G1 SQLite no encontrado; se usaran YAML G1."
                    )

                cenhid_output = create_cenhid_template(
                    period=self.period,
                    catalog_path=None if g1_catalog_db is not None else self.cenhid_catalog,
                    output_path=templates_dir / f"CENHID_{period_label}_template.xlsx",
                    catalog_db_path=g1_catalog_db,
                )
                self.log.emit(f"CENHID: {cenhid_output}")
                generated.append("CENHID")

                center_output = create_center_template(
                    period=self.period,
                    catalog_path=None if g1_catalog_db is not None else self.center_catalog,
                    output_path=templates_dir / f"CENTER_{period_label}_template.xlsx",
                    catalog_db_path=g1_catalog_db,
                )
                self.log.emit(f"CENTER: {center_output}")
                generated.append("CENTER")

                dacoce_output = create_dacoce_template(
                    period=self.period,
                    source_dbf_path=None if g1_catalog_db is not None else dacoce_path,
                    output_path=templates_dir / f"DACOCE_{period_label}_template.xlsx",
                    cenhid_catalog_path=None if g1_catalog_db is not None else self.cenhid_catalog,
                    center_catalog_path=None if g1_catalog_db is not None else self.center_catalog,
                    catalog_db_path=g1_catalog_db,
                )
                self.log.emit(f"DACOCE: {dacoce_output.output_path}")
                generated.append("DACOCE")

                comcen_output = create_comcen_template(
                    period=self.period,
                    catalog_path=None if g1_catalog_db is not None else self.center_catalog,
                    output_path=templates_dir / f"COMCEN_{period_label}_template.xlsx",
                    catalog_db_path=g1_catalog_db,
                )
                self.log.emit(f"COMCEN: {comcen_output.output_path}")
                generated.append("COMCEN")

            if self._wants("G2"):
                self._ensure_file(vepoen_path)

                g2_catalog_db = None
                if self.g2_catalog_db is not None and self.g2_catalog_db.exists():
                    g2_catalog_db = self.g2_catalog_db
                else:
                    self._ensure_file(self.g2_catalog)

                self.log.emit("Generando plantillas G2...")
                if g2_catalog_db is not None:
                    self.log.emit(f"Catalogo G2 SQLite: {g2_catalog_db}")
                else:
                    self.log.emit(f"Catalogo G2 YAML: {self.g2_catalog}")

                vepoen_output = create_vepoen_template(
                    period=self.period,
                    source_dbf_path=vepoen_path,
                    catalog_path=None if g2_catalog_db is not None else self.g2_catalog,
                    catalog_db_path=g2_catalog_db,
                    base_period=None,
                    output_path=templates_dir / f"VEPOEN_{period_label}_template.xlsx",
                )
                self.log.emit(f"VEPOEN: {vepoen_output.output_path}")
                generated.append("VEPOEN")

            if self._wants("G7"):
                self._ensure_file(self.g7_catalog)

                self.log.emit("Generando plantillas G7...")

                comene_output = create_comene_template(
                    period=self.period,
                    catalog_path=self.g7_catalog,
                    output_path=templates_dir / f"COMENE_{period_label}_template.xlsx",
                )
                self.log.emit(f"COMENE: {comene_output.output_path}")
                generated.append("COMENE")

                venene_output = create_venene_template(
                    period=self.period,
                    catalog_path=self.g7_catalog,
                    output_path=templates_dir / f"VENENE_{period_label}_template.xlsx",
                )
                self.log.emit(f"VENENE: {venene_output.output_path}")
                generated.append("VENENE")

                comnet_output = create_comnet_template(
                    period=self.period,
                    catalog_path=self.g7_catalog,
                    output_path=templates_dir / f"COMNET_{period_label}_template.xlsx",
                )
                self.log.emit(f"COMNET: {comnet_output.output_path}")
                generated.append("COMNET")

                traene_output = create_traene_template(
                    period=self.period,
                    catalog_path=self.g7_catalog,
                    output_path=templates_dir / f"TRAENE_{period_label}_template.xlsx",
                )
                self.log.emit(f"TRAENE: {traene_output.output_path}")
                generated.append("TRAENE")

                valene_output = create_valene_template(
                    period=self.period,
                    catalog_path=self.g7_catalog,
                    output_path=templates_dir / f"VALENE_{period_label}_template.xlsx",
                )
                self.log.emit(f"VALENE: {valene_output.output_path}")
                generated.append("VALENE")

            if self._wants("G8"):
                self._ensure_file(self.g8_catalog)
                self._ensure_file(vefame_path)

                self.log.emit("Generando plantillas G8...")

                vefame_output = create_vefame_template(
                    period=self.period,
                    source_dbf_path=vefame_path,
                    catalog_path=self.g8_catalog,
                    base_period=None,
                    output_path=templates_dir / f"VEFAME_{period_label}_template.xlsx",
                )
                self.log.emit(f"VEFAME: {vefame_output.output_path}")
                generated.append("VEFAME")

            if self._wants("U2"):
                self._ensure_file(self.u2_catalog)
                self._ensure_file(ciugen_path)

                self.log.emit("Generando plantillas U2...")

                ciugen_output = create_ciugen_template(
                    period=self.period,
                    source_dbf_path=ciugen_path,
                    catalog_path=self.u2_catalog,
                    base_period=None,
                    output_path=templates_dir / f"CIUGEN_{period_label}_template.xlsx",
                )
                self.log.emit(f"CIUGEN: {ciugen_output.output_path}")
                generated.append("CIUGEN")

            if self._wants("G11"):
                self._ensure_file(self.g11_catalog)

                self.log.emit("Generando plantillas G11...")

                cacehi_output = create_cacehi_template(
                    period=self.period,
                    catalog_path=self.g11_catalog,
                    output_path=templates_dir / f"CACEHI_{period_label}_template.xlsx",
                )
                self.log.emit(f"CACEHI: {cacehi_output.output_path}")
                generated.append("CACEHI")

                cacete_output = create_cacete_template(
                    period=self.period,
                    catalog_path=self.g11_catalog,
                    output_path=templates_dir / f"CACETE_{period_label}_template.xlsx",
                )
                self.log.emit(f"CACETE: {cacete_output.output_path}")
                generated.append("CACETE")

            generated_text = ", ".join(generated) if generated else "ninguna"
            self.finished.emit(
                f"Plantillas generadas correctamente en: {templates_dir}. "
                f"Archivos: {generated_text}"
            )
        except Exception as error:  # noqa: BLE001
            details = traceback.format_exc()
            self.failed.emit(f"{error}\n\nDetalle tecnico:\n{details}")
