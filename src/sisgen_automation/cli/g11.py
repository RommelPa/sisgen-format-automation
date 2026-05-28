from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from sisgen_automation.cacehi.template import (
    CacehiTemplateResult,
    create_cacehi_template,
)
from sisgen_automation.cacehi.template_validation import (
    CacehiTemplateValidationResult,
    validate_cacehi_template,
)
from sisgen_automation.cacehi.export_dbf import (
    CacehiExportResult,
    export_cacehi_dbf,
)

from sisgen_automation.cacete.template import (
    CaceteTemplateResult,
    create_cacete_template,
)
from sisgen_automation.cacete.template_validation import (
    CaceteTemplateValidationResult,
    validate_cacete_template,
)
from sisgen_automation.cacete.export_dbf import (
    CaceteExportResult,
    export_cacete_dbf,
)

from sisgen_automation.g11.sources import (
    G11SourcesValidationResult,
    validate_g11_sources,
)
from sisgen_automation.g11.txt import G11TxtResult, create_g11_txt


def register_g11_commands(app: typer.Typer, console: Console) -> None:
    def _render_g11_template_summary(
        cacehi_result: CacehiTemplateResult,
        cacete_result: CaceteTemplateResult,
    ) -> None:
        console.print("")
        console.print("[bold green]Plantillas G11 generadas correctamente.[/bold green]")
        console.print("")

        table = Table(title=f"Resumen plantillas G11 {cacehi_result.period}")
        table.add_column("Plantilla")
        table.add_column("Ruta")
        table.add_column("Filas", justify="right")

        table.add_row("CACEHI", str(cacehi_result.output_path), str(cacehi_result.rows))
        table.add_row("CACETE", str(cacete_result.output_path), str(cacete_result.rows))

        console.print(table)
        console.print("[bold]Columnas editables CACEHI:[/bold] NCAMEDI, NALVOUT")
        console.print("[bold]Columnas editables CACETE:[/bold] NVOLALM, NADQMES")


    def _render_g11_template_validation_summary(
        cacehi_result: CacehiTemplateValidationResult,
        cacete_result: CaceteTemplateValidationResult,
    ) -> None:
        console.print("")
        console.print("[bold green]Validación de plantillas G11 completada.[/bold green]")
        console.print("")

        table = Table(title=f"Resumen validación plantillas G11 {cacehi_result.period}")
        table.add_column("Plantilla")
        table.add_column("Registros válidos", justify="right")
        table.add_column("Errores", justify="right")
        table.add_column("Advertencias", justify="right")

        table.add_row(
            "CACEHI",
            str(len(cacehi_result.records)),
            str(cacehi_result.error_count),
            str(cacehi_result.warning_count),
        )
        table.add_row(
            "CACETE",
            str(len(cacete_result.records)),
            str(cacete_result.error_count),
            str(cacete_result.warning_count),
        )

        console.print(table)

        for issue in cacehi_result.issues[:20]:
            console.print(
                f"{issue.severity.value} | CACEHI | fila {issue.row or 'general'} | "
                f"{issue.field or ''} | {issue.message} | {issue.value or ''}"
            )

        for issue in cacete_result.issues[:20]:
            console.print(
                f"{issue.severity.value} | CACETE | fila {issue.row or 'general'} | "
                f"{issue.field or ''} | {issue.message} | {issue.value or ''}"
            )

        if cacehi_result.has_errors or cacete_result.has_errors:
            console.print("[bold red]Las plantillas G11 no están listas para exportar.[/bold red]")
        else:
            console.print("[bold green]Las plantillas G11 están listas para exportar.[/bold green]")


    def _render_g11_export_summary(
        cacehi_result: CacehiExportResult,
        cacete_result: CaceteExportResult,
    ) -> None:
        console.print("")
        console.print("[bold green]DBF G11 exportados correctamente.[/bold green]")
        console.print("")

        table = Table(title=f"Resumen exportación G11 {cacehi_result.period}")
        table.add_column("DBF")
        table.add_column("Ruta")
        table.add_column("Originales", justify="right")
        table.add_column("Agregados", justify="right")
        table.add_column("Finales", justify="right")

        table.add_row(
            "CACEHI",
            str(cacehi_result.output_path),
            str(cacehi_result.original_record_count),
            str(cacehi_result.appended_record_count),
            str(cacehi_result.final_record_count),
        )
        table.add_row(
            "CACETE",
            str(cacete_result.output_path),
            str(cacete_result.original_record_count),
            str(cacete_result.appended_record_count),
            str(cacete_result.final_record_count),
        )

        console.print(table)


    def _render_g11_sources_summary(result: G11SourcesValidationResult) -> None:
        console.print("")
        console.print("[bold green]Validación de fuentes G11 completada.[/bold green]")
        console.print("")

        table = Table(title=f"Resumen fuentes G11 {result.period}")
        table.add_column("Métrica")
        table.add_column("Valor", justify="right")

        table.add_row("Registros hidro CACEHI", str(len(result.hydro_rows)))
        table.add_row("Registros térmicos CACETE", str(len(result.thermal_rows)))
        table.add_row("Errores", str(len(result.errors)))
        table.add_row("Advertencias", str(len(result.warnings)))

        console.print(table)

        for issue in result.issues[:30]:
            console.print(
                f"{issue.severity.value} | {issue.section} | {issue.source} | "
                f"{issue.field or ''} | {issue.message} | {issue.value or ''}"
            )

        if result.has_errors:
            console.print("[bold red]Las fuentes G11 no están listas para generar TXT.[/bold red]")
        else:
            console.print("[bold green]Las fuentes G11 están listas.[/bold green]")


    def _render_g11_txt_summary(result: G11TxtResult) -> None:
        console.print("")
        console.print(f"[bold green]TXT G11 generado:[/bold green] {result.output_path}")
        console.print("")

        table = Table(title=f"Resumen TXT G11 {result.period}")
        table.add_column("Métrica")
        table.add_column("Valor", justify="right")

        table.add_row("Registros hidro", str(result.hydro_count))
        table.add_row("Registros térmicos", str(result.thermal_count))
        table.add_row("Advertencias de fuentes", str(result.warnings_count))

        console.print(table)

    @app.command("create-g11-templates")
    def create_g11_templates_command(
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
            help="Ruta del catálogo local G11 en YAML.",
        ),
        output_dir: Path = typer.Option(
            Path("reports/templates"),
            "--output-dir",
            help="Carpeta donde se generarán las plantillas.",
        ),
    ) -> None:
        """Genera las plantillas Excel CACEHI y CACETE para G11."""
        period_label = period.replace("-", "_")

        try:
            cacehi_result = create_cacehi_template(
                period=period,
                catalog_path=catalog,
                output_path=output_dir / f"CACEHI_{period_label}_template.xlsx",
            )
            cacete_result = create_cacete_template(
                period=period,
                catalog_path=catalog,
                output_path=output_dir / f"CACETE_{period_label}_template.xlsx",
            )
        except ValueError as error:
            console.print(f"[bold red]Error:[/bold red] {error}")
            raise typer.Exit(code=1) from error

        _render_g11_template_summary(cacehi_result, cacete_result)


    @app.command("validate-g11-templates")
    def validate_g11_templates_command(
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
            help="Ruta del catálogo local G11 en YAML.",
        ),
        cacehi_template: Path = typer.Option(
            ...,
            "--cacehi-template",
            help="Ruta de la plantilla CACEHI.",
        ),
        cacete_template: Path = typer.Option(
            ...,
            "--cacete-template",
            help="Ruta de la plantilla CACETE.",
        ),
        fail_on_errors: bool = typer.Option(
            False,
            "--fail-on-errors",
            help="Termina con código de error si se encuentran errores.",
        ),
    ) -> None:
        """Valida las plantillas CACEHI y CACETE antes de exportar DBF."""
        try:
            cacehi_result = validate_cacehi_template(
                template_path=cacehi_template,
                period=period,
                catalog_path=catalog,
            )
            cacete_result = validate_cacete_template(
                template_path=cacete_template,
                period=period,
                catalog_path=catalog,
            )
        except ValueError as error:
            console.print(f"[bold red]Error:[/bold red] {error}")
            raise typer.Exit(code=1) from error

        _render_g11_template_validation_summary(cacehi_result, cacete_result)

        if fail_on_errors and (cacehi_result.has_errors or cacete_result.has_errors):
            raise typer.Exit(code=1)


    @app.command("export-g11-dbf")
    def export_g11_dbf_command(
        cacehi_source: Path = typer.Option(
            ...,
            "--cacehi-source",
            help="Ruta del CACEHI.DBF histórico fuente.",
        ),
        cacete_source: Path = typer.Option(
            ...,
            "--cacete-source",
            help="Ruta del CACETE.DBF histórico fuente.",
        ),
        cacehi_template: Path = typer.Option(
            ...,
            "--cacehi-template",
            help="Ruta de la plantilla CACEHI validada.",
        ),
        cacete_template: Path = typer.Option(
            ...,
            "--cacete-template",
            help="Ruta de la plantilla CACETE validada.",
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
            help="Ruta del catálogo local G11 en YAML.",
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
        """Genera CACEHI.DBF y CACETE.DBF agregando el periodo mensual validado."""
        period_output_dir = output_dir / period

        try:
            cacehi_result = export_cacehi_dbf(
                source_dbf_path=cacehi_source,
                template_path=cacehi_template,
                period=period,
                catalog_path=catalog,
                output_path=period_output_dir / "CACEHI.DBF",
                allow_existing_period=allow_existing_period,
            )
            cacete_result = export_cacete_dbf(
                source_dbf_path=cacete_source,
                template_path=cacete_template,
                period=period,
                catalog_path=catalog,
                output_path=period_output_dir / "CACETE.DBF",
                allow_existing_period=allow_existing_period,
            )
        except ValueError as error:
            console.print(f"[bold red]Error:[/bold red] {error}")
            raise typer.Exit(code=1) from error

        _render_g11_export_summary(cacehi_result, cacete_result)


    @app.command("validate-g11-sources")
    def validate_g11_sources_command(
        cacehi: Path = typer.Option(
            ...,
            "--cacehi",
            help="Ruta del CACEHI.DBF.",
        ),
        cacete: Path = typer.Option(
            ...,
            "--cacete",
            help="Ruta del CACETE.DBF.",
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
            help="Ruta del catálogo local G11 en YAML.",
        ),
        fail_on_errors: bool = typer.Option(
            False,
            "--fail-on-errors",
            help="Termina con código de error si se encuentran errores.",
        ),
    ) -> None:
        """Valida CACEHI + CACETE como fuentes del Formato G11."""
        try:
            result = validate_g11_sources(
                cacehi_path=cacehi,
                cacete_path=cacete,
                period=period,
                catalog_path=catalog,
            )
        except ValueError as error:
            console.print(f"[bold red]Error:[/bold red] {error}")
            raise typer.Exit(code=1) from error

        _render_g11_sources_summary(result)

        if fail_on_errors and result.has_errors:
            raise typer.Exit(code=1)


    @app.command("create-g11-txt")
    def create_g11_txt_command(
        cacehi: Path = typer.Option(
            ...,
            "--cacehi",
            help="Ruta del CACEHI.DBF.",
        ),
        cacete: Path = typer.Option(
            ...,
            "--cacete",
            help="Ruta del CACETE.DBF.",
        ),
        period: str = typer.Option(
            ...,
            "--period",
            "-p",
            help="Periodo a generar en formato YYYY-MM. Ejemplo: 2026-01.",
        ),
        catalog: Path = typer.Option(
            ...,
            "--catalog",
            "-c",
            help="Ruta del catálogo local G11 en YAML.",
        ),
        output: Optional[Path] = typer.Option(
            None,
            "--output",
            "-o",
            help="Ruta del TXT generado.",
        ),
    ) -> None:
        """Genera el Formato G11 en TXT."""
        try:
            result = create_g11_txt(
                cacehi_path=cacehi,
                cacete_path=cacete,
                period=period,
                catalog_path=catalog,
                output_path=output,
            )
        except ValueError as error:
            console.print(f"[bold red]Error:[/bold red] {error}")
            raise typer.Exit(code=1) from error

        _render_g11_txt_summary(result)
