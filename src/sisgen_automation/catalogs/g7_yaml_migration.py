from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path
from typing import Any

import yaml

from sisgen_automation.catalogs.g7_repository import ensure_g7_schema


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

    if text in {"true", "1", "yes", "si", "s"}:
        return 1

    if text in {"false", "0", "no", "n"}:
        return 0

    return int(default)


def load_yaml_catalog(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))

    if not isinstance(data, dict):
        raise ValueError(f"El archivo {path} no contiene un diccionario YAML valido.")

    required_sections = [
        "company",
        "system",
        "energy_purchases",
        "energy_sales",
        "net_commitments",
        "power_transfers",
        "transfer_valuations",
    ]

    for section in required_sections:
        if section not in data:
            raise ValueError(f"El archivo {path} no contiene la seccion {section}.")

    if not isinstance(data["company"], dict):
        raise ValueError("company debe ser un diccionario.")

    if not isinstance(data["system"], dict):
        raise ValueError("system debe ser un diccionario.")

    for section in required_sections[2:]:
        if not isinstance(data[section], list):
            raise ValueError(f"{section} debe ser una lista.")

    return data


def upsert_energy_parties(
    conn: sqlite3.Connection,
    *,
    section: str,
    rows: list[Any],
) -> tuple[int, int, int]:
    inserted = 0
    updated = 0
    skipped = 0

    for raw in rows:
        if not isinstance(raw, dict):
            skipped += 1
            continue

        ccodgen = as_text(raw.get("ccodgen"))
        cdesgen = as_text(raw.get("cdesgen"))

        if not ccodgen or not cdesgen:
            skipped += 1
            continue

        exists = conn.execute(
            """
            SELECT id
            FROM catalog_g7_energy_parties
            WHERE section = ? AND ccodgen = ?
            """,
            (section, ccodgen),
        ).fetchone()

        values = (
            section,
            ccodgen,
            cdesgen,
            as_bool_int(raw.get("active"), True),
            as_bool_int(raw.get("visible_in_txt"), True),
            as_text(raw.get("notes")),
        )

        if exists:
            conn.execute(
                """
                UPDATE catalog_g7_energy_parties
                SET
                    cdesgen = ?,
                    active = ?,
                    visible_in_txt = ?,
                    notes = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE section = ? AND ccodgen = ?
                """,
                (values[2], values[3], values[4], values[5], section, ccodgen),
            )
            updated += 1
        else:
            conn.execute(
                """
                INSERT INTO catalog_g7_energy_parties (
                    section,
                    ccodgen,
                    cdesgen,
                    active,
                    visible_in_txt,
                    notes
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                values,
            )
            inserted += 1

    return inserted, updated, skipped


def upsert_net_commitments(
    conn: sqlite3.Connection,
    *,
    rows: list[Any],
) -> tuple[int, int, int]:
    inserted = 0
    updated = 0
    skipped = 0

    for raw in rows:
        if not isinstance(raw, dict):
            skipped += 1
            continue

        ccoddis = as_text(raw.get("ccoddis"))
        cnomdis = as_text(raw.get("cnomdis"))

        if not ccoddis or not cnomdis:
            skipped += 1
            continue

        exists = conn.execute(
            """
            SELECT id
            FROM catalog_g7_net_commitments
            WHERE ccoddis = ?
            """,
            (ccoddis,),
        ).fetchone()

        values = (
            ccoddis,
            cnomdis,
            as_bool_int(raw.get("active"), True),
            as_bool_int(raw.get("visible_in_txt"), True),
            as_text(raw.get("notes")),
        )

        if exists:
            conn.execute(
                """
                UPDATE catalog_g7_net_commitments
                SET
                    cnomdis = ?,
                    active = ?,
                    visible_in_txt = ?,
                    notes = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE ccoddis = ?
                """,
                (values[1], values[2], values[3], values[4], ccoddis),
            )
            updated += 1
        else:
            conn.execute(
                """
                INSERT INTO catalog_g7_net_commitments (
                    ccoddis,
                    cnomdis,
                    active,
                    visible_in_txt,
                    notes
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                values,
            )
            inserted += 1

    return inserted, updated, skipped


def upsert_transfer_parties(
    conn: sqlite3.Connection,
    *,
    section: str,
    rows: list[Any],
) -> tuple[int, int, int]:
    inserted = 0
    updated = 0
    skipped = 0

    for raw in rows:
        if not isinstance(raw, dict):
            skipped += 1
            continue

        ccodgen = as_text(raw.get("ccodgen"))
        cnomgen = as_text(raw.get("cnomgen"))

        if not ccodgen or not cnomgen:
            skipped += 1
            continue

        exists = conn.execute(
            """
            SELECT id
            FROM catalog_g7_transfer_parties
            WHERE section = ? AND ccodgen = ?
            """,
            (section, ccodgen),
        ).fetchone()

        values = (
            section,
            ccodgen,
            cnomgen,
            as_bool_int(raw.get("active"), True),
            as_bool_int(raw.get("visible_in_txt"), True),
            as_text(raw.get("notes")),
        )

        if exists:
            conn.execute(
                """
                UPDATE catalog_g7_transfer_parties
                SET
                    cnomgen = ?,
                    active = ?,
                    visible_in_txt = ?,
                    notes = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE section = ? AND ccodgen = ?
                """,
                (values[2], values[3], values[4], values[5], section, ccodgen),
            )
            updated += 1
        else:
            conn.execute(
                """
                INSERT INTO catalog_g7_transfer_parties (
                    section,
                    ccodgen,
                    cnomgen,
                    active,
                    visible_in_txt,
                    notes
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                values,
            )
            inserted += 1

    return inserted, updated, skipped


def migrate_g7_yaml_catalog(
    *,
    source_path: Path,
    db_path: Path,
) -> tuple[int, int, int]:
    if not source_path.exists():
        raise FileNotFoundError(source_path)

    db_path.parent.mkdir(parents=True, exist_ok=True)

    data = load_yaml_catalog(source_path)

    company = data["company"]
    system = data["system"]

    ccodeemp = as_text(company.get("ccodeemp"))
    company_name = as_text(company.get("name"))
    ccosisi = as_text(system.get("ccosisi"))

    if not ccodeemp or not company_name:
        raise ValueError("company.ccodeemp y company.name son obligatorios.")

    if not ccosisi:
        raise ValueError("system.ccosisi es obligatorio.")

    inserted = 0
    updated = 0
    skipped = 0

    with sqlite3.connect(db_path) as conn:
        ensure_g7_schema(conn)

        conn.execute(
            """
            INSERT INTO catalog_g7_company (
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

        conn.execute(
            """
            INSERT INTO catalog_g7_system (
                id,
                ccosisi
            )
            VALUES (1, ?)
            ON CONFLICT(id) DO UPDATE SET
                ccosisi = excluded.ccosisi,
                updated_at = CURRENT_TIMESTAMP
            """,
            (ccosisi,),
        )

        for section in ("energy_purchases", "energy_sales"):
            section_inserted, section_updated, section_skipped = upsert_energy_parties(
                conn,
                section=section,
                rows=data[section],
            )
            inserted += section_inserted
            updated += section_updated
            skipped += section_skipped

        section_inserted, section_updated, section_skipped = upsert_net_commitments(
            conn,
            rows=data["net_commitments"],
        )
        inserted += section_inserted
        updated += section_updated
        skipped += section_skipped

        for section in ("power_transfers", "transfer_valuations"):
            section_inserted, section_updated, section_skipped = upsert_transfer_parties(
                conn,
                section=section,
                rows=data[section],
            )
            inserted += section_inserted
            updated += section_updated
            skipped += section_skipped

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
                "G7",
                str(source_path),
                inserted,
                updated,
                skipped,
                "Migracion G7 YAML a SQLite",
            ),
        )

        conn.commit()

    return inserted, updated, skipped


def print_summary(db_path: Path) -> None:
    with sqlite3.connect(db_path) as conn:
        company = conn.execute(
            """
            SELECT ccodeemp, name
            FROM catalog_g7_company
            WHERE id = 1
            """
        ).fetchone()

        system = conn.execute(
            """
            SELECT ccosisi
            FROM catalog_g7_system
            WHERE id = 1
            """
        ).fetchone()

        energy = conn.execute(
            """
            SELECT section, COUNT(*), SUM(active), SUM(visible_in_txt)
            FROM catalog_g7_energy_parties
            GROUP BY section
            ORDER BY section
            """
        ).fetchall()

        net_commitments = conn.execute(
            """
            SELECT COUNT(*), SUM(active), SUM(visible_in_txt)
            FROM catalog_g7_net_commitments
            """
        ).fetchone()

        transfers = conn.execute(
            """
            SELECT section, COUNT(*), SUM(active), SUM(visible_in_txt)
            FROM catalog_g7_transfer_parties
            GROUP BY section
            ORDER BY section
            """
        ).fetchall()

    print(f"BD creada/actualizada: {db_path}")

    if company:
        print(f"Empresa G7: {company[0]} - {company[1]}")

    if system:
        print(f"Sistema G7: {system[0]}")

    for section, total, active, visible in energy:
        print(f"{section}: total={total}, activos={active}, visibles={visible}")

    if net_commitments:
        total, active, visible = net_commitments
        print(f"net_commitments: total={total}, activos={active}, visibles={visible}")

    for section, total, active, visible in transfers:
        print(f"{section}: total={total}, activos={active}, visibles={visible}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Migra el catalogo G7 YAML local a SQLite."
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=Path("config/local/g7_units.yaml"),
        help="Ruta del catalogo YAML G7.",
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=Path("data/catalogs/sisgen_catalogs.db"),
        help="Ruta de la base SQLite de catalogos.",
    )

    args = parser.parse_args()

    inserted, updated, skipped = migrate_g7_yaml_catalog(
        source_path=args.source,
        db_path=args.db,
    )

    print(f"G7: inserted={inserted}, updated={updated}, skipped={skipped}")
    print_summary(args.db)


if __name__ == "__main__":
    main()
