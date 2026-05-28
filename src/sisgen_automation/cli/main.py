from __future__ import annotations


import typer
from rich.console import Console
from sisgen_automation.cli.g7 import register_g7_commands
from sisgen_automation.cli.g11 import register_g11_commands
from sisgen_automation.cli.g2 import register_g2_commands
from sisgen_automation.cli.g1 import register_g1_commands
from sisgen_automation.cli.dbf import register_dbf_commands
from sisgen_automation.cli.cenhid import register_cenhid_commands
from sisgen_automation.cli.dacoce import register_dacoce_commands
from sisgen_automation.cli.center import register_center_commands
from sisgen_automation.cli.comcen import register_comcen_commands


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
register_comcen_commands(app, console)
@app.callback()
def cli() -> None:
    """CLI principal para automatizar formatos SISGEN."""
    pass

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
