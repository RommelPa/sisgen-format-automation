from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from sisgen_automation.catalogs.g1_repository import list_g1_units
from sisgen_automation.catalogs.g1_yaml_migration import (
    migrate_g1_yaml_catalogs,
    print_summary,
)


def register_catalog_commands(app: typer.Typer, console: Console) -> None:
    catalog_app = typer.Typer(
        help="Herramientas para administrar catálogos locales.",
        no_args_is_help=True,
    )

    app.add_typer(catalog_app, name="catalog")

    @catalog_app.command("migrate-g1-yaml")
    def migrate_g1_yaml_command(
        config_dir: Path = typer.Option(
            Path("config/local"),
            "--config-dir",
            help="Carpeta donde están los YAML locales.",
        ),
        db: Path = typer.Option(
            Path("data/catalogs/sisgen_catalogs.db"),
            "--db",
            help="Ruta de la base SQLite local.",
        ),
    ) -> None:
        """Migra catálogos YAML G1 hacia SQLite."""
        try:
            results = migrate_g1_yaml_catalogs(config_dir=config_dir, db_path=db)
        except Exception as error:
            console.print(f"[bold red]Error:[/bold red] {error}")
            raise typer.Exit(code=1) from error

        for source_format, (inserted, updated, skipped) in results.items():
            console.print(
                f"{source_format}: inserted={inserted}, "
                f"updated={updated}, skipped={skipped}"
            )

        print_summary(db)


    @catalog_app.command("list-g1-units")
    def list_g1_units_command(
        db: Path = typer.Option(
            Path("data/catalogs/sisgen_catalogs.db"),
            "--db",
            help="Ruta de la base SQLite local.",
        ),
        source_format: str | None = typer.Option(
            None,
            "--source-format",
            help="Filtra por CENHID o CENTER.",
        ),
        active_only: bool = typer.Option(
            False,
            "--active-only",
            help="Muestra solo registros activos.",
        ),
    ) -> None:
        """Lista unidades G1 almacenadas en SQLite."""
        try:
            rows = list_g1_units(
                db,
                source_format=source_format,
                active_only=active_only,
            )
        except Exception as error:
            console.print(f"[bold red]Error:[/bold red] {error}")
            raise typer.Exit(code=1) from error

        if not rows:
            console.print("No se encontraron unidades G1.")
            return

        table = Table(title="Catalogo G1 SQLite")
        table.add_column("Fuente")
        table.add_column("Central")
        table.add_column("CCODCON")
        table.add_column("Tipo")
        table.add_column("Unidad")
        table.add_column("NPOTINS")
        table.add_column("NPOTEFE")
        table.add_column("Activo")
        table.add_column("Visible")

        for row in rows:
            table.add_row(
                str(row["source_format"]),
                str(row["central"]),
                str(row["ccodcon"]),
                str(row["ctipgru"] or "-"),
                str(row["cnomnum"]),
                str(row["npotins"] or ""),
                str(row["npotefe"] or ""),
                "si" if row["active"] else "no",
                "si" if row["visible_in_template"] else "no",
            )

        console.print(table)
        console.print(f"Total: {len(rows)}")
