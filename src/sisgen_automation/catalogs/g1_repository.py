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
