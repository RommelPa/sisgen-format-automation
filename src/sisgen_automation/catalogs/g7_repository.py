from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any


SCHEMA = """
CREATE TABLE IF NOT EXISTS catalog_g7_company (
    id INTEGER PRIMARY KEY CHECK (id = 1),

    ccodeemp TEXT NOT NULL,
    name TEXT NOT NULL,

    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS catalog_g7_system (
    id INTEGER PRIMARY KEY CHECK (id = 1),

    ccosisi TEXT NOT NULL,

    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS catalog_g7_energy_parties (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    section TEXT NOT NULL,
    ccodgen TEXT NOT NULL,
    cdesgen TEXT NOT NULL,

    active INTEGER NOT NULL DEFAULT 1,
    visible_in_txt INTEGER NOT NULL DEFAULT 1,

    notes TEXT,

    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(section, ccodgen)
);

CREATE TABLE IF NOT EXISTS catalog_g7_net_commitments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    ccoddis TEXT NOT NULL UNIQUE,
    cnomdis TEXT NOT NULL,

    active INTEGER NOT NULL DEFAULT 1,
    visible_in_txt INTEGER NOT NULL DEFAULT 1,

    notes TEXT,

    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS catalog_g7_transfer_parties (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    section TEXT NOT NULL,
    ccodgen TEXT NOT NULL,
    cnomgen TEXT NOT NULL,

    active INTEGER NOT NULL DEFAULT 1,
    visible_in_txt INTEGER NOT NULL DEFAULT 1,

    notes TEXT,

    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(section, ccodgen)
);

CREATE TABLE IF NOT EXISTS catalog_migration_audit (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    source_type TEXT NOT NULL,
    source_name TEXT NOT NULL,
    source_path TEXT NOT NULL,

    inserted_count INTEGER NOT NULL DEFAULT 0,
    updated_count INTEGER NOT NULL DEFAULT 0,
    skipped_count INTEGER NOT NULL DEFAULT 0,

    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    notes TEXT
);
"""


def ensure_g7_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    conn.commit()


def get_g7_company(db_path: Path) -> dict[str, Any]:
    if not db_path.exists():
        raise FileNotFoundError(db_path)

    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            """
            SELECT ccodeemp, name
            FROM catalog_g7_company
            WHERE id = 1
            """
        ).fetchone()

    if row is None:
        raise ValueError("No existe empresa G7 en la base SQLite.")

    return dict(row)


def get_g7_system(db_path: Path) -> dict[str, Any]:
    if not db_path.exists():
        raise FileNotFoundError(db_path)

    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            """
            SELECT ccosisi
            FROM catalog_g7_system
            WHERE id = 1
            """
        ).fetchone()

    if row is None:
        raise ValueError("No existe sistema G7 en la base SQLite.")

    return dict(row)


def list_g7_energy_parties(
    db_path: Path,
    *,
    section: str | None = None,
    active_only: bool = False,
    visible_only: bool = False,
) -> list[dict[str, Any]]:
    if not db_path.exists():
        raise FileNotFoundError(db_path)

    conditions: list[str] = []
    params: list[Any] = []

    if section is not None:
        conditions.append("section = ?")
        params.append(section)

    if active_only:
        conditions.append("active = 1")

    if visible_only:
        conditions.append("visible_in_txt = 1")

    where_clause = ""
    if conditions:
        where_clause = "WHERE " + " AND ".join(conditions)

    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            f"""
            SELECT
                id,
                section,
                ccodgen,
                cdesgen,
                active,
                visible_in_txt,
                notes
            FROM catalog_g7_energy_parties
            {where_clause}
            ORDER BY section, ccodgen
            """,
            params,
        ).fetchall()

    return [dict(row) for row in rows]


def list_g7_net_commitments(
    db_path: Path,
    *,
    active_only: bool = False,
    visible_only: bool = False,
) -> list[dict[str, Any]]:
    if not db_path.exists():
        raise FileNotFoundError(db_path)

    conditions: list[str] = []
    params: list[Any] = []

    if active_only:
        conditions.append("active = 1")

    if visible_only:
        conditions.append("visible_in_txt = 1")

    where_clause = ""
    if conditions:
        where_clause = "WHERE " + " AND ".join(conditions)

    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            f"""
            SELECT
                id,
                ccoddis,
                cnomdis,
                active,
                visible_in_txt,
                notes
            FROM catalog_g7_net_commitments
            {where_clause}
            ORDER BY ccoddis
            """,
            params,
        ).fetchall()

    return [dict(row) for row in rows]


def list_g7_transfer_parties(
    db_path: Path,
    *,
    section: str | None = None,
    active_only: bool = False,
    visible_only: bool = False,
) -> list[dict[str, Any]]:
    if not db_path.exists():
        raise FileNotFoundError(db_path)

    conditions: list[str] = []
    params: list[Any] = []

    if section is not None:
        conditions.append("section = ?")
        params.append(section)

    if active_only:
        conditions.append("active = 1")

    if visible_only:
        conditions.append("visible_in_txt = 1")

    where_clause = ""
    if conditions:
        where_clause = "WHERE " + " AND ".join(conditions)

    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            f"""
            SELECT
                id,
                section,
                ccodgen,
                cnomgen,
                active,
                visible_in_txt,
                notes
            FROM catalog_g7_transfer_parties
            {where_clause}
            ORDER BY section, ccodgen
            """,
            params,
        ).fetchall()

    return [dict(row) for row in rows]
