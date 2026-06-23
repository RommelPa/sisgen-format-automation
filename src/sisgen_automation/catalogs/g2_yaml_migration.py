from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path
from typing import Any

import yaml

from sisgen_automation.catalogs.g2_repository import ensure_g2_schema


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

    if text in {"true", "1", "yes", "si", "s?", "s"}:
        return 1

    if text in {"false", "0", "no", "n"}:
        return 0

    return int(default)


def load_yaml_catalog(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))

    if not isinstance(data, dict):
        raise ValueError(f"El archivo {path} no contiene un diccionario YAML valido.")

    company = data.get("company")
    distributors = data.get("distributors")

    if not isinstance(company, dict):
        raise ValueError(f"El archivo {path} no contiene company valido.")

    if not isinstance(distributors, list):
        raise ValueError(f"El archivo {path} no contiene lista distributors valida.")

    return data


def migrate_g2_yaml_catalog(
    *,
    source_path: Path,
    db_path: Path,
) -> tuple[int, int, int]:
    if not source_path.exists():
        raise FileNotFoundError(source_path)

    db_path.parent.mkdir(parents=True, exist_ok=True)

    data = load_yaml_catalog(source_path)

    company = data["company"]
    distributors = data["distributors"]

    ccodeemp = as_text(company.get("ccodeemp"))
    company_name = as_text(company.get("name"))

    if not ccodeemp or not company_name:
        raise ValueError("company.ccodeemp y company.name son obligatorios.")

    inserted = 0
    updated = 0
    skipped = 0

    with sqlite3.connect(db_path) as conn:
        ensure_g2_schema(conn)

        conn.execute(
            """
            INSERT INTO catalog_g2_company (
                id,
                ccodeemp,
                name
            )
            VALUES (1, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                ccodeemp = excluded.ccodeemp,
                name = excluded.name,
                updated_at = CURRENT_TIMESTAMP
            """,
            (ccodeemp, company_name),
        )

        for raw_distributor in distributors:
            if not isinstance(raw_distributor, dict):
                skipped += 1
                continue

            ccoddis = as_text(raw_distributor.get("ccoddis"))
            display_name = as_text(raw_distributor.get("display_name"))

            if not ccoddis or not display_name:
                skipped += 1
                continue

            exists = conn.execute(
                """
                SELECT id
                FROM catalog_g2_distributors
                WHERE ccoddis = ?
                """,
                (ccoddis,),
            ).fetchone()

            values = {
                "ccoddis": ccoddis,
                "display_name": display_name,
                "active": as_bool_int(raw_distributor.get("active"), True),
                "visible_in_txt": as_bool_int(raw_distributor.get("visible_in_txt"), True),
                "notes": as_text(raw_distributor.get("notes")),
            }

            if exists:
                conn.execute(
                    """
                    UPDATE catalog_g2_distributors
                    SET display_name = ?,
                        active = ?,
                        visible_in_txt = ?,
                        notes = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE ccoddis = ?
                    """,
                    (
                        values["display_name"],
                        values["active"],
                        values["visible_in_txt"],
                        values["notes"],
                        values["ccoddis"],
                    ),
                )
                updated += 1
            else:
                conn.execute(
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
                        values["ccoddis"],
                        values["display_name"],
                        values["active"],
                        values["visible_in_txt"],
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
                "G2",
                str(source_path),
                inserted,
                updated,
                skipped,
                "Migracion G2 YAML a SQLite",
            ),
        )

        conn.commit()

    return inserted, updated, skipped


def print_summary(db_path: Path) -> None:
    with sqlite3.connect(db_path) as conn:
        total = conn.execute(
            "SELECT COUNT(*) FROM catalog_g2_distributors"
        ).fetchone()[0]
        active = conn.execute(
            "SELECT COUNT(*) FROM catalog_g2_distributors WHERE active = 1"
        ).fetchone()[0]
        visible = conn.execute(
            "SELECT COUNT(*) FROM catalog_g2_distributors WHERE visible_in_txt = 1"
        ).fetchone()[0]

        company = conn.execute(
            """
            SELECT ccodeemp, name
            FROM catalog_g2_company
            WHERE id = 1
            """
        ).fetchone()

    print(f"BD creada/actualizada: {db_path}")
    if company is not None:
        print(f"Empresa G2: {company[0]} - {company[1]}")
    print(f"Total catalog_g2_distributors: {total}")
    print(f"Activos: {active}")
    print(f"Visibles TXT: {visible}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Migra catalogo YAML G2 a SQLite.")
    parser.add_argument("--source", default="config/local/g2_distributors.yaml")
    parser.add_argument("--db", default="data/catalogs/sisgen_catalogs.db")
    args = parser.parse_args()

    source_path = Path(args.source)
    db_path = Path(args.db)

    inserted, updated, skipped = migrate_g2_yaml_catalog(
        source_path=source_path,
        db_path=db_path,
    )

    print(f"G2: inserted={inserted}, updated={updated}, skipped={skipped}")
    print_summary(db_path)


if __name__ == "__main__":
    main()
