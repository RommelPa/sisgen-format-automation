from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class CenterUnit:
    central: str
    group: str
    ccodcon: str
    ccodcen: str
    ctipgru: str
    cnomnum: str
    npotins: Decimal
    npotefe: Decimal

    @property
    def key(self) -> tuple[str, str, str]:
        return (self.ccodcon, self.ctipgru, self.cnomnum)


def _read_text(item: dict[str, Any], field: str) -> str:
    value = item.get(field)

    if value is None:
        raise ValueError(f"Falta el campo obligatorio '{field}' en el catálogo CENTER.")

    text = str(value).strip()

    if not text:
        raise ValueError(f"El campo '{field}' del catálogo CENTER está vacío.")

    return text


def _read_decimal(item: dict[str, Any], field: str) -> Decimal:
    value = _read_text(item, field)

    try:
        return Decimal(value)
    except InvalidOperation as error:
        raise ValueError(
            f"El campo '{field}' del catálogo CENTER no es numérico válido: {value}"
        ) from error


def load_center_catalog(path: Path) -> dict[tuple[str, str, str], CenterUnit]:
    if not path.exists():
        raise FileNotFoundError(f"No existe el catálogo CENTER: {path}")

    raw_data = yaml.safe_load(path.read_text(encoding="utf-8"))

    if not isinstance(raw_data, dict):
        raise ValueError("El catálogo CENTER debe ser un YAML con estructura de diccionario.")

    raw_units = raw_data.get("units")

    if not isinstance(raw_units, list):
        raise ValueError("El catálogo CENTER debe tener una lista llamada 'units'.")

    catalog: dict[tuple[str, str, str], CenterUnit] = {}

    for index, raw_unit in enumerate(raw_units, start=1):
        if not isinstance(raw_unit, dict):
            raise ValueError(f"La unidad #{index} del catálogo CENTER no es válida.")

        unit = CenterUnit(
            central=_read_text(raw_unit, "central"),
            group=_read_text(raw_unit, "cnomnum"),
            ccodcon=_read_text(raw_unit, "ccodcon"),
            ccodcen=_read_text(raw_unit, "ccodcen"),
            ctipgru=_read_text(raw_unit, "ctipgru").upper(),
            cnomnum=_read_text(raw_unit, "cnomnum"),
            npotins=_read_decimal(raw_unit, "npotins"),
            npotefe=_read_decimal(raw_unit, "npotefe"),
        )

        if unit.key in catalog:
            raise ValueError(
                "Catálogo CENTER duplicado para "
                f"CCODCON={unit.ccodcon}, CTIPGRU={unit.ctipgru}, CNOMNUM={unit.cnomnum}."
            )

        catalog[unit.key] = unit

    if not catalog:
        raise ValueError("El catálogo CENTER no contiene unidades.")

    return catalog