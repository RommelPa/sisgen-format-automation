from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from sisgen_automation.g1.sources import (
    G1SourcesValidationResult,
    validate_g1_sources,
    write_g1_sources_validation_markdown,
)
from sisgen_automation.g1.txt import G1TxtResult, create_g1_txt


def register_g1_commands(app: typer.Typer, console: Console) -> None:
    def _render_g1_sources_summary(
        result: G1SourcesValidationResult,
        output_path: Path,
    ) -> None:
        console.print("")
        console.print(f"[bold green]Validación de fuentes G1 generada:[/bold green] {output_path}")
        console.print("")

        table = Table(title=f"Resumen G1 {result.period}")
        table.add_column("Métrica")
        table.add_column("Valor", justify="right")

        table.add_row("Grupos hidro", str(result.hydro_group_count))
        table.add_row("Centrales hidro", str(len(result.hydro_blocks)))
        table.add_row("DACOCE hidro", str(result.dacoce_hydro_count))
        table.add_row("Grupos termo", str(result.thermal_group_count))
        table.add_row("Centrales termo", str(len(result.thermal_blocks)))
        table.add_row("DACOCE termo", str(result.dacoce_thermal_count))
        table.add_row("COMCEN termo", str(result.comcen_record_count))
        table.add_row("Errores", str(len(result.errors)))
        table.add_row("Advertencias", str(len(result.warnings)))

        console.print(table)

        if result.has_errors:
            console.print("[bold red]Las fuentes no están listas para generar G1.[/bold red]")
        elif result.warnings:
            console.print("[bold yellow]Las fuentes tienen advertencias. Revisar antes de generar G1.[/bold yellow]")
        else:
            console.print("[bold green]Las fuentes están listas para generar G1.[/bold green]")


    @app.command("validate-g1-sources")
    def validate_g1_sources_command(
        cenhid: Path = typer.Option(
            ...,
            "--cenhid",
            help="Ruta del archivo CENHID.DBF.",
        ),
        center: Path = typer.Option(
            ...,
            "--center",
            help="Ruta del archivo CENTER.DBF.",
        ),
        dacoce: Path = typer.Option(
            ...,
            "--dacoce",
            help="Ruta del archivo DACOCE.DBF.",
        ),
        comcen: Path = typer.Option(
            ...,
            "--comcen",
            help="Ruta del archivo COMCEN.DBF.",
        ),
        period: str = typer.Option(
            ...,
            "--period",
            "-p",
            help="Periodo a validar en formato YYYY-MM. Ejemplo: 2026-01.",
        ),
        cenhid_catalog: Path = typer.Option(
            ...,
            "--cenhid-catalog",
            help="Ruta del catálogo local CENHID en YAML.",
        ),
        center_catalog: Path = typer.Option(
            ...,
            "--center-catalog",
            help="Ruta del catálogo local CENTER en YAML.",
        ),
        output: Optional[Path] = typer.Option(
            None,
            "--output",
            "-o",
            help="Ruta del reporte Markdown generado.",
        ),
        fail_on_errors: bool = typer.Option(
            False,
            "--fail-on-errors",
            help="Termina con código de error si se encuentran errores.",
        ),
    ) -> None:
        """Valida CENHID + CENTER + DACOCE como fuentes del Formato G1."""
        try:
            result = validate_g1_sources(
                cenhid_path=cenhid,
                center_path=center,
                dacoce_path=dacoce,
                comcen_path=comcen,
                period=period,
                cenhid_catalog_path=cenhid_catalog,
                center_catalog_path=center_catalog,
            )
        except ValueError as error:
            console.print(f"[bold red]Error:[/bold red] {error}")
            raise typer.Exit(code=1) from error

        output_path = output
        if output_path is None:
            output_path = Path("reports") / "g1" / f"G1_{period.replace('-', '_')}_sources_validation.md"

        write_g1_sources_validation_markdown(result, output_path)
        _render_g1_sources_summary(result, output_path)

        if fail_on_errors and result.has_errors:
            raise typer.Exit(code=1)
    
    def _render_g1_txt_summary(result: G1TxtResult) -> None:
        console.print("")
        console.print(f"[bold green]TXT G1 generado:[/bold green] {result.output_path}")
        console.print("")

        table = Table(title=f"Resumen TXT G1 {result.period}")
        table.add_column("Métrica")
        table.add_column("Valor", justify="right")

        table.add_row("Centrales hidro", str(result.hydro_central_count))
        table.add_row("Grupos hidro", str(result.hydro_group_count))
        table.add_row("Centrales termo", str(result.thermal_central_count))
        table.add_row("Grupos termo", str(result.thermal_group_count))
        table.add_row("Advertencias de fuentes", str(result.warnings_count))

        console.print(table)

        if result.warnings_count:
            console.print(
                "[bold yellow]El TXT fue generado con advertencias de fuente. "
                "Revisar validate-g1-sources.[/bold yellow]"
            )


    @app.command("create-g1-txt")
    def create_g1_txt_command(
        cenhid: Path = typer.Option(
            ...,
            "--cenhid",
            help="Ruta del archivo CENHID.DBF.",
        ),
        center: Path = typer.Option(
            ...,
            "--center",
            help="Ruta del archivo CENTER.DBF.",
        ),
        dacoce: Path = typer.Option(
            ...,
            "--dacoce",
            help="Ruta del archivo DACOCE.DBF.",
        ),
        comcen: Path = typer.Option(
            ...,
            "--comcen",
            help="Ruta del archivo COMCEN.DBF.",
        ),
        period: str = typer.Option(
            ...,
            "--period",
            "-p",
            help="Periodo a generar en formato YYYY-MM. Ejemplo: 2026-01.",
        ),
        cenhid_catalog: Path = typer.Option(
            ...,
            "--cenhid-catalog",
            help="Ruta del catálogo local CENHID en YAML.",
        ),
        center_catalog: Path = typer.Option(
            ...,
            "--center-catalog",
            help="Ruta del catálogo local CENTER en YAML.",
        ),
        output: Optional[Path] = typer.Option(
            None,
            "--output",
            "-o",
            help="Ruta del TXT generado.",
        ),
    ) -> None:
        """Genera el Formato G1 completo en TXT."""
        try:
            result = create_g1_txt(
                cenhid_path=cenhid,
                center_path=center,
                dacoce_path=dacoce,
                comcen_path=comcen,
                period=period,
                cenhid_catalog_path=cenhid_catalog,
                center_catalog_path=center_catalog,
                output_path=output,
            )
        except ValueError as error:
            console.print(f"[bold red]Error:[/bold red] {error}")
            raise typer.Exit(code=1) from error

        _render_g1_txt_summary(result)
