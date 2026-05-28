from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from sisgen_automation.g2.sources import (
    G2SourcesValidationResult,
    validate_g2_sources,
)
from sisgen_automation.g2.txt import G2TxtResult, create_g2_txt
from sisgen_automation.g2.template import (
    VepoenTemplateResult,
    create_vepoen_template,
)
from sisgen_automation.g2.template_validation import (
    VepoenTemplateValidationResult,
    validate_vepoen_template,
)
from sisgen_automation.g2.export_dbf import (
    VepoenExportResult,
    export_vepoen_dbf,
)


def register_g2_commands(app: typer.Typer, console: Console) -> None:
    def _render_g2_sources_summary(result: G2SourcesValidationResult) -> None:
        console.print("")
        console.print(f"[bold green]Validación de fuentes G2 completada:[/bold green] {result.vepoen_path}")
        console.print("")

        table = Table(title=f"Resumen G2 {result.period}")
        table.add_column("Métrica")
        table.add_column("Valor", justify="right")

        table.add_row("Registros VEPOEN", str(len(result.rows)))
        table.add_row("Errores", str(len(result.errors)))
        table.add_row("Advertencias", str(len(result.warnings)))

        console.print(table)

        for issue in result.issues[:30]:
            console.print(
                f"{issue.severity} | {issue.source} | {issue.field or ''} | "
                f"{issue.message} | {issue.value or ''}"
            )

        if result.has_errors:
            console.print("[bold red]Las fuentes G2 no están listas.[/bold red]")
        elif result.warnings:
            console.print("[bold yellow]Las fuentes G2 tienen advertencias.[/bold yellow]")
        else:
            console.print("[bold green]Las fuentes G2 están listas.[/bold green]")

    @app.command("validate-g2-sources")
    def validate_g2_sources_command(
        vepoen: Path = typer.Option(
            ...,
            "--vepoen",
            help="Ruta del archivo VEPOEN.DBF.",
        ),
        period: str = typer.Option(
            ...,
            "--period",
            "-p",
            help="Periodo a validar en formato YYYY-MM. Ejemplo: 2026-01.",
        ),
        catalog: Path = typer.Option(
            ...,
            "--catalog",
            "-c",
            help="Ruta del catálogo local G2 en YAML.",
        ),
        fail_on_errors: bool = typer.Option(
            False,
            "--fail-on-errors",
            help="Termina con código de error si se encuentran errores.",
        ),
    ) -> None:
        """Valida VEPOEN como fuente del Formato G2."""
        try:
            result = validate_g2_sources(
                vepoen_path=vepoen,
                catalog_path=catalog,
                period=period,
            )
        except ValueError as error:
            console.print(f"[bold red]Error:[/bold red] {error}")
            raise typer.Exit(code=1) from error

        _render_g2_sources_summary(result)

        if fail_on_errors and result.has_errors:
            raise typer.Exit(code=1)

    def _render_g2_txt_summary(result: G2TxtResult) -> None:
        console.print("")
        console.print(f"[bold green]TXT G2 generado:[/bold green] {result.output_path}")
        console.print("")

        table = Table(title=f"Resumen TXT G2 {result.period}")
        table.add_column("Métrica")
        table.add_column("Valor", justify="right")

        table.add_row("Registros", str(result.row_count))
        table.add_row("Distribuidoras", str(result.distributor_count))
        table.add_row("Advertencias de fuentes", str(result.warnings_count))

        console.print(table)

        if result.warnings_count:
            console.print(
                "[bold yellow]El TXT fue generado con advertencias de fuente. "
                "Revisar validate-g2-sources.[/bold yellow]"
            )
        
    @app.command("create-g2-txt")
    def create_g2_txt_command(
        vepoen: Path = typer.Option(
            ...,
            "--vepoen",
            help="Ruta del archivo VEPOEN.DBF.",
        ),
        period: str = typer.Option(
            ...,
            "--period",
            "-p",
            help="Periodo a generar en formato YYYY-MM. Ejemplo: 2025-12.",
        ),
        catalog: Path = typer.Option(
            ...,
            "--catalog",
            "-c",
            help="Ruta del catálogo local G2 en YAML.",
        ),
        output: Optional[Path] = typer.Option(
            None,
            "--output",
            "-o",
            help="Ruta del TXT generado.",
        ),
    ) -> None:
        """Genera el Formato G2 en TXT desde VEPOEN."""
        try:
            result = create_g2_txt(
                vepoen_path=vepoen,
                period=period,
                catalog_path=catalog,
                output_path=output,
            )
        except ValueError as error:
            console.print(f"[bold red]Error:[/bold red] {error}")
            raise typer.Exit(code=1) from error

        _render_g2_txt_summary(result)

    def _render_vepoen_template_summary(result: VepoenTemplateResult) -> None:
        console.print("")
        console.print(f"[bold green]Plantilla VEPOEN generada:[/bold green] {result.output_path}")
        console.print("")

        table = Table(title=f"Resumen plantilla VEPOEN {result.period}")
        table.add_column("Métrica")
        table.add_column("Valor", justify="right")

        table.add_row("Periodo", result.period)
        table.add_row("Periodo base", result.base_period)
        table.add_row("Filas", str(result.rows))

        console.print(table)
        console.print(
            "[bold]Columnas editables:[/bold] NPRPOBA, NPRENHO, NPRENFU, "
            "NENVEHO, NENVEFU, NENVETO, NPOCOHO, NPOCOFU, "
            "NMADEHO, NMADEFU, NFACPOT, NFACENE"
        )


    def _render_vepoen_template_validation_summary(
        result: VepoenTemplateValidationResult,
    ) -> None:
        console.print("")
        console.print(f"[bold green]Validación VEPOEN:[/bold green] {result.template_path}")
        console.print("")

        table = Table(title=f"Resumen validación plantilla VEPOEN {result.period}")
        table.add_column("Métrica")
        table.add_column("Valor", justify="right")

        table.add_row("Registros válidos", str(len(result.records)))
        table.add_row("Errores", str(result.error_count))
        table.add_row("Advertencias", str(result.warning_count))

        console.print(table)

        for issue in result.issues[:30]:
            location = f"fila {issue.row}" if issue.row is not None else "general"
            field = issue.field or "-"
            severity = issue.severity.value if hasattr(issue.severity, "value") else str(issue.severity)

            console.print(
                f"{severity} | {location} | {field} | "
                f"{issue.message} | {issue.value or ''}"
            )

        if result.has_errors:
            console.print("[bold red]La plantilla VEPOEN no está lista para exportar.[/bold red]")
        elif result.warning_count:
            console.print("[bold yellow]La plantilla VEPOEN tiene advertencias.[/bold yellow]")
        else:
            console.print("[bold green]La plantilla VEPOEN está lista para exportar.[/bold green]")


    def _render_vepoen_export_summary(result: VepoenExportResult) -> None:
        console.print("")
        console.print(f"[bold green]DBF VEPOEN exportado correctamente:[/bold green] {result.output_path}")
        console.print("")

        table = Table(title="Resumen de exportación VEPOEN")
        table.add_column("Métrica")
        table.add_column("Valor", justify="right")

        table.add_row("Periodo agregado", result.period)
        table.add_row("Registros originales", str(result.original_record_count))
        table.add_row("Registros agregados", str(result.appended_record_count))
        table.add_row("Registros finales", str(result.final_record_count))

        console.print(table)

    @app.command("create-vepoen-template")
    def create_vepoen_template_command(
        period: str = typer.Option(
            ...,
            "--period",
            "-p",
            help="Periodo de la plantilla en formato YYYY-MM. Ejemplo: 2026-01.",
        ),
        source: Path = typer.Option(
            ...,
            "--source",
            "-s",
            help="Ruta del VEPOEN.DBF histórico fuente.",
        ),
        catalog: Path = typer.Option(
            ...,
            "--catalog",
            "-c",
            help="Ruta del catálogo local G2 en YAML.",
        ),
        base_period: Optional[str] = typer.Option(
            None,
            "--base-period",
            help="Periodo base para copiar barras en formato YYYY-MM. Si se omite, usa el último periodo válido.",
        ),
        output: Optional[Path] = typer.Option(
            None,
            "--output",
            "-o",
            help="Ruta del Excel generado.",
        ),
    ) -> None:
        """Genera una plantilla Excel mensual para VEPOEN."""
        try:
            result = create_vepoen_template(
                period=period,
                source_dbf_path=source,
                catalog_path=catalog,
                base_period=base_period,
                output_path=output,
            )
        except ValueError as error:
            console.print(f"[bold red]Error:[/bold red] {error}")
            raise typer.Exit(code=1) from error

        _render_vepoen_template_summary(result)


    @app.command("validate-vepoen-template")
    def validate_vepoen_template_command(
        template_path: Path = typer.Argument(
            ...,
            help="Ruta de la plantilla VEPOEN en Excel.",
        ),
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
            help="Ruta del catálogo local G2 en YAML.",
        ),
        fail_on_errors: bool = typer.Option(
            False,
            "--fail-on-errors",
            help="Termina con código de error si se encuentran errores.",
        ),
    ) -> None:
        """Valida una plantilla mensual VEPOEN antes de generar DBF."""
        try:
            result = validate_vepoen_template(
                template_path=template_path,
                period=period,
                catalog_path=catalog,
            )
        except ValueError as error:
            console.print(f"[bold red]Error:[/bold red] {error}")
            raise typer.Exit(code=1) from error

        _render_vepoen_template_validation_summary(result)

        if fail_on_errors and result.has_errors:
            raise typer.Exit(code=1)


    @app.command("export-vepoen-dbf")
    def export_vepoen_dbf_command(
        source_dbf_path: Path = typer.Argument(
            ...,
            help="Ruta del VEPOEN.DBF histórico fuente.",
        ),
        template_path: Path = typer.Argument(
            ...,
            help="Ruta de la plantilla VEPOEN validada.",
        ),
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
            help="Ruta del catálogo local G2 en YAML.",
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
        """Genera un nuevo VEPOEN.DBF agregando el periodo mensual validado."""
        try:
            result = export_vepoen_dbf(
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

        _render_vepoen_export_summary(result)
