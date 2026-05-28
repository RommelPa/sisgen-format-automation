from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from sisgen_automation.cli.g7 import register_g7_commands
from sisgen_automation.cli.g11 import register_g11_commands
from sisgen_automation.cli.g2 import register_g2_commands
from sisgen_automation.cli.g1 import register_g1_commands
from sisgen_automation.cli.dbf import register_dbf_commands
from sisgen_automation.cli.cenhid import register_cenhid_commands
from sisgen_automation.cli.dacoce import register_dacoce_commands
from sisgen_automation.cli.center import register_center_commands


from sisgen_automation.comcen.template import create_comcen_template
from sisgen_automation.comcen.template_validation import validate_comcen_template


from sisgen_automation.comcen.export_dbf import ComcenExportResult, export_comcen_dbf


app = typer.Typer(
    help="Herramientas para automatizar formatos SISGEN.",
    no_args_is_help=True,
)
console = Console()
register_g7_commands(app, console)
register_g11_commands(app, console)
register_g2_commands(app, console)
register_g1_commands(app, console)
register_dbf_commands(app, console)
register_cenhid_commands(app, console)
register_dacoce_commands(app, console)
register_center_commands(app, console)
@app.callback()
def cli() -> None:
    """CLI principal para automatizar formatos SISGEN."""
    pass

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
