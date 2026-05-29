from __future__ import annotations

import traceback
from pathlib import Path

from PySide6.QtCore import QObject, Signal

from sisgen_automation.g8.sources import validate_g8_sources
from sisgen_automation.g8.txt import create_g8_txt
from sisgen_automation.ui.workers.base import WorkerFileMixin


class G8Worker(QObject, WorkerFileMixin):
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
        g8_catalog: Path,
    ) -> None:
        super().__init__()
        self.action = action
        self.period = period
        self.raw_dir = raw_dir
        self.output_dir = output_dir
        self.g8_catalog = g8_catalog

    def run(self) -> None:
        try:
            vefame_path = self.raw_dir / "VEFAME.DBF"

            for path in [
                vefame_path,
                self.g8_catalog,
            ]:
                self._ensure_file(path)

            self.log.emit(f"Periodo: {self.period}")
            self.log.emit(f"VEFAME: {vefame_path}")
            self.log.emit(f"Catálogo G8: {self.g8_catalog}")
            self.log.emit("Validando fuentes G8...")

            validation = validate_g8_sources(
                vefame_path=vefame_path,
                period=self.period,
                catalog_path=self.g8_catalog,
            )

            self.log.emit(f"Clientes libres VEFAME: {len(validation.rows)}")
            self.log.emit(f"Energía total MWh: {validation.totals.active_total_mwh:.3f}")
            self.log.emit(f"Facturación total S/: {validation.totals.billing_total_s:.2f}")
            self.log.emit(
                f"Precio medio Ct.S/kWh: {validation.totals.average_price_cents_kwh:.2f}"
            )
            self.log.emit(f"Errores: {len(validation.errors)}")
            self.log.emit(f"Advertencias: {len(validation.warnings)}")

            if validation.has_errors:
                for issue in validation.errors[:20]:
                    self.log.emit(
                        f"ERROR | fila {issue.row or 'general'} | "
                        f"{issue.client_code or ''} | {issue.field or ''} | "
                        f"{issue.message} | {issue.value or ''}"
                    )

                raise ValueError(
                    "Las fuentes G8 tienen errores. Revisa los logs antes de generar G8."
                )

            for issue in validation.warnings[:20]:
                self.log.emit(
                    f"WARNING | fila {issue.row or 'general'} | "
                    f"{issue.client_code or ''} | {issue.field or ''} | "
                    f"{issue.message} | {issue.value or ''}"
                )

            if self.action == "validate":
                self.finished.emit("Validación G8 completada.")
                return

            g8_dir = self.output_dir / "g8"
            g8_dir.mkdir(parents=True, exist_ok=True)
            output_path = g8_dir / f"G8_{self.period.replace('-', '_')}.txt"

            self.log.emit("Generando TXT G8...")

            result = create_g8_txt(
                vefame_path=vefame_path,
                period=self.period,
                catalog_path=self.g8_catalog,
                output_path=output_path,
            )

            self.finished.emit(f"TXT G8 generado correctamente: {result.output_path}")
        except Exception as error:  # noqa: BLE001
            details = traceback.format_exc()
            self.failed.emit(f"{error}\n\nDetalle técnico:\n{details}")
