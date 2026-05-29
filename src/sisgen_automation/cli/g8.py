from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from sisgen_automation.g8.sources import G8SourcesValidationResult, validate_g8_sources
from sisgen_automation.g8.txt import G8TxtResult, create_g8_txt
from sisgen_automation.vefame.export_dbf import VefameExportResult, export_vefame_dbf
from sisgen_automation.vefame.template import VefameTemplateResult, create_vefame_template
from sisgen_automation.vefame.template_validation import (
    VefameTemplateValidationResult,
    validate_vefame_template,
)


def _render_g8_sources_summary(console: Console, result: G8SourcesValidationResult) -> None:
    console.print("")
    console.print("[bold green]Validación de fuentes G8 completada.[/bold green]")
    console.print("")

    table = Table(title=f"Resumen fuentes G8 {result.period}")
    table.add_column("Métrica")
    table.add_column("Valor", justify="right")

    table.add_row("Registros VEFAME", str(len(result.rows)))
    table.add_row("Errores", str(len(result.errors)))
    table.add_row("Advertencias", str(len(result.warnings)))
    table.add_row("Potencia HP MW", f"{result.totals.contracted_hp_mw:.6f}")
    table.add_row("Energía HP MWh", f"{result.totals.active_hp_mwh:.3f}")
    table.add_row("Energía HFP MWh", f"{result.totals.active_hfp_mwh:.3f}")
    table.add_row("Energía total MWh", f"{result.totals.active_total_mwh:.3f}")
    table.add_row("Facturación total S/", f"{result.totals.billing_total_s:.2f}")
    table.add_row("Precio medio Ct.S/kWh", f"{result.totals.average_price_cents_kwh:.2f}")

    console.print(table)

    for issue in result.issues[:30]:
        console.print(
            f"{issue.severity.value} | fila {issue.row or 'general'} | "
            f"{issue.client_code or ''} | {issue.field or ''} | "
            f"{issue.message} | {issue.value or ''}"
        )

    if result.has_errors:
        console.print("[bold red]Las fuentes G8 no están listas para generar TXT.[/bold red]")
    else:
        console.print("[bold green]Las fuentes G8 están listas.[/bold green]")


def _render_g8_txt_summary(console: Console, result: G8TxtResult) -> None:
    console.print("")
    console.print(f"[bold green]TXT G8 generado:[/bold green] {result.output_path}")
    console.print("")

    table = Table(title=f"Resumen TXT G8 {result.period}")
    table.add_column("Métrica")
    table.add_column("Valor", justify="right")

    table.add_row("Clientes libres", str(result.rows_count))
    table.add_row("Advertencias de fuentes", str(result.warnings_count))
    table.add_row("Energía total MWh", f"{result.active_total_mwh:.3f}")
    table.add_row("Facturación total S/", f"{result.billing_total_s:.2f}")
    table.add_row("Precio medio Ct.S/kWh", f"{result.average_price_cents_kwh:.2f}")

    console.print(table)



def _render_vefame_template_summary(console: Console, result: VefameTemplateResult) -> None:
    console.print("")
    console.print(f"[bold green]Plantilla VEFAME generada:[/bold green] {result.output_path}")
    console.print("")

    table = Table(title=f"Resumen plantilla VEFAME {result.period}")
    table.add_column("Métrica")
    table.add_column("Valor", justify="right")

    table.add_row("Periodo base", result.base_period)
    table.add_row("Filas", str(result.rows))
    table.add_row("Columnas editables", "14")
    table.add_row("Columnas calculadas", "3")

    console.print(table)
    console.print(
        "[bold]Columnas editables:[/bold] "
        "NHRSPUN, NFUHOPU, NEXHOPU, NEXFUHO, NENACHO, NENACFU, "
        "NENREFA, NPRENRE, NPRPOHO, NPRPOFU, NPRPOEX, NPRENHO, NPRENFU, NFACOTR"
    )
    console.print("[bold]Columnas calculadas:[/bold] NENACTO, NFACPOT, NFACEXC")


def _render_vefame_template_validation_summary(
    console: Console,
    result: VefameTemplateValidationResult,
) -> None:
    console.print("")
    console.print(f"[bold green]Validación VEFAME:[/bold green] {result.period}")
    console.print("")

    table = Table(title=f"Resumen validación plantilla VEFAME {result.period}")
    table.add_column("Métrica")
    table.add_column("Valor", justify="right")

    table.add_row("Registros válidos", str(len(result.records)))
    table.add_row("Errores", str(result.error_count))
    table.add_row("Advertencias", str(result.warning_count))

    console.print(table)

    for issue in result.issues[:30]:
        console.print(
            f"{issue.severity.value} | fila {issue.row or 'general'} | "
            f"{issue.field or ''} | {issue.message} | {issue.value or ''}"
        )

    if result.has_errors:
        console.print("[bold red]La plantilla VEFAME no está lista para exportar.[/bold red]")
    else:
        console.print("[bold green]La plantilla VEFAME está lista para exportar.[/bold green]")


def _render_vefame_export_summary(console: Console, result: VefameExportResult) -> None:
    console.print("")
    console.print(f"[bold green]DBF VEFAME exportado:[/bold green] {result.output_path}")
    console.print("")

    table = Table(title=f"Resumen exportación VEFAME {result.period}")
    table.add_column("Métrica")
    table.add_column("Valor", justify="right")

    table.add_row("Registros originales", str(result.original_record_count))
    table.add_row("Registros agregados", str(result.appended_record_count))
    table.add_row("Registros finales", str(result.final_record_count))

    console.print(table)

def register_g8_commands(app: typer.Typer, console: Console) -> None:
    @app.command("create-vefame-template")
    def create_vefame_template_command(
        source: Path = typer.Option(
            ...,
            "--source",
            help="Ruta del VEFAME.DBF histórico fuente.",
        ),
        period: str = typer.Option(
            ...,
            "--period",
            "-p",
            help="Periodo de la plantilla en formato YYYY-MM. Ejemplo: 2025-12.",
        ),
        catalog: Path = typer.Option(
            ...,
            "--catalog",
            "-c",
            help="Ruta del catálogo local G8 en YAML.",
        ),
        base_period: Optional[str] = typer.Option(
            None,
            "--base-period",
            help="Periodo base opcional en formato YYYY-MM. Si se omite, usa el último periodo válido.",
        ),
        output: Optional[Path] = typer.Option(
            None,
            "--output",
            "-o",
            help="Ruta de la plantilla Excel generada.",
        ),
    ) -> None:
        try:
            result = create_vefame_template(
                period=period,
                source_dbf_path=source,
                catalog_path=catalog,
                base_period=base_period,
                output_path=output,
            )
        except ValueError as error:
            console.print(f"[bold red]Error:[/bold red] {error}")
            raise typer.Exit(code=1) from error

        _render_vefame_template_summary(console, result)

    @app.command("validate-vefame-template")
    def validate_vefame_template_command(
        template: Path = typer.Argument(
            ...,
            help="Ruta de la plantilla VEFAME a validar.",
        ),
        period: str = typer.Option(
            ...,
            "--period",
            "-p",
            help="Periodo esperado en formato YYYY-MM. Ejemplo: 2025-12.",
        ),
        catalog: Path = typer.Option(
            ...,
            "--catalog",
            "-c",
            help="Ruta del catálogo local G8 en YAML.",
        ),
        fail_on_errors: bool = typer.Option(
            False,
            "--fail-on-errors",
            help="Termina con código de error si se encuentran errores.",
        ),
    ) -> None:
        try:
            result = validate_vefame_template(
                template_path=template,
                period=period,
                catalog_path=catalog,
            )
        except ValueError as error:
            console.print(f"[bold red]Error:[/bold red] {error}")
            raise typer.Exit(code=1) from error

        _render_vefame_template_validation_summary(console, result)

        if fail_on_errors and result.has_errors:
            raise typer.Exit(code=1)

    @app.command("export-vefame-dbf")
    def export_vefame_dbf_command(
        source: Path = typer.Option(
            ...,
            "--source",
            help="Ruta del VEFAME.DBF histórico fuente.",
        ),
        template: Path = typer.Option(
            ...,
            "--template",
            help="Ruta de la plantilla VEFAME validada.",
        ),
        period: str = typer.Option(
            ...,
            "--period",
            "-p",
            help="Periodo a agregar en formato YYYY-MM. Ejemplo: 2025-12.",
        ),
        catalog: Path = typer.Option(
            ...,
            "--catalog",
            "-c",
            help="Ruta del catálogo local G8 en YAML.",
        ),
        output: Optional[Path] = typer.Option(
            None,
            "--output",
            "-o",
            help="Ruta del VEFAME.DBF generado.",
        ),
        allow_existing_period: bool = typer.Option(
            False,
            "--allow-existing-period",
            help="Permite exportar aunque el periodo ya exista en el DBF fuente.",
        ),
    ) -> None:
        try:
            result = export_vefame_dbf(
                source_dbf_path=source,
                template_path=template,
                period=period,
                catalog_path=catalog,
                output_path=output,
                allow_existing_period=allow_existing_period,
            )
        except ValueError as error:
            console.print(f"[bold red]Error:[/bold red] {error}")
            raise typer.Exit(code=1) from error

        _render_vefame_export_summary(console, result)

    @app.command("validate-g8-sources")
    def validate_g8_sources_command(
        vefame: Path = typer.Option(
            ...,
            "--vefame",
            help="Ruta del VEFAME.DBF.",
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
            help="Ruta del catálogo local G8 en YAML.",
        ),
        fail_on_errors: bool = typer.Option(
            False,
            "--fail-on-errors",
            help="Termina con código de error si se encuentran errores.",
        ),
    ) -> None:
        """Valida VEFAME como fuente del Formato G8."""
        try:
            result = validate_g8_sources(
                vefame_path=vefame,
                period=period,
                catalog_path=catalog,
            )
        except ValueError as error:
            console.print(f"[bold red]Error:[/bold red] {error}")
            raise typer.Exit(code=1) from error

        _render_g8_sources_summary(console, result)

        if fail_on_errors and result.has_errors:
            raise typer.Exit(code=1)

    @app.command("create-g8-txt")
    def create_g8_txt_command(
        vefame: Path = typer.Option(
            ...,
            "--vefame",
            help="Ruta del VEFAME.DBF.",
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
            help="Ruta del catálogo local G8 en YAML.",
        ),
        output: Optional[Path] = typer.Option(
            None,
            "--output",
            "-o",
            help="Ruta del TXT generado.",
        ),
    ) -> None:
        """Genera el Formato G8 en TXT."""
        try:
            result = create_g8_txt(
                vefame_path=vefame,
                period=period,
                catalog_path=catalog,
                output_path=output,
            )
        except ValueError as error:
            console.print(f"[bold red]Error:[/bold red] {error}")
            raise typer.Exit(code=1) from error

        _render_g8_txt_summary(console, result)
