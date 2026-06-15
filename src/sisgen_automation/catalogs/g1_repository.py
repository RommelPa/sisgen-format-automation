from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any


def list_g1_units(
    db_path: Path,
    *,
    source_format: str | None = None,
    active_only: bool = False,
) -> list[dict[str, Any]]:
    if not db_path.exists():
        raise FileNotFoundError(db_path)

    conditions: list[str] = []
    params: list[Any] = []

    if source_format:
        conditions.append("source_format = ?")
        params.append(source_format.upper())

    if active_only:
        conditions.append("active = 1")

    where_clause = ""
    if conditions:
        where_clause = "WHERE " + " AND ".join(conditions)

    query = f"""
        SELECT
            id,
            source_format,
            central,
            ccodcon,
            ccodcen,
            ctipgru,
            cnomnum,
            npotins,
            npotefe,
            active,
            visible_in_template,
            source_period
        FROM catalog_g1_units
        {where_clause}
        ORDER BY source_format, central, cnomnum
    """

    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(query, params).fetchall()

    return [dict(row) for row in rows]


def set_g1_unit_active(
    db_path: Path,
    *,
    unit_id: int,
    active: bool,
) -> dict[str, Any]:
    if not db_path.exists():
        raise FileNotFoundError(db_path)

    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row

        row = conn.execute(
            """
            SELECT
                id,
                source_format,
                central,
                ccodcon,
                ccodcen,
                ctipgru,
                cnomnum,
                active,
                visible_in_template
            FROM catalog_g1_units
            WHERE id = ?
            """,
            (unit_id,),
        ).fetchone()

        if row is None:
            raise ValueError(f"No existe unidad G1 con id {unit_id}.")

        conn.execute(
            """
            UPDATE catalog_g1_units
            SET active = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (1 if active else 0, unit_id),
        )
        conn.commit()

    result = dict(row)
    result["active"] = 1 if active else 0
    return result
