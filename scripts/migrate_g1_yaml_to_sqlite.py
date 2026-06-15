from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path
from typing import Any

import yaml


SCHEMA = """
CREATE TABLE IF NOT EXISTS catalog_g1_units (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    source_format TEXT NOT NULL,
    central TEXT NOT NULL,

    ccodcon TEXT NOT NULL,
    ccodcen TEXT NOT NULL,
    ctipgru TEXT NOT NULL DEFAULT '',
    cnomnum TEXT NOT NULL,

    npotins TEXT,
    npotefe TEXT,

    active INTEGER NOT NULL DEFAULT 1,
    visible_in_template INTEGER NOT NULL DEFAULT 1,
    source_period TEXT,

    notes TEXT,

    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE (source_format, ccodcon, ccodcen, ctipgru, cnomnum)
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


def as_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def as_bool_int(value: Any, default: bool = True) -> int:
    if value is None:
        return int(default)

    if isinstance(value, bool):
        return int(value)

    text = str(value).strip().lower()
    if text in {"true", "1", "yes", "si", "sí", "s"}:
        return 1
    if text in {"false", "0", "no", "n"}:
        return 0

    return int(default)


def load_units(path: Path) -> list[dict[str, Any]]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    units = data.get("units", [])

    if not isinstance(units, list):
        raise ValueError(f"El archivo {path} no tiene una lista units válida.")

    return units


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    conn.commit()


def migrate_file(
    conn: sqlite3.Connection,
    *,
    source_format: str,
    source_path: Path,
) -> tuple[int, int, int]:
    inserted = 0
    updated = 0
    skipped = 0

    units = load_units(source_path)

    for unit in units:
        central = as_text(unit.get("central"))
        ccodcon = as_text(unit.get("ccodcon"))
        ccodcen = as_text(unit.get("ccodcen"))
        ctipgru = as_text(unit.get("ctipgru"))
        cnomnum = as_text(unit.get("cnomnum"))

        if not central or not ccodcon or not ccodcen or not cnomnum:
            skipped += 1
            continue

        exists = conn.execute(
            """
            SELECT id
            FROM catalog_g1_units
            WHERE source_format = ?
              AND ccodcon = ?
              AND ccodcen = ?
              AND ctipgru = ?
              AND cnomnum = ?
            """,
            (source_format, ccodcon, ccodcen, ctipgru, cnomnum),
        ).fetchone()

        values = {
            "source_format": source_format,
            "central": central,
            "ccodcon": ccodcon,
            "ccodcen": ccodcen,
            "ctipgru": ctipgru,
            "cnomnum": cnomnum,
            "npotins": as_text(unit.get("npotins")),
            "npotefe": as_text(unit.get("npotefe")),
            "active": as_bool_int(unit.get("active"), True),
            "visible_in_template": as_bool_int(unit.get("visible_in_template"), True),
            "source_period": as_text(unit.get("source_period")),
            "notes": as_text(unit.get("notes")),
        }

        if exists:
            conn.execute(
                """
                UPDATE catalog_g1_units
                SET central = ?,
                    npotins = ?,
                    npotefe = ?,
                    active = ?,
                    visible_in_template = ?,
                    source_period = ?,
                    notes = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (
                    values["central"],
                    values["npotins"],
                    values["npotefe"],
                    values["active"],
                    values["visible_in_template"],
                    values["source_period"],
                    values["notes"],
                    exists[0],
                ),
            )
            updated += 1
        else:
            conn.execute(
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
                    source_period,
                    notes
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    values["source_format"],
                    values["central"],
                    values["ccodcon"],
                    values["ccodcen"],
                    values["ctipgru"],
                    values["cnomnum"],
                    values["npotins"],
                    values["npotefe"],
                    values["active"],
                    values["visible_in_template"],
                    values["source_period"],
                    values["notes"],
                ),
            )
            inserted += 1

    conn.execute(
        """
        INSERT INTO catalog_migration_audit (
            source_type,
            source_name,
            source_path,
            inserted_count,
            updated_count,
            skipped_count,
            notes
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "YAML",
            source_format,
            str(source_path),
            inserted,
            updated,
            skipped,
            "Migración G1 YAML a SQLite",
        ),
    )

    conn.commit()

    return inserted, updated, skipped


def main() -> None:
    parser = argparse.ArgumentParser(description="Migra catálogos YAML G1 a SQLite.")
    parser.add_argument("--config-dir", default="config/local")
    parser.add_argument("--db", default="data/catalogs/sisgen_catalogs.db")
    args = parser.parse_args()

    config_dir = Path(args.config_dir)
    db_path = Path(args.db)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    sources = [
        ("CENHID", config_dir / "cenhid_units.yaml"),
        ("CENTER", config_dir / "center_units.yaml"),
    ]

    for _, source_path in sources:
        if not source_path.exists():
            raise FileNotFoundError(source_path)

    with sqlite3.connect(db_path) as conn:
        ensure_schema(conn)

        for source_format, source_path in sources:
            inserted, updated, skipped = migrate_file(
                conn,
                source_format=source_format,
                source_path=source_path,
            )
            print(
                f"{source_format}: inserted={inserted}, "
                f"updated={updated}, skipped={skipped}"
            )

        total = conn.execute("SELECT COUNT(*) FROM catalog_g1_units").fetchone()[0]
        active = conn.execute(
            "SELECT COUNT(*) FROM catalog_g1_units WHERE active = 1"
        ).fetchone()[0]

    print(f"BD creada/actualizada: {db_path}")
    print(f"Total catalog_g1_units: {total}")
    print(f"Activos: {active}")


if __name__ == "__main__":
    main()
