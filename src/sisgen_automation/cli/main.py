from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from sisgen_automation.dbf.profile import DbfProfile, read_dbf_profile, write_profile_markdown

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

from sisgen_automation.center.validate import (
    CenterValidationResult,
    validate_center_dbf,
    write_center_validation_markdown,
)

from sisgen_automation.center.template import create_center_template

from sisgen_automation.center.template_validation import (
    CenterTemplateValidationResult,
    validate_center_template,
    write_center_template_validation_markdown,
)

from sisgen_automation.center.export_dbf import CenterExportResult, export_center_dbf
from sisgen_automation.comcen.template import create_comcen_template
from sisgen_automation.comcen.template_validation import validate_comcen_template

from sisgen_automation.g1.sources import (
    G1SourcesValidationResult,
    validate_g1_sources,
    write_g1_sources_validation_markdown,
)

from sisgen_automation.g1.txt import G1TxtResult, create_g1_txt
from sisgen_automation.comcen.export_dbf import ComcenExportResult, export_comcen_dbf
from sisgen_automation.g2.sources import G2SourcesValidationResult, validate_g2_sources

from sisgen_automation.g2.txt import G2TxtResult, create_g2_txt

from sisgen_automation.g2.template import VepoenTemplateResult, create_vepoen_template
from sisgen_automation.g2.template_validation import (
    VepoenTemplateValidationResult,
    validate_vepoen_template,
)
from sisgen_automation.g2.export_dbf import VepoenExportResult, export_vepoen_dbf

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

app = typer.Typer(
    help="Herramientas para automatizar formatos SISGEN.",
    no_args_is_help=True,
)
console = Console()
@app.callback()
def cli() -> None:
    """CLI principal para automatizar formatos SISGEN."""
    pass

def _render_profile_summary(profile: DbfProfile, output_path: Path) -> None:
    console.print("")
    console.print(f"[bold green]Perfil DBF generado correctamente:[/bold green] {output_path}")
    console.print("")

    metadata_table = Table(title=f"Resumen de {profile.path.name}")
    metadata_table.add_column("Propiedad")
    metadata_table.add_column("Valor", justify="right")

    metadata_table.add_row("Versión DBF", f"{profile.version_byte} - {profile.version_label}")
    metadata_table.add_row("Registros", str(profile.record_count))
    metadata_table.add_row("Registros activos", str(profile.active_record_count))
    metadata_table.add_row("Registros eliminados", str(profile.deleted_record_count))
    metadata_table.add_row("Campos", str(len(profile.fields)))
    metadata_table.add_row("Longitud de cabecera", f"{profile.header_length} bytes")
    metadata_table.add_row("Longitud por registro", f"{profile.record_length} bytes")

    console.print(metadata_table)

    fields_table = Table(title="Campos detectados")
    fields_table.add_column("#", justify="right")
    fields_table.add_column("Campo")
    fields_table.add_column("Tipo")
    fields_table.add_column("Longitud", justify="right")
    fields_table.add_column("Decimales", justify="right")

    for index, field in enumerate(profile.fields, start=1):
        fields_table.add_row(
            str(index),
            field.name,
            field.field_type,
            str(field.length),
            str(field.decimal_count),
        )

    console.print(fields_table)

    if profile.warnings:
        console.print("[bold yellow]Advertencias:[/bold yellow]")
        for warning in profile.warnings:
            console.print(f"- {warning}")


@app.command("profile-dbf")
def profile_dbf(
    dbf_path: Path = typer.Argument(..., help="Ruta del archivo DBF a perfilar."),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Ruta del reporte Markdown generado.",
    ),
) -> None:
    """Lee la estructura técnica de un archivo DBF y genera un reporte Markdown."""
    profile = read_dbf_profile(dbf_path)

    output_path = output
    if output_path is None:
        output_path = Path("reports") / f"{dbf_path.stem}_profile.md"

    write_profile_markdown(profile, output_path)
    _render_profile_summary(profile, output_path)

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
        help="Ruta del Excel generado.",
    ),
) -> None:
    """Genera una plantilla Excel mensual para CENHID."""
    try:
        output_path = create_cenhid_template(
            period=period,
            catalog_path=catalog,
            output_path=output,
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
    
def _render_center_validation_summary(
    result: CenterValidationResult,
    output_path: Path,
) -> None:
    console.print("")
    console.print(f"[bold green]Validación CENTER generada:[/bold green] {output_path}")
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


@app.command("validate-center")
def validate_center(
    dbf_path: Path = typer.Argument(..., help="Ruta del archivo CENTER.DBF a validar."),
    catalog: Path = typer.Option(
        ...,
        "--catalog",
        "-c",
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
        help="Termina con código de error si se encuentran errores de validación.",
    ),
) -> None:
    """Valida CENTER contra estructura, catálogo y reglas de negocio."""
    result = validate_center_dbf(dbf_path=dbf_path, catalog_path=catalog)

    output_path = output
    if output_path is None:
        output_path = Path("reports") / f"{dbf_path.stem}_validation.md"

    write_center_validation_markdown(result, output_path)
    _render_center_validation_summary(result, output_path)

    if fail_on_errors and result.has_errors:
        raise typer.Exit(code=1)
    
@app.command("create-center-template")
def create_center_template_command(
    period: str = typer.Option(
        ...,
        "--period",
        "-p",
        help="Periodo de la plantilla en formato YYYY-MM. Ejemplo: 2026-01.",
    ),
    catalog: Path = typer.Option(
        ...,
        "--catalog",
        "-c",
        help="Ruta del catálogo local CENTER en YAML.",
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Ruta del Excel generado.",
    ),
) -> None:
    """Genera una plantilla Excel mensual para CENTER."""
    try:
        output_path = create_center_template(
            period=period,
            catalog_path=catalog,
            output_path=output,
        )
    except ValueError as error:
        console.print(f"[bold red]Error:[/bold red] {error}")
        raise typer.Exit(code=1) from error

    console.print("")
    console.print(f"[bold green]Plantilla CENTER generada:[/bold green] {output_path}")
    console.print("")
    console.print(
        "[bold]Columnas editables:[/bold] CESTGRU, NHORPUN, NFUHOPU, "
        "CHRSMAN, CHRSOPE, CHRSSAL, NCONLUB"
    )
    console.print("[bold]Columna calculada:[/bold] NTOPRBR = NHORPUN + NFUHOPU")

def _render_center_template_validation_summary(
    result: CenterTemplateValidationResult,
    output_path: Path,
) -> None:
    console.print("")
    console.print(f"[bold green]Validación de plantilla CENTER generada:[/bold green] {output_path}")
    console.print("")

    table = Table(title=f"Resumen validación plantilla CENTER {result.period}")
    table.add_column("Métrica")
    table.add_column("Valor", justify="right")

    table.add_row("Filas leídas", str(result.rows_read))
    table.add_row("Unidades esperadas", str(result.expected_units))
    table.add_row("Unidades válidas", str(result.valid_units))
    table.add_row("Errores", str(len(result.errors)))
    table.add_row("Advertencias", str(len(result.warnings)))

    console.print(table)

    if result.has_errors:
        console.print("[bold red]La plantilla CENTER no está lista para exportar.[/bold red]")
    elif result.warnings:
        console.print("[bold yellow]La plantilla CENTER tiene advertencias.[/bold yellow]")
    else:
        console.print("[bold green]La plantilla CENTER está lista para exportar.[/bold green]")


@app.command("validate-center-template")
def validate_center_template_command(
    template_path: Path = typer.Argument(..., help="Ruta de la plantilla CENTER en Excel."),
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
    """Valida una plantilla mensual CENTER antes de generar DBF."""
    try:
        result = validate_center_template(
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

    write_center_template_validation_markdown(result, output_path)
    _render_center_template_validation_summary(result, output_path)

    if fail_on_errors and result.has_errors:
        raise typer.Exit(code=1)
    
def _render_center_export_summary(result: CenterExportResult) -> None:
    console.print("")
    console.print(f"[bold green]DBF CENTER exportado correctamente:[/bold green] {result.output_path}")
    console.print("")

    table = Table(title="Resumen de exportación CENTER")
    table.add_column("Métrica")
    table.add_column("Valor", justify="right")

    table.add_row("Periodo agregado", result.period)
    table.add_row("Registros originales", str(result.original_record_count))
    table.add_row("Registros agregados", str(result.appended_record_count))
    table.add_row("Registros finales", str(result.final_record_count))

    console.print(table)


@app.command("export-center-dbf")
def export_center_dbf_command(
    source_dbf_path: Path = typer.Argument(..., help="Ruta del CENTER.DBF histórico fuente."),
    template_path: Path = typer.Argument(..., help="Ruta de la plantilla CENTER validada."),
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
        help="Ruta del catálogo local CENTER en YAML.",
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
    """Genera un nuevo CENTER.DBF agregando el periodo mensual validado."""
    try:
        result = export_center_dbf(
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

    _render_center_export_summary(result)

@app.command("create-comcen-template")
def create_comcen_template_command(
    period: str = typer.Option(
        ...,
        "--period",
        "-p",
        help="Periodo de la plantilla en formato YYYY-MM. Ejemplo: 2026-01.",
    ),
    catalog: Path = typer.Option(
        ...,
        "--catalog",
        "-c",
        help="Ruta del catálogo local CENTER en YAML.",
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Ruta del Excel generado.",
    ),
) -> None:
    """Genera una plantilla Excel mensual para COMCEN."""
    try:
        result = create_comcen_template(
            period=period,
            catalog_path=catalog,
            output_path=output,
        )
    except ValueError as error:
        console.print(f"[bold red]Error:[/bold red] {error}")
        raise typer.Exit(code=1) from error

    console.print("")
    console.print(f"[bold green]Plantilla COMCEN generada:[/bold green] {result.output_path}")
    console.print("")

    table = Table(title=f"Resumen plantilla COMCEN {result.period}")
    table.add_column("Métrica")
    table.add_column("Valor", justify="right")
    table.add_row("Periodo", result.period)
    table.add_row("Filas", str(result.rows))
    console.print(table)

    console.print("[bold]Columna editable:[/bold] NTOTCOM")


@app.command("validate-comcen-template")
def validate_comcen_template_command(
    template_path: Path = typer.Argument(
        ...,
        help="Ruta de la plantilla COMCEN en Excel.",
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
        help="Ruta del catálogo local CENTER en YAML.",
    ),
    fail_on_errors: bool = typer.Option(
        False,
        "--fail-on-errors",
        help="Termina con código de error si se encuentran errores.",
    ),
) -> None:
    """Valida una plantilla mensual COMCEN antes de generar DBF."""
    try:
        result = validate_comcen_template(
            template_path=template_path,
            period=period,
            catalog_path=catalog,
        )
    except ValueError as error:
        console.print(f"[bold red]Error:[/bold red] {error}")
        raise typer.Exit(code=1) from error

    console.print("")
    console.print(f"[bold green]Validación COMCEN:[/bold green] {template_path}")
    console.print("")

    table = Table(title=f"Resumen validación plantilla COMCEN {period}")
    table.add_column("Métrica")
    table.add_column("Valor", justify="right")
    table.add_row("Registros válidos", str(len(result.records)))
    table.add_row("Errores", str(result.error_count))
    table.add_row("Advertencias", str(result.warning_count))
    console.print(table)

    for issue in result.issues:
        location = f"fila {issue.row}" if issue.row is not None else "general"
        field = issue.field or "-"
        console.print(
            f"{issue.severity.value} | {location} | {field} | "
            f"{issue.message} | {issue.value}"
        )

    if result.has_errors:
        console.print("[bold red]La plantilla COMCEN no está lista para exportar.[/bold red]")
        if fail_on_errors:
            raise typer.Exit(code=1)
    else:
        console.print("[bold green]La plantilla COMCEN está lista para exportar.[/bold green]")

def _render_comcen_export_summary(result: ComcenExportResult) -> None:
    console.print("")
    console.print(f"[bold green]DBF COMCEN exportado correctamente:[/bold green] {result.output_path}")
    console.print("")

    table = Table(title="Resumen de exportación COMCEN")
    table.add_column("Métrica")
    table.add_column("Valor", justify="right")

    table.add_row("Periodo agregado", result.period)
    table.add_row("Registros originales", str(result.original_record_count))
    table.add_row("Registros agregados", str(result.appended_record_count))
    table.add_row("Registros finales", str(result.final_record_count))

    console.print(table)

@app.command("export-comcen-dbf")
def export_comcen_dbf_command(
    source_dbf_path: Path = typer.Argument(..., help="Ruta del COMCEN.DBF fuente."),
    template_path: Path = typer.Argument(..., help="Ruta de la plantilla COMCEN validada."),
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
        help="Ruta del catálogo local CENTER en YAML.",
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
    """Genera un nuevo COMCEN.DBF agregando el periodo mensual validado."""
    try:
        result = export_comcen_dbf(
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

    _render_comcen_export_summary(result)

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
    
@app.command("desktop")
def desktop_command() -> None:
    """Abre la interfaz gráfica de escritorio."""
    try:
        from sisgen_automation.ui.desktop_app import run_desktop_app
    except ModuleNotFoundError as error:
        console.print(
            "[bold red]Error:[/bold red] PySide6 no está instalado. "
            'Ejecuta: pip install -e ".[desktop]"'
        )
        raise typer.Exit(code=1) from error

    run_desktop_app()

if __name__ == "__main__":
    app()