from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class U2Company:
    ccodgen: str
    name: str


@dataclass(frozen=True)
class U2Location:
    ccodreg: str
    region_name: str
    ccoddep: str
    department_name: str


@dataclass(frozen=True)
class U2Ciiu:
    ccodciu: str
    description: str


@dataclass(frozen=True)
class U2Catalog:
    company: U2Company
    location: U2Location
    ciiu: tuple[U2Ciiu, ...]

    @property
    def ciiu_by_code(self) -> dict[str, U2Ciiu]:
        return {item.ccodciu: item for item in self.ciiu}


def _require_mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"La seccion '{label}' debe ser un mapa YAML.")
    return value


def _require_string(mapping: dict[str, Any], key: str, label: str) -> str:
    value = mapping.get(key)
    if value is None:
        raise ValueError(f"Falta '{key}' en '{label}'.")

    text = str(value).strip()
    if not text:
        raise ValueError(f"'{key}' en '{label}' no puede estar vacio.")

    return text


def load_u2_catalog(path: Path) -> U2Catalog:
    if not path.exists():
        raise FileNotFoundError(f"No existe el catalogo U2: {path}")

    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    root = _require_mapping(data, "root")

    company_data = _require_mapping(root.get("company"), "company")
    company = U2Company(
        ccodgen=_require_string(company_data, "ccodgen", "company"),
        name=_require_string(company_data, "name", "company"),
    )

    location_data = _require_mapping(root.get("location"), "location")
    location = U2Location(
        ccodreg=_require_string(location_data, "ccodreg", "location"),
        region_name=_require_string(location_data, "region_name", "location"),
        ccoddep=_require_string(location_data, "ccoddep", "location"),
        department_name=_require_string(location_data, "department_name", "location"),
    )

    ciiu_data = root.get("ciiu")
    if not isinstance(ciiu_data, list) or not ciiu_data:
        raise ValueError("'ciiu' debe ser una lista no vacia.")

    items: list[U2Ciiu] = []
    seen_codes: set[str] = set()

    for index, item in enumerate(ciiu_data, start=1):
        item_data = _require_mapping(item, f"ciiu[{index}]")
        code = _require_string(item_data, "ccodciu", f"ciiu[{index}]")
        description = _require_string(item_data, "description", f"ciiu[{index}]")

        if code in seen_codes:
            raise ValueError(f"Codigo CIIU duplicado en catalogo U2: {code}")

        seen_codes.add(code)
        items.append(U2Ciiu(ccodciu=code, description=description))

    return U2Catalog(company=company, location=location, ciiu=tuple(items))
