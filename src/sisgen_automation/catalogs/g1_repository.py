from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any


def list_g1_units(
    db_path: Path,
    *,
    source_format: str | None = None,
    active_only: bool = False,
    visible_only: bool = False,
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

    if visible_only:
        conditions.append("visible_in_template = 1")

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


def get_g1_unit_by_id(
    conn: sqlite3.Connection,
    *,
    unit_id: int,
) -> sqlite3.Row:
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
            npotins,
            npotefe,
            active,
            visible_in_template,
            source_period,
            notes
        FROM catalog_g1_units
        WHERE id = ?
        """,
        (unit_id,),
    ).fetchone()

    if row is None:
        raise ValueError(f"No existe unidad G1 con id {unit_id}.")

    return row


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
        row = get_g1_unit_by_id(conn, unit_id=unit_id)

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


def set_g1_unit_visible(
    db_path: Path,
    *,
    unit_id: int,
    visible: bool,
) -> dict[str, Any]:
    if not db_path.exists():
        raise FileNotFoundError(db_path)

    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        row = get_g1_unit_by_id(conn, unit_id=unit_id)

        conn.execute(
            """
            UPDATE catalog_g1_units
            SET visible_in_template = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (1 if visible else 0, unit_id),
        )
        conn.commit()

    result = dict(row)
    result["visible_in_template"] = 1 if visible else 0
    return result



def _normalize_g1_text(value: str | None) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _normalize_g1_format(value: str) -> str:
    source_format = value.strip().upper()
    if source_format not in {"CENHID", "CENTER"}:
        raise ValueError("Formato G1 invalido. Usa CENHID o CENTER.")
    return source_format


def get_g1_unit(
    db_path: Path,
    *,
    unit_id: int,
) -> dict[str, Any]:
    if not db_path.exists():
        raise FileNotFoundError(db_path)

    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        row = get_g1_unit_by_id(conn, unit_id=unit_id)

    return dict(row)


def create_g1_unit(
    db_path: Path,
    *,
    source_format: str,
    central: str,
    ccodcon: str,
    ccodcen: str,
    ctipgru: str,
    cnomnum: str,
    npotins: str | None = None,
    npotefe: str | None = None,
    notes: str | None = None,
    active: bool = True,
) -> dict[str, Any]:
    if not db_path.exists():
        raise FileNotFoundError(db_path)

    clean_format = _normalize_g1_format(source_format)
    clean_central = _normalize_g1_text(central)
    clean_ccodcon = _normalize_g1_text(ccodcon)
    clean_ccodcen = _normalize_g1_text(ccodcen)
    clean_ctipgru = _normalize_g1_text(ctipgru)
    clean_cnomnum = _normalize_g1_text(cnomnum)
    clean_npotins = _normalize_g1_text(npotins)
    clean_npotefe = _normalize_g1_text(npotefe)
    clean_notes = _normalize_g1_text(notes)

    if not clean_central:
        raise ValueError("La central es obligatoria.")

    if not clean_ccodcon:
        raise ValueError("CCODCON es obligatorio.")

    if not clean_ccodcen:
        raise ValueError("CCODCEN es obligatorio.")

    if not clean_cnomnum:
        raise ValueError("El nombre de unidad es obligatorio.")

    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row

        try:
            cursor = conn.execute(
                """
                INSERT INTO catalog_g1_units (
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
                    notes
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    clean_format,
                    clean_central,
                    clean_ccodcon,
                    clean_ccodcen,
                    clean_ctipgru,
                    clean_cnomnum,
                    clean_npotins,
                    clean_npotefe,
                    1 if active else 0,
                    1 if active else 0,
                    clean_notes,
                ),
            )
        except sqlite3.IntegrityError as error:
            raise ValueError("Ya existe una unidad G1 con esos codigos.") from error

        unit_id = int(cursor.lastrowid)
        conn.commit()
        row = get_g1_unit_by_id(conn, unit_id=unit_id)

    return dict(row)


def update_g1_unit(
    db_path: Path,
    *,
    unit_id: int,
    source_format: str,
    central: str,
    ccodcon: str,
    ccodcen: str,
    ctipgru: str,
    cnomnum: str,
    npotins: str | None = None,
    npotefe: str | None = None,
    notes: str | None = None,
) -> dict[str, Any]:
    if not db_path.exists():
        raise FileNotFoundError(db_path)

    clean_format = _normalize_g1_format(source_format)
    clean_central = _normalize_g1_text(central)
    clean_ccodcon = _normalize_g1_text(ccodcon)
    clean_ccodcen = _normalize_g1_text(ccodcen)
    clean_ctipgru = _normalize_g1_text(ctipgru)
    clean_cnomnum = _normalize_g1_text(cnomnum)
    clean_npotins = _normalize_g1_text(npotins)
    clean_npotefe = _normalize_g1_text(npotefe)
    clean_notes = _normalize_g1_text(notes)

    if not clean_central:
        raise ValueError("La central es obligatoria.")

    if not clean_ccodcon:
        raise ValueError("CCODCON es obligatorio.")

    if not clean_ccodcen:
        raise ValueError("CCODCEN es obligatorio.")

    if not clean_cnomnum:
        raise ValueError("El nombre de unidad es obligatorio.")

    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        get_g1_unit_by_id(conn, unit_id=unit_id)

        try:
            conn.execute(
                """
                UPDATE catalog_g1_units
                SET
                    source_format = ?,
                    central = ?,
                    ccodcon = ?,
                    ccodcen = ?,
                    ctipgru = ?,
                    cnomnum = ?,
                    npotins = ?,
                    npotefe = ?,
                    notes = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (
                    clean_format,
                    clean_central,
                    clean_ccodcon,
                    clean_ccodcen,
                    clean_ctipgru,
                    clean_cnomnum,
                    clean_npotins,
                    clean_npotefe,
                    clean_notes,
                    unit_id,
                ),
            )
        except sqlite3.IntegrityError as error:
            raise ValueError("Ya existe una unidad G1 con esos codigos.") from error

        conn.commit()
        row = get_g1_unit_by_id(conn, unit_id=unit_id)

    return dict(row)
