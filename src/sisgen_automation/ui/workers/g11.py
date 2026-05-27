from __future__ import annotations

import traceback
from pathlib import Path

from PySide6.QtCore import QObject, Signal

from sisgen_automation.g11.sources import validate_g11_sources
from sisgen_automation.g11.txt import create_g11_txt
from sisgen_automation.ui.workers.base import WorkerFileMixin


class G11Worker(QObject, WorkerFileMixin):
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
        g11_catalog: Path,
    ) -> None:
        super().__init__()
        self.action = action
        self.period = period
        self.raw_dir = raw_dir
        self.output_dir = output_dir
        self.g11_catalog = g11_catalog

    def run(self) -> None:
        try:
            cacehi_path = self.raw_dir / "CACEHI.DBF"
            cacete_path = self.raw_dir / "CACETE.DBF"

            self._ensure_file(cacehi_path)
            self._ensure_file(cacete_path)
            self._ensure_file(self.g11_catalog)

            self.log.emit(f"Periodo: {self.period}")
            self.log.emit(f"CACEHI: {cacehi_path}")
            self.log.emit(f"CACETE: {cacete_path}")
            self.log.emit(f"Catálogo G11: {self.g11_catalog}")
            self.log.emit("Validando fuentes G11...")

            validation = validate_g11_sources(
                cacehi_path=cacehi_path,
                cacete_path=cacete_path,
                period=self.period,
                catalog_path=self.g11_catalog,
            )

            self.log.emit(f"Registros hidro CACEHI: {len(validation.hydro_rows)}")
            self.log.emit(f"Registros térmicos CACETE: {len(validation.thermal_rows)}")
            self.log.emit(f"Errores: {len(validation.errors)}")
            self.log.emit(f"Advertencias: {len(validation.warnings)}")

            if validation.has_errors:
                for issue in validation.errors[:20]:
                    self.log.emit(
                        f"ERROR | {issue.section} | {issue.source} | "
                        f"{issue.field or ''} | {issue.message} | {issue.value or ''}"
                    )

                raise ValueError(
                    "Las fuentes G11 tienen errores. Revisa los logs antes de generar G11."
                )

            for issue in validation.warnings[:20]:
                self.log.emit(
                    f"WARNING | {issue.section} | {issue.source} | "
                    f"{issue.field or ''} | {issue.message} | {issue.value or ''}"
                )

            if self.action == "validate":
                self.finished.emit("Validación G11 completada.")
                return

            g11_dir = self.output_dir / "g11"
            g11_dir.mkdir(parents=True, exist_ok=True)
            output_path = g11_dir / f"G11_{self.period.replace('-', '_')}.txt"

            self.log.emit("Generando TXT G11...")

            result = create_g11_txt(
                cacehi_path=cacehi_path,
                cacete_path=cacete_path,
                period=self.period,
                catalog_path=self.g11_catalog,
                output_path=output_path,
            )

            self.finished.emit(f"TXT G11 generado correctamente: {result.output_path}")
        except Exception as error:  # noqa: BLE001
            details = traceback.format_exc()
            self.failed.emit(f"{error}\n\nDetalle técnico:\n{details}")