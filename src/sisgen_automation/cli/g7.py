from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from sisgen_automation.comene.export_dbf import ComeneExportResult, export_comene_dbf
from sisgen_automation.comene.template import ComeneTemplateResult, create_comene_template
from sisgen_automation.comene.template_validation import (
    EnergyTemplateValidationResult as ComeneTemplateValidationResult,
)
from sisgen_automation.comene.template_validation import validate_comene_template
from sisgen_automation.comnet.export_dbf import ComnetExportResult, export_comnet_dbf
from sisgen_automation.comnet.template import ComnetTemplateResult, create_comnet_template
from sisgen_automation.comnet.template_validation import (
    ComnetTemplateValidationResult,
)
from sisgen_automation.comnet.template_validation import validate_comnet_template
from sisgen_automation.g7.sources import G7SourcesValidationResult, validate_g7_sources
from sisgen_automation.g7.txt import G7TxtResult, create_g7_txt
from sisgen_automation.traene.export_dbf import TraeneExportResult, export_traene_dbf
from sisgen_automation.traene.template import TraeneTemplateResult, create_traene_template
from sisgen_automation.traene.template_validation import (
    TraeneTemplateValidationResult,
)
from sisgen_automation.traene.template_validation import validate_traene_template
from sisgen_automation.valene.export_dbf import ValeneExportResult, export_valene_dbf
from sisgen_automation.valene.template import ValeneTemplateResult, create_valene_template
from sisgen_automation.valene.template_validation import (
    ValeneTemplateValidationResult,
)
from sisgen_automation.valene.template_validation import validate_valene_template
from sisgen_automation.venene.export_dbf import VeneneExportResult, export_venene_dbf
from sisgen_automation.venene.template import VeneneTemplateResult, create_venene_template
from sisgen_automation.venene.template_validation import (
    EnergyTemplateValidationResult as VeneneTemplateValidationResult,
)
from sisgen_automation.venene.template_validation import validate_venene_template


def _render_g7_template_summary(
    console: Console,
    comene_result: ComeneTemplateResult,
    venene_result: VeneneTemplateResult,
    comnet_result: ComnetTemplateResult,
    traene_result: TraeneTemplateResult,
    valene_result: ValeneTemplateResult,
) -> None:
    console.print("")
    console.print("[bold green]Plantillas G7 generadas correctamente.[/bold green]")
    console.print("")

    table = Table(title=f"Resumen plantillas G7 {comene_result.period}")
    table.add_column("Plantilla")
    table.add_column("Ruta")
    table.add_column("Filas", justify="right")

    table.add_row("COMENE", str(comene_result.output_path), str(comene_result.rows))
    table.add_row("VENENE", str(venene_result.output_path), str(venene_result.rows))
    table.add_row("COMNET", str(comnet_result.output_path), str(comnet_result.rows))
    table.add_row("TRAENE", str(traene_result.output_path), str(traene_result.rows))
    table.add_row("VALENE", str(valene_result.output_path), str(valene_result.rows))

    console.print(table)
    console.print(
        "[bold]Columnas editables COMENE/VENENE:[/bold] "
        "NENHOPU, NENFUHO, NVAHOPU, NVAFUHO"
    )
    console.print("[bold]Columnas calculadas COMENE/VENENE:[/bold] NENETOT, NVALTOT")
    console.print(
        "[bold]Columnas editables COMNET/TRAENE/VALENE:[/bold] "
        "NCOMNET, NTRAPOT, NVALTRA"
    )


def _render_g7_template_validation_summary(
    console: Console,
    comene_result: ComeneTemplateValidationResult,
    venene_result: VeneneTemplateValidationResult,
    comnet_result: ComnetTemplateValidationResult,
    traene_result: TraeneTemplateValidationResult,
    valene_result: ValeneTemplateValidationResult,
) -> None:
    console.print("")
    console.print("[bold green]Validación de plantillas G7 completada.[/bold green]")
    console.print("")

    table = Table(title=f"Resumen validación plantillas G7 {comene_result.period}")
    table.add_column("Plantilla")
    table.add_column("Registros válidos", justify="right")
    table.add_column("Errores", justify="right")
    table.add_column("Advertencias", justify="right")

    results = [
        ("COMENE", comene_result),
        ("VENENE", venene_result),
        ("COMNET", comnet_result),
        ("TRAENE", traene_result),
        ("VALENE", valene_result),
    ]

    for name, result in results:
        table.add_row(
            name,
            str(len(result.records)),
            str(result.error_count),
            str(result.warning_count),
        )

    console.print(table)

    for name, result in results:
        for issue in result.issues[:20]:
            console.print(
                f"{issue.severity.value} | {name} | fila {issue.row or 'general'} | "
                f"{issue.field or ''} | {issue.message} | {issue.value or ''}"
            )

    if any(result.has_errors for _, result in results):
        console.print("[bold red]Las plantillas G7 no están listas para exportar.[/bold red]")
    else:
        console.print("[bold green]Las plantillas G7 están listas para exportar.[/bold green]")


def _render_g7_export_summary(
    console: Console,
    comene_result: ComeneExportResult,
    venene_result: VeneneExportResult,
    comnet_result: ComnetExportResult,
    traene_result: TraeneExportResult,
    valene_result: ValeneExportResult,
) -> None:
    console.print("")
    console.print("[bold green]DBF G7 exportados correctamente.[/bold green]")
    console.print("")

    table = Table(title=f"Resumen exportación G7 {comene_result.period}")
    table.add_column("DBF")
    table.add_column("Ruta")
    table.add_column("Originales", justify="right")
    table.add_column("Agregados", justify="right")
    table.add_column("Finales", justify="right")

    results = [
        ("COMENE", comene_result),
        ("VENENE", venene_result),
        ("COMNET", comnet_result),
        ("TRAENE", traene_result),
        ("VALENE", valene_result),
    ]

    for name, result in results:
        table.add_row(
            name,
            str(result.output_path),
            str(result.original_record_count),
            str(result.appended_record_count),
            str(result.final_record_count),
        )

    console.print(table)


def _render_g7_sources_summary(console: Console, result: G7SourcesValidationResult) -> None:
    console.print("")
    console.print("[bold green]Validación de fuentes G7 completada.[/bold green]")
    console.print("")

    table = Table(title=f"Resumen fuentes G7 {result.period}")
    table.add_column("Métrica")
    table.add_column("Valor", justify="right")

    table.add_row("Compras energía COMENE", str(len(result.purchases)))
    table.add_row("Ventas energía VENENE", str(len(result.sales)))
    table.add_row("Compromisos netos COMNET", str(len(result.net_commitments)))
    table.add_row("Transferencias potencia TRAENE", str(len(result.power_transfers)))
    table.add_row("Valorizaciones VALENE", str(len(result.transfer_valuations)))
    table.add_row("Errores", str(len(result.errors)))
    table.add_row("Advertencias", str(len(result.warnings)))

    console.print(table)

    for issue in result.issues[:30]:
        console.print(
            f"{issue.severity.value} | {issue.section} | {issue.source} | "
            f"{issue.field or ''} | {issue.message} | {issue.value or ''}"
        )

    if result.has_errors:
        console.print("[bold red]Las fuentes G7 no están listas para generar TXT.[/bold red]")
    else:
        console.print("[bold green]Las fuentes G7 están listas.[/bold green]")


def _render_g7_txt_summary(console: Console, result: G7TxtResult) -> None:
    console.print("")
    console.print(f"[bold green]TXT G7 generado:[/bold green] {result.output_path}")
    console.print("")

    table = Table(title=f"Resumen TXT G7 {result.period}")
    table.add_column("Métrica")
    table.add_column("Valor", justify="right")

    table.add_row("Compras energía", str(result.purchases_count))
    table.add_row("Ventas energía", str(result.sales_count))
    table.add_row("Compromisos netos", str(result.net_commitments_count))
    table.add_row("Transferencias potencia", str(result.power_transfers_count))
    table.add_row("Valorizaciones", str(result.transfer_valuations_count))
    table.add_row("Advertencias de fuentes", str(result.warnings_count))

    console.print(table)


def register_g7_commands(app: typer.Typer, console: Console) -> None:
    @app.command("create-g7-templates")
    def create_g7_templates_command(
        period: str = typer.Option(
            ...,
            "--period",
            "-p",
            help="Periodo de las plantillas en formato YYYY-MM. Ejemplo: 2026-01.",
        ),
        catalog: Path = typer.Option(
            ...,
            "--catalog",
            "-c",
            help="Ruta del catálogo local G7 en YAML.",
        ),
        output_dir: Path = typer.Option(
            Path("reports/templates"),
            "--output-dir",
            help="Carpeta donde se generarán las plantillas.",
        ),
    ) -> None:
        """Genera las plantillas Excel COMENE, VENENE, COMNET, TRAENE y VALENE para G7."""
        period_label = period.replace("-", "_")

        try:
            comene_result = create_comene_template(
                period=period,
                catalog_path=catalog,
                output_path=output_dir / f"COMENE_{period_label}_template.xlsx",
            )
            venene_result = create_venene_template(
                period=period,
                catalog_path=catalog,
                output_path=output_dir / f"VENENE_{period_label}_template.xlsx",
            )
            comnet_result = create_comnet_template(
                period=period,
                catalog_path=catalog,
                output_path=output_dir / f"COMNET_{period_label}_template.xlsx",
            )
            traene_result = create_traene_template(
                period=period,
                catalog_path=catalog,
                output_path=output_dir / f"TRAENE_{period_label}_template.xlsx",
            )
            valene_result = create_valene_template(
                period=period,
                catalog_path=catalog,
                output_path=output_dir / f"VALENE_{period_label}_template.xlsx",
            )
        except ValueError as error:
            console.print(f"[bold red]Error:[/bold red] {error}")
            raise typer.Exit(code=1) from error

        _render_g7_template_summary(
            console,
            comene_result,
            venene_result,
            comnet_result,
            traene_result,
            valene_result,
        )

    @app.command("validate-g7-templates")
    def validate_g7_templates_command(
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
            help="Ruta del catálogo local G7 en YAML.",
        ),
        comene_template: Path = typer.Option(
            ...,
            "--comene-template",
            help="Ruta de la plantilla COMENE.",
        ),
        venene_template: Path = typer.Option(
            ...,
            "--venene-template",
            help="Ruta de la plantilla VENENE.",
        ),
        comnet_template: Path = typer.Option(
            ...,
            "--comnet-template",
            help="Ruta de la plantilla COMNET.",
        ),
        traene_template: Path = typer.Option(
            ...,
            "--traene-template",
            help="Ruta de la plantilla TRAENE.",
        ),
        valene_template: Path = typer.Option(
            ...,
            "--valene-template",
            help="Ruta de la plantilla VALENE.",
        ),
        fail_on_errors: bool = typer.Option(
            False,
            "--fail-on-errors",
            help="Termina con código de error si se encuentran errores.",
        ),
    ) -> None:
        """Valida las plantillas G7 antes de exportar DBF."""
        try:
            comene_result = validate_comene_template(
                template_path=comene_template,
                period=period,
                catalog_path=catalog,
            )
            venene_result = validate_venene_template(
                template_path=venene_template,
                period=period,
                catalog_path=catalog,
            )
            comnet_result = validate_comnet_template(
                template_path=comnet_template,
                period=period,
                catalog_path=catalog,
            )
            traene_result = validate_traene_template(
                template_path=traene_template,
                period=period,
                catalog_path=catalog,
            )
            valene_result = validate_valene_template(
                template_path=valene_template,
                period=period,
                catalog_path=catalog,
            )
        except ValueError as error:
            console.print(f"[bold red]Error:[/bold red] {error}")
            raise typer.Exit(code=1) from error

        _render_g7_template_validation_summary(
            console,
            comene_result,
            venene_result,
            comnet_result,
            traene_result,
            valene_result,
        )

        if fail_on_errors and any(
            result.has_errors
            for result in [
                comene_result,
                venene_result,
                comnet_result,
                traene_result,
                valene_result,
            ]
        ):
            raise typer.Exit(code=1)

    @app.command("export-g7-dbf")
    def export_g7_dbf_command(
        comene_source: Path = typer.Option(
            ...,
            "--comene-source",
            help="Ruta del COMENE.DBF histórico fuente.",
        ),
        venene_source: Path = typer.Option(
            ...,
            "--venene-source",
            help="Ruta del VENENE.DBF histórico fuente.",
        ),
        comnet_source: Path = typer.Option(
            ...,
            "--comnet-source",
            help="Ruta del COMNET.DBF histórico fuente.",
        ),
        traene_source: Path = typer.Option(
            ...,
            "--traene-source",
            help="Ruta del TRAENE.DBF histórico fuente.",
        ),
        valene_source: Path = typer.Option(
            ...,
            "--valene-source",
            help="Ruta del VALENE.DBF histórico fuente.",
        ),
        comene_template: Path = typer.Option(
            ...,
            "--comene-template",
            help="Ruta de la plantilla COMENE validada.",
        ),
        venene_template: Path = typer.Option(
            ...,
            "--venene-template",
            help="Ruta de la plantilla VENENE validada.",
        ),
        comnet_template: Path = typer.Option(
            ...,
            "--comnet-template",
            help="Ruta de la plantilla COMNET validada.",
        ),
        traene_template: Path = typer.Option(
            ...,
            "--traene-template",
            help="Ruta de la plantilla TRAENE validada.",
        ),
        valene_template: Path = typer.Option(
            ...,
            "--valene-template",
            help="Ruta de la plantilla VALENE validada.",
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
            help="Ruta del catálogo local G7 en YAML.",
        ),
        output_dir: Path = typer.Option(
            Path("reports/dbf"),
            "--output-dir",
            help="Carpeta base donde se generarán los DBF por periodo.",
        ),
        allow_existing_period: bool = typer.Option(
            False,
            "--allow-existing-period",
            help="Permite exportar aunque el periodo ya exista en los DBF fuente.",
        ),
    ) -> None:
        """Genera los cinco DBF G7 agregando el periodo mensual validado."""
        period_output_dir = output_dir / period

        try:
            comene_result = export_comene_dbf(
                source_dbf_path=comene_source,
                template_path=comene_template,
                period=period,
                catalog_path=catalog,
                output_path=period_output_dir / "COMENE.DBF",
                allow_existing_period=allow_existing_period,
            )
            venene_result = export_venene_dbf(
                source_dbf_path=venene_source,
                template_path=venene_template,
                period=period,
                catalog_path=catalog,
                output_path=period_output_dir / "VENENE.DBF",
                allow_existing_period=allow_existing_period,
            )
            comnet_result = export_comnet_dbf(
                source_dbf_path=comnet_source,
                template_path=comnet_template,
                period=period,
                catalog_path=catalog,
                output_path=period_output_dir / "COMNET.DBF",
                allow_existing_period=allow_existing_period,
            )
            traene_result = export_traene_dbf(
                source_dbf_path=traene_source,
                template_path=traene_template,
                period=period,
                catalog_path=catalog,
                output_path=period_output_dir / "TRAENE.DBF",
                allow_existing_period=allow_existing_period,
            )
            valene_result = export_valene_dbf(
                source_dbf_path=valene_source,
                template_path=valene_template,
                period=period,
                catalog_path=catalog,
                output_path=period_output_dir / "VALENE.DBF",
                allow_existing_period=allow_existing_period,
            )
        except ValueError as error:
            console.print(f"[bold red]Error:[/bold red] {error}")
            raise typer.Exit(code=1) from error

        _render_g7_export_summary(
            console,
            comene_result,
            venene_result,
            comnet_result,
            traene_result,
            valene_result,
        )

    @app.command("validate-g7-sources")
    def validate_g7_sources_command(
        comene: Path = typer.Option(
            ...,
            "--comene",
            help="Ruta del COMENE.DBF.",
        ),
        venene: Path = typer.Option(
            ...,
            "--venene",
            help="Ruta del VENENE.DBF.",
        ),
        comnet: Path = typer.Option(
            ...,
            "--comnet",
            help="Ruta del COMNET.DBF.",
        ),
        traene: Path = typer.Option(
            ...,
            "--traene",
            help="Ruta del TRAENE.DBF.",
        ),
        valene: Path = typer.Option(
            ...,
            "--valene",
            help="Ruta del VALENE.DBF.",
        ),
        period: str = typer.Option(
            ...,
            "--period",
            "-p",
            help="Periodo a validar en formato YYYY-MM. Ejemplo: 2026-01.",
        ),
        catalog: Optional[Path] = typer.Option(
            None,
            "--catalog",
            "-c",
            help="Ruta del catalogo local G7 en YAML.",
        ),
        catalog_db: Optional[Path] = typer.Option(
            None,
            "--catalog-db",
            help="Ruta de la base SQLite de catalogos.",
        ),
        fail_on_errors: bool = typer.Option(
            False,
            "--fail-on-errors",
            help="Termina con c?digo de error si se encuentran errores.",
        ),
    ) -> None:
        """Valida los cinco DBF fuente del Formato G7."""
        try:
            result = validate_g7_sources(
                comene_path=comene,
                venene_path=venene,
                comnet_path=comnet,
                traene_path=traene,
                valene_path=valene,
                period=period,
                catalog_path=catalog,
                catalog_db_path=catalog_db,
            )
        except ValueError as error:
            console.print(f"[bold red]Error:[/bold red] {error}")
            raise typer.Exit(code=1) from error

        _render_g7_sources_summary(console, result)

        if fail_on_errors and result.has_errors:
            raise typer.Exit(code=1)


    @app.command("create-g7-txt")
    def create_g7_txt_command(
        comene: Path = typer.Option(
            ...,
            "--comene",
            help="Ruta del COMENE.DBF.",
        ),
        venene: Path = typer.Option(
            ...,
            "--venene",
            help="Ruta del VENENE.DBF.",
        ),
        comnet: Path = typer.Option(
            ...,
            "--comnet",
            help="Ruta del COMNET.DBF.",
        ),
        traene: Path = typer.Option(
            ...,
            "--traene",
            help="Ruta del TRAENE.DBF.",
        ),
        valene: Path = typer.Option(
            ...,
            "--valene",
            help="Ruta del VALENE.DBF.",
        ),
        period: str = typer.Option(
            ...,
            "--period",
            "-p",
            help="Periodo a generar en formato YYYY-MM. Ejemplo: 2026-01.",
        ),
        catalog: Optional[Path] = typer.Option(
            None,
            "--catalog",
            "-c",
            help="Ruta del catalogo local G7 en YAML.",
        ),
        catalog_db: Optional[Path] = typer.Option(
            None,
            "--catalog-db",
            help="Ruta de la base SQLite de catalogos.",
        ),
        output: Optional[Path] = typer.Option(
            None,
            "--output",
            "-o",
            help="Ruta del TXT generado.",
        ),
    ) -> None:
        """Genera el Formato G7 en TXT."""
        try:
            result = create_g7_txt(
                comene_path=comene,
                venene_path=venene,
                comnet_path=comnet,
                traene_path=traene,
                valene_path=valene,
                period=period,
                catalog_path=catalog,
                catalog_db_path=catalog_db,
                output_path=output,
            )
        except ValueError as error:
            console.print(f"[bold red]Error:[/bold red] {error}")
            raise typer.Exit(code=1) from error

        _render_g7_txt_summary(console, result)
