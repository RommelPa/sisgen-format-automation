from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from sisgen_automation.dbf.profile import DbfProfile, read_dbf_profile, write_profile_markdown


def register_dbf_commands(app: typer.Typer, console: Console) -> None:
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
