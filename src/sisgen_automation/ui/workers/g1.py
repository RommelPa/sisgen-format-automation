from __future__ import annotations

import traceback
from pathlib import Path

from PySide6.QtCore import QObject, Signal

from sisgen_automation.g1.sources import validate_g1_sources
from sisgen_automation.g1.txt import create_g1_txt
from sisgen_automation.ui.workers.base import WorkerFileMixin


class G1Worker(QObject, WorkerFileMixin):
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