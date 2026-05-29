from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class G8Company:
    ccodeemp: str
    name: str


@dataclass(frozen=True)
class G8FreeClient:
    ccoclli: str
    name: str
    cnivten: str


@dataclass(frozen=True)
class G8Catalog:
    company: G8Company
    free_clients: tuple[G8FreeClient, ...]

    @property
    def clients_by_code(self) -> dict[str, G8FreeClient]:
        return {client.ccoclli: client for client in self.free_clients}


def _require_mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"La sección '{label}' debe ser un mapa YAML.")
    return value


def _require_string(mapping: dict[str, Any], key: str, label: str) -> str:
    value = mapping.get(key)
    if value is None:
        raise ValueError(f"Falta '{key}' en '{label}'.")

    text = str(value).strip()
    if not text:
        raise ValueError(f"'{key}' en '{label}' no puede estar vacío.")

    return text


def load_g8_catalog(path: Path) -> G8Catalog:
    if not path.exists():
        raise FileNotFoundError(f"No existe el catálogo G8: {path}")

    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    root = _require_mapping(data, "root")

    company_data = _require_mapping(root.get("company"), "company")
    company = G8Company(
        ccodeemp=_require_string(company_data, "ccodeemp", "company"),
        name=_require_string(company_data, "name", "company"),
    )

    clients_data = root.get("free_clients")
    if not isinstance(clients_data, list) or not clients_data:
        raise ValueError("'free_clients' debe ser una lista no vacía.")

    clients: list[G8FreeClient] = []
    seen_codes: set[str] = set()

    for index, item in enumerate(clients_data, start=1):
        client_data = _require_mapping(item, f"free_clients[{index}]")
        ccoclli = _require_string(client_data, "ccoclli", f"free_clients[{index}]")
        name = _require_string(client_data, "name", f"free_clients[{index}]")
        cnivten = _require_string(client_data, "cnivten", f"free_clients[{index}]")

        if ccoclli in seen_codes:
            raise ValueError(f"Cliente G8 duplicado en catálogo: {ccoclli}")

        seen_codes.add(ccoclli)
        clients.append(G8FreeClient(ccoclli=ccoclli, name=name, cnivten=cnivten))

    return G8Catalog(company=company, free_clients=tuple(clients))
