from __future__ import annotations

import traceback
from pathlib import Path

from PySide6.QtCore import QObject, Signal

from sisgen_automation.cenhid.template import create_cenhid_template
from sisgen_automation.center.template import create_center_template
from sisgen_automation.comcen.template import create_comcen_template
from sisgen_automation.dacoce.template import create_dacoce_template
from sisgen_automation.g2.template import create_vepoen_template
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