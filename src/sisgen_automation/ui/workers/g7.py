from __future__ import annotations

import traceback
from pathlib import Path

from PySide6.QtCore import QObject, Signal

from sisgen_automation.g7.sources import validate_g7_sources
from sisgen_automation.g7.txt import create_g7_txt
from sisgen_automation.ui.workers.base import WorkerFileMixin


class G7Worker(QObject, WorkerFileMixin):
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
        g7_catalog: Path,
    ) -> None:
        super().__init__()
        self.action = action
        self.period = period
        self.raw_dir = raw_dir
        self.output_dir = output_dir
        self.g7_catalog = g7_catalog

    def run(self) -> None:
        try:
            comene_path = self.raw_dir / "COMENE.DBF"
            venene_path = self.raw_dir / "VENENE.DBF"
            comnet_path = self.raw_dir / "COMNET.DBF"
            traene_path = self.raw_dir / "TRAENE.DBF"
            valene_path = self.raw_dir / "VALENE.DBF"

            for path in [
                comene_path,
                venene_path,
                comnet_path,
                traene_path,
                valene_path,
                self.g7_catalog,
            ]:
                self._ensure_file(path)

            self.log.emit(f"Periodo: {self.period}")
            self.log.emit(f"COMENE: {comene_path}")
            self.log.emit(f"VENENE: {venene_path}")
            self.log.emit(f"COMNET: {comnet_path}")
            self.log.emit(f"TRAENE: {traene_path}")
            self.log.emit(f"VALENE: {valene_path}")

            g7_catalog_db = Path("data/catalogs/sisgen_catalogs.db")
            if g7_catalog_db.exists():
                self.log.emit(f"Catalogo G7 SQLite: {g7_catalog_db}")
            else:
                g7_catalog_db = None
                self.log.emit(f"Catalogo G7 YAML: {self.g7_catalog}")

            self.log.emit("Validando fuentes G7...")

            validation = validate_g7_sources(
                comene_path=comene_path,
                venene_path=venene_path,
                comnet_path=comnet_path,
                traene_path=traene_path,
                valene_path=valene_path,
                period=self.period,
                catalog_path=None if g7_catalog_db is not None else self.g7_catalog,
                catalog_db_path=g7_catalog_db,
            )

            self.log.emit(f"Compras energía COMENE: {len(validation.purchases)}")
            self.log.emit(f"Ventas energía VENENE: {len(validation.sales)}")
            self.log.emit(f"Compromisos netos COMNET: {len(validation.net_commitments)}")
            self.log.emit(f"Transferencias potencia TRAENE: {len(validation.power_transfers)}")
            self.log.emit(f"Valorizaciones VALENE: {len(validation.transfer_valuations)}")
            self.log.emit(f"Errores: {len(validation.errors)}")
            self.log.emit(f"Advertencias: {len(validation.warnings)}")

            if validation.has_errors:
                for issue in validation.errors[:20]:
                    self.log.emit(
                        f"ERROR | {issue.section} | {issue.source} | "
                        f"{issue.field or ''} | {issue.message} | {issue.value or ''}"
                    )

                raise ValueError(
                    "Las fuentes G7 tienen errores. Revisa los logs antes de generar G7."
                )

            for issue in validation.warnings[:20]:
                self.log.emit(
                    f"WARNING | {issue.section} | {issue.source} | "
                    f"{issue.field or ''} | {issue.message} | {issue.value or ''}"
                )

            if self.action == "validate":
                self.finished.emit("Validación G7 completada.")
                return

            self.output_dir.mkdir(parents=True, exist_ok=True)
            output_path = self.output_dir / f"G7_{self.period.replace('-', '_')}.txt"

            self.log.emit("Generando TXT G7...")

            result = create_g7_txt(
                comene_path=comene_path,
                venene_path=venene_path,
                comnet_path=comnet_path,
                traene_path=traene_path,
                valene_path=valene_path,
                period=self.period,
                catalog_path=None if g7_catalog_db is not None else self.g7_catalog,
                catalog_db_path=g7_catalog_db,
                output_path=output_path,
            )

            self.finished.emit(f"TXT G7 generado correctamente: {result.output_path}")
        except Exception as error:  # noqa: BLE001
            details = traceback.format_exc()
            self.failed.emit(f"{error}\n\nDetalle t?cnico:\n{details}")
