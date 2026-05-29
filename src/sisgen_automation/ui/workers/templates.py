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

    def run(self) -> None:
        try:
            self._ensure_file(self.cenhid_catalog)
            self._ensure_file(self.center_catalog)
            self._ensure_file(self.u2_catalog)
            self._ensure_file(self.g2_catalog)
            self._ensure_file(self.g7_catalog)
            self._ensure_file(self.g8_catalog)
            self._ensure_file(self.g11_catalog)

            dacoce_path = self.raw_dir / "DACOCE.DBF"
            ciugen_path = self.raw_dir / "CIUGEN.DBF"
            vepoen_path = self.raw_dir / "VEPOEN.DBF"
            vefame_path = self.raw_dir / "VEFAME.DBF"
            self._ensure_file(dacoce_path)
            self._ensure_file(ciugen_path)
            self._ensure_file(vepoen_path)
            self._ensure_file(vefame_path)

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

            self.log.emit("Generando plantilla CIUGEN...")
            ciugen_output = create_ciugen_template(
                period=self.period,
                source_dbf_path=ciugen_path,
                catalog_path=self.u2_catalog,
                base_period=None,
                output_path=templates_dir / f"CIUGEN_{period_label}_template.xlsx",
            )
            self.log.emit(f"CIUGEN: {ciugen_output.output_path}")

            self.log.emit("Generando plantilla VEPOEN...")
            vepoen_output = create_vepoen_template(
                period=self.period,
                source_dbf_path=vepoen_path,
                catalog_path=self.g2_catalog,
                base_period=None,
                output_path=templates_dir / f"VEPOEN_{period_label}_template.xlsx",
            )
            self.log.emit(f"VEPOEN: {vepoen_output.output_path}")

            self.log.emit("Generando plantilla VEFAME...")
            vefame_output = create_vefame_template(
                period=self.period,
                source_dbf_path=vefame_path,
                catalog_path=self.g8_catalog,
                base_period=None,
                output_path=templates_dir / f"VEFAME_{period_label}_template.xlsx",
            )
            self.log.emit(f"VEFAME: {vefame_output.output_path}")

            self.log.emit("Generando plantilla COMENE...")
            comene_output = create_comene_template(
                period=self.period,
                catalog_path=self.g7_catalog,
                output_path=templates_dir / f"COMENE_{period_label}_template.xlsx",
            )
            self.log.emit(f"COMENE: {comene_output.output_path}")

            self.log.emit("Generando plantilla VENENE...")
            venene_output = create_venene_template(
                period=self.period,
                catalog_path=self.g7_catalog,
                output_path=templates_dir / f"VENENE_{period_label}_template.xlsx",
            )
            self.log.emit(f"VENENE: {venene_output.output_path}")

            self.log.emit("Generando plantilla COMNET...")
            comnet_output = create_comnet_template(
                period=self.period,
                catalog_path=self.g7_catalog,
                output_path=templates_dir / f"COMNET_{period_label}_template.xlsx",
            )
            self.log.emit(f"COMNET: {comnet_output.output_path}")

            self.log.emit("Generando plantilla TRAENE...")
            traene_output = create_traene_template(
                period=self.period,
                catalog_path=self.g7_catalog,
                output_path=templates_dir / f"TRAENE_{period_label}_template.xlsx",
            )
            self.log.emit(f"TRAENE: {traene_output.output_path}")

            self.log.emit("Generando plantilla VALENE...")
            valene_output = create_valene_template(
                period=self.period,
                catalog_path=self.g7_catalog,
                output_path=templates_dir / f"VALENE_{period_label}_template.xlsx",
            )
            self.log.emit(f"VALENE: {valene_output.output_path}")

            self.log.emit("Generando plantilla CACEHI...")
            cacehi_output = create_cacehi_template(
                period=self.period,
                catalog_path=self.g11_catalog,
                output_path=templates_dir / f"CACEHI_{period_label}_template.xlsx",
            )
            self.log.emit(f"CACEHI: {cacehi_output.output_path}")

            self.log.emit("Generando plantilla CACETE...")
            cacete_output = create_cacete_template(
                period=self.period,
                catalog_path=self.g11_catalog,
                output_path=templates_dir / f"CACETE_{period_label}_template.xlsx",
            )
            self.log.emit(f"CACETE: {cacete_output.output_path}")

            self.finished.emit(f"Plantillas generadas correctamente en: {templates_dir}")
        except Exception as error:  # noqa: BLE001
            details = traceback.format_exc()
            self.failed.emit(f"{error}\n\nDetalle técnico:\n{details}")