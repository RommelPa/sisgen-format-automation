from __future__ import annotations

from pathlib import Path


class WorkerFileMixin:
    @staticmethod
    def _ensure_file(path: Path) -> None:
        if not path.exists():
            raise FileNotFoundError(f"No existe el archivo requerido: {path}")