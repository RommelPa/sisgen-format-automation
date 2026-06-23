from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any


SCHEMA = """
CREATE TABLE IF NOT EXISTS catalog_g2_company (
    id INTEGER PRIMARY KEY CHECK (id = 1),

    ccodeemp TEXT NOT NULL,
    name TEXT NOT NULL,

    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS catalog_g2_distributors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    ccoddis TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL,

    active INTEGER NOT NULL DEFAULT 1,
    visible_in_txt INTEGER NOT NULL DEFAULT 1,

    notes TEXT,

    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
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


def ensure_g2_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    conn.commit()


def get_g2_company(db_path: Path) -> dict[str, Any]:
    if not db_path.exists():
        raise FileNotFoundError(db_path)

    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            """
            SELECT
                ccodeemp,
                name
            FROM catalog_g2_company
            WHERE id = 1
            """
        ).fetchone()

    if row is None:
        raise ValueError("No existe empresa G2 en la base SQLite.")

    return dict(row)


def list_g2_distributors(
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

    query = f"""
        SELECT
            id,
            ccoddis,
            display_name,
            active,
            visible_in_txt,
            notes
        FROM catalog_g2_distributors
        {where_clause}
        ORDER BY ccoddis
    """

    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(query, params).fetchall()

    return [dict(row) for row in rows]


def set_g2_distributor_active(
    db_path: Path,
    *,
    distributor_id: int,
    active: bool,
) -> dict[str, Any]:
    if not db_path.exists():
        raise FileNotFoundError(db_path)

    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        ensure_g2_schema(conn)

        row = conn.execute(
            """
            SELECT
                id,
                ccoddis,
                display_name,
                active,
                visible_in_txt,
                notes
            FROM catalog_g2_distributors
            WHERE id = ?
            """,
            (distributor_id,),
        ).fetchone()

        if row is None:
            raise ValueError(f"No existe distribuidora G2 con id={distributor_id}.")

        conn.execute(
            """
            UPDATE catalog_g2_distributors
            SET
                active = ?,
                visible_in_txt = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (1 if active else 0, 1 if active else 0, distributor_id),
        )
        conn.commit()

        updated = conn.execute(
            """
            SELECT
                id,
                ccoddis,
                display_name,
                active,
                visible_in_txt,
                notes
            FROM catalog_g2_distributors
            WHERE id = ?
            """,
            (distributor_id,),
        ).fetchone()

    if updated is None:
        raise ValueError(f"No se pudo actualizar distribuidora G2 con id={distributor_id}.")

    return dict(updated)




def _get_g2_distributor_by_id(
    conn: sqlite3.Connection,
    *,
    distributor_id: int,
) -> sqlite3.Row:
    row = conn.execute(
        """
        SELECT
            id,
            ccoddis,
            display_name,
            active,
            visible_in_txt,
            notes
        FROM catalog_g2_distributors
        WHERE id = ?
        """,
        (distributor_id,),
    ).fetchone()

    if row is None:
        raise ValueError(f"No existe distribuidora G2 con id={distributor_id}.")

    return row


def create_g2_distributor(
    db_path: Path,
    *,
    ccoddis: str,
    display_name: str,
    notes: str | None = None,
    active: bool = True,
) -> dict[str, Any]:
    if not db_path.exists():
        raise FileNotFoundError(db_path)

    code = ccoddis.strip().upper()
    name = display_name.strip()
    clean_notes = notes.strip() if notes else None

    if not code:
        raise ValueError("El codigo CCODDIS es obligatorio.")

    if not name:
        raise ValueError("El nombre de la distribuidora es obligatorio.")

    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        ensure_g2_schema(conn)

        try:
            cursor = conn.execute(
                """
                INSERT INTO catalog_g2_distributors (
                    ccoddis,
                    display_name,
                    active,
                    visible_in_txt,
                    notes
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    code,
                    name,
                    1 if active else 0,
                    1 if active else 0,
                    clean_notes,
                ),
            )
        except sqlite3.IntegrityError as error:
            raise ValueError(f"Ya existe una distribuidora G2 con codigo {code}.") from error

        distributor_id = int(cursor.lastrowid)
        conn.commit()

        row = _get_g2_distributor_by_id(conn, distributor_id=distributor_id)

    return dict(row)


def update_g2_distributor(
    db_path: Path,
    *,
    distributor_id: int,
    ccoddis: str,
    display_name: str,
    notes: str | None = None,
) -> dict[str, Any]:
    if not db_path.exists():
        raise FileNotFoundError(db_path)

    code = ccoddis.strip().upper()
    name = display_name.strip()
    clean_notes = notes.strip() if notes else None

    if not code:
        raise ValueError("El codigo CCODDIS es obligatorio.")

    if not name:
        raise ValueError("El nombre de la distribuidora es obligatorio.")

    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        ensure_g2_schema(conn)
        _get_g2_distributor_by_id(conn, distributor_id=distributor_id)

        try:
            conn.execute(
                """
                UPDATE catalog_g2_distributors
                SET
                    ccoddis = ?,
                    display_name = ?,
                    notes = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (code, name, clean_notes, distributor_id),
            )
        except sqlite3.IntegrityError as error:
            raise ValueError(f"Ya existe una distribuidora G2 con codigo {code}.") from error

        conn.commit()
        row = _get_g2_distributor_by_id(conn, distributor_id=distributor_id)

    return dict(row)
