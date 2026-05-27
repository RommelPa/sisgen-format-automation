from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass(frozen=True)
class G11Company:
    ccodgen: str
    name: str


@dataclass(frozen=True)
class G11HydroUnit:
    ccodcen: str
    cnomcen: str
    cnomcue: str


@dataclass(frozen=True)
class G11ThermalFuel:
    ccodcen: str
    cnomcen: str
    ctipcom: str
    cdescom: str


@dataclass(frozen=True)
class G11Catalog:
    company: G11Company
    hydro: list[G11HydroUnit]
    thermal_fuels: list[G11ThermalFuel]


def _required_text(raw: dict[str, object], field: str, context: str) -> str:
    value = str(raw.get(field, "")).strip()

    if not value:
        raise ValueError(f"{context}: campo obligatorio vacío: {field}")

    return value


def load_g11_catalog(catalog_path: Path) -> G11Catalog:
    if not catalog_path.exists():
        raise ValueError(f"No existe el catálogo G11: {catalog_path}")

    data = yaml.safe_load(catalog_path.read_text(encoding="utf-8"))

    if not isinstance(data, dict):
        raise ValueError("El catálogo G11 debe ser un YAML con estructura de diccionario.")

    raw_company = data.get("company")

    if not isinstance(raw_company, dict):
        raise ValueError("El catálogo G11 debe contener la sección 'company'.")

    company = G11Company(
        ccodgen=_required_text(raw_company, "ccodgen", "company"),
        name=_required_text(raw_company, "name", "company"),
    )

    raw_hydro = data.get("hydro")

    if not isinstance(raw_hydro, list):
        raise ValueError("El catálogo G11 debe contener una lista 'hydro'.")

    hydro: list[G11HydroUnit] = []
    hydro_keys: set[str] = set()

    for index, raw_item in enumerate(raw_hydro, start=1):
        if not isinstance(raw_item, dict):
            raise ValueError(f"hydro #{index} no es un diccionario válido.")

        unit = G11HydroUnit(
            ccodcen=_required_text(raw_item, "ccodcen", f"hydro #{index}"),
            cnomcen=_required_text(raw_item, "cnomcen", f"hydro #{index}"),
            cnomcue=_required_text(raw_item, "cnomcue", f"hydro #{index}"),
        )

        if unit.ccodcen in hydro_keys:
            raise ValueError(f"Central hidro duplicada en catálogo G11: {unit.ccodcen}")

        hydro_keys.add(unit.ccodcen)
        hydro.append(unit)

    if not hydro:
        raise ValueError("El catálogo G11 debe contener al menos una central hidro.")

    raw_thermal = data.get("thermal_fuels")

    if not isinstance(raw_thermal, list):
        raise ValueError("El catálogo G11 debe contener una lista 'thermal_fuels'.")

    thermal_fuels: list[G11ThermalFuel] = []
    thermal_keys: set[tuple[str, str]] = set()

    for index, raw_item in enumerate(raw_thermal, start=1):
        if not isinstance(raw_item, dict):
            raise ValueError(f"thermal_fuels #{index} no es un diccionario válido.")

        fuel = G11ThermalFuel(
            ccodcen=_required_text(raw_item, "ccodcen", f"thermal_fuels #{index}"),
            cnomcen=_required_text(raw_item, "cnomcen", f"thermal_fuels #{index}"),
            ctipcom=_required_text(raw_item, "ctipcom", f"thermal_fuels #{index}"),
            cdescom=_required_text(raw_item, "cdescom", f"thermal_fuels #{index}"),
        )

        key = (fuel.ccodcen, fuel.ctipcom)

        if key in thermal_keys:
            raise ValueError(
                f"Combustible térmico duplicado en catálogo G11: "
                f"{fuel.ccodcen} / {fuel.ctipcom}"
            )

        thermal_keys.add(key)
        thermal_fuels.append(fuel)

    if not thermal_fuels:
        raise ValueError("El catálogo G11 debe contener al menos un combustible térmico.")

    return G11Catalog(
        company=company,
        hydro=hydro,
        thermal_fuels=thermal_fuels,
    )