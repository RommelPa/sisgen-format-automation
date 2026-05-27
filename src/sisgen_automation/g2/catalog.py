from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass(frozen=True)
class G2Distributor:
    ccoddis: str
    display_name: str


@dataclass(frozen=True)
class G2Company:
    ccodeemp: str
    name: str


@dataclass(frozen=True)
class G2Catalog:
    company: G2Company
    distributors: dict[str, G2Distributor]


def load_g2_catalog(catalog_path: Path) -> G2Catalog:
    if not catalog_path.exists():
        raise ValueError(f"No existe el catálogo G2: {catalog_path}")

    data = yaml.safe_load(catalog_path.read_text(encoding="utf-8"))

    if not isinstance(data, dict):
        raise ValueError("El catálogo G2 debe ser un YAML con estructura de diccionario.")

    raw_company = data.get("company")
    if not isinstance(raw_company, dict):
        raise ValueError("El catálogo G2 debe contener la sección 'company'.")

    company = G2Company(
        ccodeemp=str(raw_company.get("ccodeemp", "")).strip(),
        name=str(raw_company.get("name", "")).strip(),
    )

    if not company.ccodeemp or not company.name:
        raise ValueError("La sección company debe tener ccodeemp y name.")

    raw_distributors = data.get("distributors")
    if not isinstance(raw_distributors, list):
        raise ValueError("El catálogo G2 debe contener una lista 'distributors'.")

    distributors: dict[str, G2Distributor] = {}

    for index, raw_item in enumerate(raw_distributors, start=1):
        if not isinstance(raw_item, dict):
            raise ValueError(f"El distribuidor #{index} no es un diccionario válido.")

        ccoddis = str(raw_item.get("ccoddis", "")).strip()
        display_name = str(raw_item.get("display_name", "")).strip()

        if not ccoddis or not display_name:
            raise ValueError(f"El distribuidor #{index} debe tener ccoddis y display_name.")

        if ccoddis in distributors:
            raise ValueError(f"Distribuidor duplicado en catálogo G2: {ccoddis}")

        distributors[ccoddis] = G2Distributor(
            ccoddis=ccoddis,
            display_name=display_name,
        )

    if not distributors:
        raise ValueError("El catálogo G2 no contiene distribuidores.")

    return G2Catalog(company=company, distributors=distributors)