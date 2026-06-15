from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from sisgen_automation.catalogs.g1_repository import list_g1_units
from sisgen_automation.cenhid.catalog import CenhidUnit
from sisgen_automation.center.catalog import CenterUnit


def load_cenhid_template_catalog_from_db(
    catalog_db_path: Path,
) -> dict[tuple[str, str], CenhidUnit]:
    rows = list_g1_units(
        catalog_db_path,
        source_format="CENHID",
        active_only=True,
        visible_only=True,
    )

    if not rows:
        raise ValueError("No hay unidades CENHID activas y visibles en la base SQLite.")

    catalog: dict[tuple[str, str], CenhidUnit] = {}

    for row in rows:
        unit = CenhidUnit(
            central=str(row["central"]),
            group=str(row["cnomnum"]),
            ccodcon=str(row["ccodcon"]),
            ccodcen=str(row["ccodcen"]),
            cnomnum=str(row["cnomnum"]),
            npotins=Decimal(str(row["npotins"])),
            npotefe=Decimal(str(row["npotefe"])),
        )

        if unit.key in catalog:
            raise ValueError(
                "Catalogo SQLite CENHID duplicado para "
                f"CCODCON={unit.ccodcon}, CNOMNUM={unit.cnomnum}."
            )

        catalog[unit.key] = unit

    return catalog


def load_center_template_catalog_from_db(
    catalog_db_path: Path,
) -> dict[tuple[str, str, str], CenterUnit]:
    rows = list_g1_units(
        catalog_db_path,
        source_format="CENTER",
        active_only=True,
        visible_only=True,
    )

    if not rows:
        raise ValueError("No hay unidades CENTER activas y visibles en la base SQLite.")

    catalog: dict[tuple[str, str, str], CenterUnit] = {}

    for row in rows:
        unit = CenterUnit(
            central=str(row["central"]),
            group=str(row["cnomnum"]),
            ccodcon=str(row["ccodcon"]),
            ccodcen=str(row["ccodcen"]),
            ctipgru=str(row["ctipgru"]).upper(),
            cnomnum=str(row["cnomnum"]),
            npotins=Decimal(str(row["npotins"])),
            npotefe=Decimal(str(row["npotefe"])),
        )

        if unit.key in catalog:
            raise ValueError(
                "Catalogo SQLite CENTER duplicado para "
                f"CCODCON={unit.ccodcon}, CTIPGRU={unit.ctipgru}, "
                f"CNOMNUM={unit.cnomnum}."
            )

        catalog[unit.key] = unit

    return catalog
