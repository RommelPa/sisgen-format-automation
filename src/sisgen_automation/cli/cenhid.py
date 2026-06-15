from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from sisgen_automation.cenhid.validate import (
    CenhidValidationResult,
    validate_cenhid_dbf,
    write_validation_markdown,
)
from sisgen_automation.cenhid.template import create_cenhid_template
from sisgen_automation.cenhid.template_validation import (
    CenhidTemplateValidationResult,
    validate_cenhid_template,
    write_template_validation_markdown,
)
from sisgen_automation.cenhid.export_dbf import CenhidExportResult, export_cenhid_dbf


def register_cenhid_commands(app: typer.Typer, console: Console) -> None:
    def _render_cenhid_validation_summary(
        result: CenhidValidationResult,
        output_path: Path,
    ) -> None:
        console.print("")
        console.print(f"[bold green]Validación CENHID generada:[/bold green] {output_path}")
        console.print("")

        table = Table(title=f"Resumen de validación {result.dbf_path.name}")
        table.add_column("Métrica")
        table.add_column("Valor", justify="right")

        table.add_row("Registros leídos", str(result.record_count))
        table.add_row("Unidades en catálogo", str(result.catalog_unit_count))
        table.add_row("Periodos válidos", str(len(result.period_counts)))
        table.add_row("Errores", str(len(result.errors)))
        table.add_row("Advertencias", str(len(result.warnings)))

        console.print(table)

        if result.has_errors:
            console.print("[bold red]La validación encontró errores.[/bold red]")
        elif result.warnings:
            console.print("[bold yellow]La validación encontró advertencias.[/bold yellow]")
        else:
            console.print("[bold green]La validación no encontró observaciones.[/bold green]")


    @app.command("validate-cenhid")
    def validate_cenhid(
        dbf_path: Path = typer.Argument(..., help="Ruta del archivo CENHID.DBF a validar."),
        catalog: Path = typer.Option(
            ...,
            "--catalog",
            "-c",
            help="Ruta del catálogo local CENHID en YAML.",
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
            help="Termina con código de error si se encuentran errores de validación.",
        ),
    ) -> None:
        """Valida CENHID contra estructura, catálogo y reglas de negocio."""
        result = validate_cenhid_dbf(dbf_path=dbf_path, catalog_path=catalog)

        output_path = output
        if output_path is None:
            output_path = Path("reports") / f"{dbf_path.stem}_validation.md"

        write_validation_markdown(result, output_path)
        _render_cenhid_validation_summary(result, output_path)

        if fail_on_errors and result.has_errors:
            raise typer.Exit(code=1)

    @app.command("create-cenhid-template")
    def create_cenhid_template_command(
        period: str = typer.Option(
            ...,
            "--period",
            "-p",
            help="Periodo de la plantilla en formato YYYY-MM. Ejemplo: 2026-01.",
        ),
        catalog: Optional[Path] = typer.Option(
            None,
            "--catalog",
            "-c",
            help="Ruta del catálogo local CENHID en YAML.",
        ),
        catalog_db: Optional[Path] = typer.Option(
            None,
            "--catalog-db",
            help="Ruta de la base SQLite local de catalogos.",
        ),
        output: Optional[Path] = typer.Option(
            None,
            "--output",
            "-o",
            help="Ruta del Excel generado.",
        ),
    ) -> None:
        """Genera una plantilla Excel mensual para CENHID."""
        try:
            output_path = create_cenhid_template(
                period=period,
                catalog_path=catalog,
                output_path=output,
                catalog_db_path=catalog_db,
            )
        except ValueError as error:
            console.print(f"[bold red]Error:[/bold red] {error}")
            raise typer.Exit(code=1) from error

        console.print("")
        console.print(f"[bold green]Plantilla CENHID generada:[/bold green] {output_path}")
        console.print("")
        console.print("[bold]Columnas editables:[/bold] CESTGRU, NHORPUN, NFUHOPU, CHRSMAN, CHRSOPE, CHRSSAL")
        console.print("[bold]Columna calculada:[/bold] NTOPRBR = NHORPUN + NFUHOPU")

    def _render_cenhid_template_validation_summary(
        result: CenhidTemplateValidationResult,
        output_path: Path,
    ) -> None:
        console.print("")
        console.print(f"[bold green]Validación de plantilla CENHID generada:[/bold green] {output_path}")
        console.print("")

        table = Table(title=f"Resumen de validación {result.template_path.name}")
        table.add_column("Métrica")
        table.add_column("Valor", justify="right")

        table.add_row("Periodo", result.period)
        table.add_row("Filas leídas", str(result.rows_read))
        table.add_row("Unidades esperadas", str(result.expected_units))
        table.add_row("Unidades válidas", str(result.valid_units))
        table.add_row("Errores", str(len(result.errors)))
        table.add_row("Advertencias", str(len(result.warnings)))

        console.print(table)

        if result.has_errors:
            console.print("[bold red]La plantilla no está lista para exportar.[/bold red]")
        elif result.warnings:
            console.print("[bold yellow]La plantilla tiene advertencias. Revisar antes de exportar.[/bold yellow]")
        else:
            console.print("[bold green]La plantilla está lista para exportar.[/bold green]")


    @app.command("validate-cenhid-template")
    def validate_cenhid_template_command(
        template_path: Path = typer.Argument(..., help="Ruta de la plantilla CENHID en Excel."),
        period: str = typer.Option(
            ...,
            "--period",
            "-p",
            help="Periodo esperado en formato YYYY-MM. Ejemplo: 2026-01.",
        ),
        catalog: Path = typer.Option(
            ...,
            "--catalog",
            "-c",
            help="Ruta del catálogo local CENHID en YAML.",
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
        """Valida una plantilla mensual CENHID antes de generar DBF."""
        try:
            result = validate_cenhid_template(
                template_path=template_path,
                period=period,
                catalog_path=catalog,
            )
        except ValueError as error:
            console.print(f"[bold red]Error:[/bold red] {error}")
            raise typer.Exit(code=1) from error

        output_path = output
        if output_path is None:
            output_path = Path("reports") / f"{template_path.stem}_validation.md"

        write_template_validation_markdown(result, output_path)
        _render_cenhid_template_validation_summary(result, output_path)

        if fail_on_errors and result.has_errors:
            raise typer.Exit(code=1)
    
    def _render_cenhid_export_summary(result: CenhidExportResult) -> None:
        console.print("")
        console.print(f"[bold green]DBF CENHID exportado correctamente:[/bold green] {result.output_path}")
        console.print("")

        table = Table(title="Resumen de exportación CENHID")
        table.add_column("Métrica")
        table.add_column("Valor", justify="right")

        table.add_row("Periodo agregado", result.period)
        table.add_row("Registros originales", str(result.original_record_count))
        table.add_row("Registros agregados", str(result.appended_record_count))
        table.add_row("Registros finales", str(result.final_record_count))

        console.print(table)


    @app.command("export-cenhid-dbf")
    def export_cenhid_dbf_command(
        source_dbf_path: Path = typer.Argument(..., help="Ruta del CENHID.DBF histórico fuente."),
        template_path: Path = typer.Argument(..., help="Ruta de la plantilla CENHID validada."),
        period: str = typer.Option(
            ...,
            "--period",
            "-p",
            help="Periodo a agregar en formato YYYY-MM. Ejemplo: 2026-01.",
        ),
        catalog: Path = typer.Option(
            ...,
            "--catalog",
            "-c",
            help="Ruta del catálogo local CENHID en YAML.",
        ),
        output: Optional[Path] = typer.Option(
            None,
            "--output",
            "-o",
            help="Ruta del DBF generado.",
        ),
        allow_existing_period: bool = typer.Option(
            False,
            "--allow-existing-period",
            help="Permite exportar aunque el periodo ya exista en el DBF fuente.",
        ),
    ) -> None:
        """Genera un nuevo CENHID.DBF agregando el periodo mensual validado."""
        try:
            result = export_cenhid_dbf(
                source_dbf_path=source_dbf_path,
                template_path=template_path,
                period=period,
                catalog_path=catalog,
                output_path=output,
                allow_existing_period=allow_existing_period,
            )
        except ValueError as error:
            console.print(f"[bold red]Error:[/bold red] {error}")
            raise typer.Exit(code=1) from error

        _render_cenhid_export_summary(result)
