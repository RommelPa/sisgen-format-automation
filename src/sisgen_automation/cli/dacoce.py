from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from sisgen_automation.dacoce.validate import (
    DacoceValidationResult,
    validate_dacoce_dbf,
    write_dacoce_validation_markdown,
)
from sisgen_automation.dacoce.template import DacoceTemplateResult, create_dacoce_template
from sisgen_automation.dacoce.template_validation import (
    DacoceTemplateValidationResult,
    validate_dacoce_template,
    write_dacoce_template_validation_markdown,
)
from sisgen_automation.dacoce.export_dbf import DacoceExportResult, export_dacoce_dbf


def register_dacoce_commands(app: typer.Typer, console: Console) -> None:
    def _render_dacoce_validation_summary(
        result: DacoceValidationResult,
        output_path: Path,
    ) -> None:
        console.print("")
        console.print(f"[bold green]Validación DACOCE generada:[/bold green] {output_path}")
        console.print("")

        table = Table(title=f"Resumen de validación {result.dbf_path.name}")
        table.add_column("Métrica")
        table.add_column("Valor", justify="right")

        table.add_row("Registros leídos", str(result.record_count))
        table.add_row("Registros hidroeléctricos", str(result.hydro_record_count))
        table.add_row("Registros termoeléctricos", str(result.thermal_record_count))
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


    @app.command("validate-dacoce")
    def validate_dacoce(
        dbf_path: Path = typer.Argument(..., help="Ruta del archivo DACOCE.DBF a validar."),
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
        """Valida DACOCE contra estructura y reglas básicas de negocio."""
        result = validate_dacoce_dbf(dbf_path)

        output_path = output
        if output_path is None:
            output_path = Path("reports") / f"{dbf_path.stem}_validation.md"

        write_dacoce_validation_markdown(result, output_path)
        _render_dacoce_validation_summary(result, output_path)

        if fail_on_errors and result.has_errors:
            raise typer.Exit(code=1)

    def _render_dacoce_template_summary(result: DacoceTemplateResult) -> None:
        console.print("")
        console.print(f"[bold green]Plantilla DACOCE generada:[/bold green] {result.output_path}")
        console.print("")

        table = Table(title=f"Resumen plantilla DACOCE {result.period}")
        table.add_column("Métrica")
        table.add_column("Valor", justify="right")

        table.add_row("Periodo", result.period)
        table.add_row("Periodo base", result.base_period)
        table.add_row("Filas", str(result.row_count))

        console.print(table)
        console.print("[bold]Columnas editables:[/bold] NCONPRO, NPRONET, NMAXDEM")


    @app.command("create-dacoce-template")
    def create_dacoce_template_command(
        period: str = typer.Option(
            ...,
            "--period",
            "-p",
            help="Periodo de la plantilla en formato YYYY-MM. Ejemplo: 2026-01.",
        ),
        source: Optional[Path] = typer.Option(
            None,
            "--source",
            "-s",
            help="Ruta del DACOCE.DBF histórico fuente.",
        ),
        cenhid_catalog: Optional[Path] = typer.Option(
            None,
            "--cenhid-catalog",
            help="Ruta del catálogo local CENHID en YAML.",
        ),
        center_catalog: Optional[Path] = typer.Option(
            None,
            "--center-catalog",
            help="Ruta del catálogo local CENTER en YAML.",
        ),
        base_period: Optional[str] = typer.Option(
            None,
            "--base-period",
            help="Periodo base para copiar centrales en formato YYYY-MM. Si se omite, usa el último periodo válido.",
        ),
        output: Optional[Path] = typer.Option(
            None,
            "--output",
            "-o",
            help="Ruta del Excel generado.",
        ),
    ) -> None:
        """Genera una plantilla Excel mensual para DACOCE."""
        try:
            result = create_dacoce_template(
                period=period,
                source_dbf_path=source,
                base_period=base_period,
                output_path=output,
                cenhid_catalog_path=cenhid_catalog,
                center_catalog_path=center_catalog,
            )
        except ValueError as error:
            console.print(f"[bold red]Error:[/bold red] {error}")
            raise typer.Exit(code=1) from error

        _render_dacoce_template_summary(result)

    def _render_dacoce_template_validation_summary(
        result: DacoceTemplateValidationResult,
        output_path: Path,
    ) -> None:
        console.print("")
        console.print(f"[bold green]Validación de plantilla DACOCE generada:[/bold green] {output_path}")
        console.print("")

        table = Table(title=f"Resumen validación plantilla DACOCE {result.period}")
        table.add_column("Métrica")
        table.add_column("Valor", justify="right")

        table.add_row("Filas leídas", str(result.rows_read))
        table.add_row("Filas hidroeléctricas", str(result.hydro_rows))
        table.add_row("Filas termoeléctricas", str(result.thermal_rows))
        table.add_row("Errores", str(len(result.errors)))
        table.add_row("Advertencias", str(len(result.warnings)))

        console.print(table)

        if result.has_errors:
            console.print("[bold red]La plantilla DACOCE no está lista para exportar.[/bold red]")
        elif result.warnings:
            console.print("[bold yellow]La plantilla DACOCE tiene advertencias.[/bold yellow]")
        else:
            console.print("[bold green]La plantilla DACOCE está lista para exportar.[/bold green]")


    @app.command("validate-dacoce-template")
    def validate_dacoce_template_command(
        template_path: Path = typer.Argument(..., help="Ruta de la plantilla DACOCE en Excel."),
        period: str = typer.Option(
            ...,
            "--period",
            "-p",
            help="Periodo esperado en formato YYYY-MM. Ejemplo: 2026-01.",
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
        """Valida una plantilla mensual DACOCE antes de generar DBF."""
        try:
            result = validate_dacoce_template(
                template_path=template_path,
                period=period,
            )
        except ValueError as error:
            console.print(f"[bold red]Error:[/bold red] {error}")
            raise typer.Exit(code=1) from error

        output_path = output
        if output_path is None:
            output_path = Path("reports") / f"{template_path.stem}_validation.md"

        write_dacoce_template_validation_markdown(result, output_path)
        _render_dacoce_template_validation_summary(result, output_path)

        if fail_on_errors and result.has_errors:
            raise typer.Exit(code=1)
    
    def _render_dacoce_export_summary(result: DacoceExportResult) -> None:
        console.print("")
        console.print(f"[bold green]DBF DACOCE exportado correctamente:[/bold green] {result.output_path}")
        console.print("")

        table = Table(title="Resumen de exportación DACOCE")
        table.add_column("Métrica")
        table.add_column("Valor", justify="right")

        table.add_row("Periodo agregado", result.period)
        table.add_row("Registros originales", str(result.original_record_count))
        table.add_row("Registros agregados", str(result.appended_record_count))
        table.add_row("Registros finales", str(result.final_record_count))

        console.print(table)


    @app.command("export-dacoce-dbf")
    def export_dacoce_dbf_command(
        source_dbf_path: Path = typer.Argument(..., help="Ruta del DACOCE.DBF histórico fuente."),
        template_path: Path = typer.Argument(..., help="Ruta de la plantilla DACOCE validada."),
        period: str = typer.Option(
            ...,
            "--period",
            "-p",
            help="Periodo a agregar en formato YYYY-MM. Ejemplo: 2026-01.",
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
        """Genera un nuevo DACOCE.DBF agregando el periodo mensual validado."""
        try:
            result = export_dacoce_dbf(
                source_dbf_path=source_dbf_path,
                template_path=template_path,
                period=period,
                output_path=output,
                allow_existing_period=allow_existing_period,
            )
        except ValueError as error:
            console.print(f"[bold red]Error:[/bold red] {error}")
            raise typer.Exit(code=1) from error

        _render_dacoce_export_summary(result)
