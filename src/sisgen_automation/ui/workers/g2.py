from __future__ import annotations

import traceback
from pathlib import Path

from PySide6.QtCore import QObject, Signal

from sisgen_automation.g2.sources import validate_g2_sources
from sisgen_automation.g2.txt import create_g2_txt
from sisgen_automation.ui.workers.base import WorkerFileMixin


class G2Worker(QObject, WorkerFileMixin):
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

            self.output_dir.mkdir(parents=True, exist_ok=True)
            output_path = self.output_dir / f"G2_{self.period.replace('-', '_')}.txt"

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