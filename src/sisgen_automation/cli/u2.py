from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from sisgen_automation.u2.sources import U2SourcesValidationResult, validate_u2_sources
from sisgen_automation.u2.txt import U2TxtResult, create_u2_txt


def _render_u2_sources_summary(console: Console, result: U2SourcesValidationResult) -> None:
    console.print("")
    console.print("[bold green]Validacion de fuentes U2 completada.[/bold green]")
    console.print("")

    table = Table(title=f"Resumen fuentes U2 {result.period}")
    table.add_column("Metrica")
    table.add_column("Valor", justify="right")

    table.add_row("Registros CIUGEN", str(len(result.rows)))
    table.add_row("Errores", str(len(result.errors)))
    table.add_row("Advertencias", str(len(result.warnings)))
    table.add_row("Clientes libres", f"{result.totals.free_clients:.0f}")
    table.add_row("Consumo MWh", f"{result.totals.consumption_mwh:.3f}")
    table.add_row("Facturacion S/", f"{result.totals.billing_s:.2f}")

    console.print(table)

    for issue in result.issues[:30]:
        console.print(
            f"{issue.severity.value} | fila {issue.row or 'general'} | "
            f"{issue.ciiu_code or ''} | {issue.field or ''} | "
            f"{issue.message} | {issue.value or ''}"
        )

    if result.has_errors:
        console.print("[bold red]Las fuentes U2 no estan listas para generar TXT.[/bold red]")
    else:
        console.print("[bold green]Las fuentes U2 estan listas.[/bold green]")


def _render_u2_txt_summary(console: Console, result: U2TxtResult) -> None:
    console.print("")
    console.print(f"[bold green]TXT U2 generado:[/bold green] {result.output_path}")
    console.print("")

    table = Table(title=f"Resumen TXT U2 {result.period}")
    table.add_column("Metrica")
    table.add_column("Valor", justify="right")

    table.add_row("Clasificaciones CIIU", str(result.rows_count))
    table.add_row("Advertencias de fuentes", str(result.warnings_count))
    table.add_row("Clientes libres", f"{result.free_clients:.0f}")
    table.add_row("Consumo MWh", f"{result.consumption_mwh:.3f}")
    table.add_row("Facturacion S/", f"{result.billing_s:.2f}")

    console.print(table)


def register_u2_commands(app: typer.Typer, console: Console) -> None:
    @app.command("validate-u2-sources")
    def validate_u2_sources_command(
        ciugen: Path = typer.Option(
            ...,
            "--ciugen",
            help="Ruta del CIUGEN.DBF.",
        ),
        period: str = typer.Option(
            ...,
            "--period",
            "-p",
            help="Periodo a validar en formato YYYY-MM. Ejemplo: 2025-11.",
        ),
        catalog: Path = typer.Option(
            ...,
            "--catalog",
            "-c",
            help="Ruta del catalogo local U2 en YAML.",
        ),
        fail_on_errors: bool = typer.Option(
            False,
            "--fail-on-errors",
            help="Termina con codigo de error si se encuentran errores.",
        ),
    ) -> None:
        """Valida CIUGEN como fuente del Formato U2."""
        try:
            result = validate_u2_sources(
                ciugen_path=ciugen,
                period=period,
                catalog_path=catalog,
            )
        except ValueError as error:
            console.print(f"[bold red]Error:[/bold red] {error}")
            raise typer.Exit(code=1) from error

        _render_u2_sources_summary(console, result)

        if fail_on_errors and result.has_errors:
            raise typer.Exit(code=1)

    @app.command("create-u2-txt")
    def create_u2_txt_command(
        ciugen: Path = typer.Option(
            ...,
            "--ciugen",
            help="Ruta del CIUGEN.DBF.",
        ),
        period: str = typer.Option(
            ...,
            "--period",
            "-p",
            help="Periodo a generar en formato YYYY-MM. Ejemplo: 2025-11.",
        ),
        catalog: Path = typer.Option(
            ...,
            "--catalog",
            "-c",
            help="Ruta del catalogo local U2 en YAML.",
        ),
        output: Optional[Path] = typer.Option(
            None,
            "--output",
            "-o",
            help="Ruta del TXT generado.",
        ),
    ) -> None:
        """Genera el Formato U2 en TXT."""
        try:
            result = create_u2_txt(
                ciugen_path=ciugen,
                period=period,
                catalog_path=catalog,
                output_path=output,
            )
        except ValueError as error:
            console.print(f"[bold red]Error:[/bold red] {error}")
            raise typer.Exit(code=1) from error

        _render_u2_txt_summary(console, result)
