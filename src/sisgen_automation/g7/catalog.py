from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from sisgen_automation.catalogs.g7_repository import (
    get_g7_company,
    get_g7_system,
    list_g7_energy_parties,
    list_g7_net_commitments,
    list_g7_transfer_parties,
)


@dataclass(frozen=True)
class G7Company:
    ccodeemp: str
    name: str


@dataclass(frozen=True)
class G7System:
    ccosisi: str


@dataclass(frozen=True)
class G7EnergyParty:
    ccodgen: str
    cdesgen: str


@dataclass(frozen=True)
class G7NetCommitmentParty:
    ccoddis: str
    cnomdis: str


@dataclass(frozen=True)
class G7TransferParty:
    ccodgen: str
    cnomgen: str


@dataclass(frozen=True)
class G7Catalog:
    company: G7Company
    system: G7System
    energy_purchases: list[G7EnergyParty]
    energy_sales: list[G7EnergyParty]
    net_commitments: list[G7NetCommitmentParty]
    power_transfers: list[G7TransferParty]
    transfer_valuations: list[G7TransferParty]


def _required_text(raw: dict[str, Any], field: str, context: str) -> str:
    value = str(raw.get(field, "")).strip()

    if not value:
        raise ValueError(f"{context}: campo obligatorio vacío: {field}")

    return value


def _required_dict(data: dict[str, Any], field: str) -> dict[str, Any]:
    value = data.get(field)

    if not isinstance(value, dict):
        raise ValueError(f"El catálogo G7 debe contener la sección '{field}'.")

    return value


def _required_list(data: dict[str, Any], field: str) -> list[Any]:
    value = data.get(field)

    if not isinstance(value, list):
        raise ValueError(f"El catálogo G7 debe contener una lista '{field}'.")

    if not value:
        raise ValueError(f"La lista '{field}' no puede estar vacía.")

    return value


def _load_energy_parties(
    *,
    raw_items: list[Any],
    section: str,
) -> list[G7EnergyParty]:
    parties: list[G7EnergyParty] = []
    seen: set[str] = set()

    for index, raw_item in enumerate(raw_items, start=1):
        if not isinstance(raw_item, dict):
            raise ValueError(f"{section} #{index} no es un diccionario válido.")

        party = G7EnergyParty(
            ccodgen=_required_text(raw_item, "ccodgen", f"{section} #{index}"),
            cdesgen=_required_text(raw_item, "cdesgen", f"{section} #{index}"),
        )

        if party.ccodgen in seen:
            raise ValueError(f"CCODGEN duplicado en {section}: {party.ccodgen}")

        seen.add(party.ccodgen)
        parties.append(party)

    return parties


def _load_net_commitments(raw_items: list[Any]) -> list[G7NetCommitmentParty]:
    parties: list[G7NetCommitmentParty] = []
    seen: set[str] = set()

    for index, raw_item in enumerate(raw_items, start=1):
        if not isinstance(raw_item, dict):
            raise ValueError(f"net_commitments #{index} no es un diccionario válido.")

        party = G7NetCommitmentParty(
            ccoddis=_required_text(raw_item, "ccoddis", f"net_commitments #{index}"),
            cnomdis=_required_text(raw_item, "cnomdis", f"net_commitments #{index}"),
        )

        if party.ccoddis in seen:
            raise ValueError(f"CCODDIS duplicado en net_commitments: {party.ccoddis}")

        seen.add(party.ccoddis)
        parties.append(party)

    return parties


def _load_transfer_parties(
    *,
    raw_items: list[Any],
    section: str,
) -> list[G7TransferParty]:
    parties: list[G7TransferParty] = []
    seen: set[str] = set()

    for index, raw_item in enumerate(raw_items, start=1):
        if not isinstance(raw_item, dict):
            raise ValueError(f"{section} #{index} no es un diccionario válido.")

        party = G7TransferParty(
            ccodgen=_required_text(raw_item, "ccodgen", f"{section} #{index}"),
            cnomgen=_required_text(raw_item, "cnomgen", f"{section} #{index}"),
        )

        if party.ccodgen in seen:
            raise ValueError(f"CCODGEN duplicado en {section}: {party.ccodgen}")

        seen.add(party.ccodgen)
        parties.append(party)

    return parties


def load_g7_catalog(catalog_path: Path) -> G7Catalog:
    if not catalog_path.exists():
        raise ValueError(f"No existe el catálogo G7: {catalog_path}")

    data = yaml.safe_load(catalog_path.read_text(encoding="utf-8"))

    if not isinstance(data, dict):
        raise ValueError("El catálogo G7 debe ser un YAML con estructura de diccionario.")

    raw_company = _required_dict(data, "company")
    raw_system = _required_dict(data, "system")

    company = G7Company(
        ccodeemp=_required_text(raw_company, "ccodeemp", "company"),
        name=_required_text(raw_company, "name", "company"),
    )

    system = G7System(
        ccosisi=_required_text(raw_system, "ccosisi", "system"),
    )

    energy_purchases = _load_energy_parties(
        raw_items=_required_list(data, "energy_purchases"),
        section="energy_purchases",
    )
    energy_sales = _load_energy_parties(
        raw_items=_required_list(data, "energy_sales"),
        section="energy_sales",
    )
    net_commitments = _load_net_commitments(
        _required_list(data, "net_commitments")
    )
    power_transfers = _load_transfer_parties(
        raw_items=_required_list(data, "power_transfers"),
        section="power_transfers",
    )
    transfer_valuations = _load_transfer_parties(
        raw_items=_required_list(data, "transfer_valuations"),
        section="transfer_valuations",
    )

    return G7Catalog(
        company=company,
        system=system,
        energy_purchases=energy_purchases,
        energy_sales=energy_sales,
        net_commitments=net_commitments,
        power_transfers=power_transfers,
        transfer_valuations=transfer_valuations,
    )


def _require_non_empty_catalog_rows(rows: list[Any], section: str) -> None:
    if not rows:
        raise ValueError(f"La seccion G7 SQLite no tiene registros activos: {section}")


def load_g7_catalog_from_db(catalog_db_path: Path) -> G7Catalog:
    company_row = get_g7_company(catalog_db_path)
    system_row = get_g7_system(catalog_db_path)

    energy_purchase_rows = list_g7_energy_parties(
        catalog_db_path,
        section="energy_purchases",
        active_only=True,
        visible_only=True,
    )
    energy_sale_rows = list_g7_energy_parties(
        catalog_db_path,
        section="energy_sales",
        active_only=True,
        visible_only=True,
    )
    net_commitment_rows = list_g7_net_commitments(
        catalog_db_path,
        active_only=True,
        visible_only=True,
    )
    power_transfer_rows = list_g7_transfer_parties(
        catalog_db_path,
        section="power_transfers",
        active_only=True,
        visible_only=True,
    )
    transfer_valuation_rows = list_g7_transfer_parties(
        catalog_db_path,
        section="transfer_valuations",
        active_only=True,
        visible_only=True,
    )

    _require_non_empty_catalog_rows(energy_purchase_rows, "energy_purchases")
    _require_non_empty_catalog_rows(energy_sale_rows, "energy_sales")
    _require_non_empty_catalog_rows(net_commitment_rows, "net_commitments")
    _require_non_empty_catalog_rows(power_transfer_rows, "power_transfers")
    _require_non_empty_catalog_rows(transfer_valuation_rows, "transfer_valuations")

    return G7Catalog(
        company=G7Company(
            ccodeemp=str(company_row["ccodeemp"]),
            name=str(company_row["name"]),
        ),
        system=G7System(
            ccosisi=str(system_row["ccosisi"]),
        ),
        energy_purchases=[
            G7EnergyParty(
                ccodgen=str(row["ccodgen"]),
                cdesgen=str(row["cdesgen"]),
            )
            for row in energy_purchase_rows
        ],
        energy_sales=[
            G7EnergyParty(
                ccodgen=str(row["ccodgen"]),
                cdesgen=str(row["cdesgen"]),
            )
            for row in energy_sale_rows
        ],
        net_commitments=[
            G7NetCommitmentParty(
                ccoddis=str(row["ccoddis"]),
                cnomdis=str(row["cnomdis"]),
            )
            for row in net_commitment_rows
        ],
        power_transfers=[
            G7TransferParty(
                ccodgen=str(row["ccodgen"]),
                cnomgen=str(row["cnomgen"]),
            )
            for row in power_transfer_rows
        ],
        transfer_valuations=[
            G7TransferParty(
                ccodgen=str(row["ccodgen"]),
                cnomgen=str(row["cnomgen"]),
            )
            for row in transfer_valuation_rows
        ],
    )
