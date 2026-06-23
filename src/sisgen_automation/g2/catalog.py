from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from sisgen_automation.catalogs.g2_repository import (
    get_g2_company,
    list_g2_distributors,
)


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


def load_g2_catalog_from_db(catalog_db_path: Path) -> G2Catalog:
    company_row = get_g2_company(catalog_db_path)
    distributor_rows = list_g2_distributors(
        catalog_db_path,
        active_only=True,
        visible_only=True,
    )

    company = G2Company(
        ccodeemp=str(company_row["ccodeemp"]).strip(),
        name=str(company_row["name"]).strip(),
    )

    if not company.ccodeemp or not company.name:
        raise ValueError("La empresa G2 SQLite debe tener ccodeemp y name.")

    distributors: dict[str, G2Distributor] = {}

    for row in distributor_rows:
        ccoddis = str(row["ccoddis"]).strip()
        display_name = str(row["display_name"]).strip()

        if not ccoddis or not display_name:
            raise ValueError("Distribuidor G2 SQLite con ccoddis o display_name vacio.")

        if ccoddis in distributors:
            raise ValueError(f"Distribuidor duplicado en catalogo SQLite G2: {ccoddis}")

        distributors[ccoddis] = G2Distributor(
            ccoddis=ccoddis,
            display_name=display_name,
        )

    if not distributors:
        raise ValueError("No hay distribuidores G2 activos y visibles en la base SQLite.")

    return G2Catalog(company=company, distributors=distributors)
