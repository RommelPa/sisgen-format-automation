from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

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
