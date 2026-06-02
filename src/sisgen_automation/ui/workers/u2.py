from __future__ import annotations

import traceback
from pathlib import Path

from PySide6.QtCore import QObject, Signal

from sisgen_automation.u2.sources import validate_u2_sources
from sisgen_automation.u2.txt import create_u2_txt
from sisgen_automation.ui.workers.base import WorkerFileMixin


class U2Worker(QObject, WorkerFileMixin):
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
        u2_catalog: Path,
    ) -> None:
        super().__init__()
        self.action = action
        self.period = period
        self.raw_dir = raw_dir
        self.output_dir = output_dir
        self.u2_catalog = u2_catalog

    def run(self) -> None:
        try:
            ciugen_path = self.raw_dir / "CIUGEN.DBF"

            self._ensure_file(ciugen_path)
            self._ensure_file(self.u2_catalog)

            self.log.emit(f"Periodo: {self.period}")
            self.log.emit(f"CIUGEN: {ciugen_path}")
            self.log.emit(f"Catálogo U2: {self.u2_catalog}")
            self.log.emit("Validando fuentes U2...")

            validation = validate_u2_sources(
                ciugen_path=ciugen_path,
                period=self.period,
                catalog_path=self.u2_catalog,
            )

            self.log.emit(f"Clasificaciones CIIU: {len(validation.rows)}")
            self.log.emit(f"Clientes libres: {validation.totals.free_clients:.0f}")
            self.log.emit(f"Consumo MWh: {validation.totals.consumption_mwh:.3f}")
            self.log.emit(f"Facturación S/: {validation.totals.billing_s:.2f}")
            self.log.emit(f"Errores: {len(validation.errors)}")
            self.log.emit(f"Advertencias: {len(validation.warnings)}")

            if validation.has_errors:
                for issue in validation.errors[:20]:
                    self.log.emit(
                        f"ERROR | fila {issue.row or 'general'} | "
                        f"{issue.ciiu_code or ''} | {issue.field or ''} | "
                        f"{issue.message} | {issue.value or ''}"
                    )

                raise ValueError(
                    "Las fuentes U2 tienen errores. Revisa los logs antes de generar U2."
                )

            for issue in validation.warnings[:20]:
                self.log.emit(
                    f"WARNING | fila {issue.row or 'general'} | "
                    f"{issue.ciiu_code or ''} | {issue.field or ''} | "
                    f"{issue.message} | {issue.value or ''}"
                )

            if self.action == "validate":
                self.finished.emit("Validación U2 completada.")
                return

            self.output_dir.mkdir(parents=True, exist_ok=True)
            output_path = self.output_dir / f"U2_{self.period.replace('-', '_')}.txt"

            self.log.emit("Generando TXT U2...")

            result = create_u2_txt(
                ciugen_path=ciugen_path,
                period=self.period,
                catalog_path=self.u2_catalog,
                output_path=output_path,
            )

            self.finished.emit(f"TXT U2 generado correctamente: {result.output_path}")
        except Exception as error:  # noqa: BLE001
            details = traceback.format_exc()
            self.failed.emit(f"{error}\n\nDetalle técnico:\n{details}")
