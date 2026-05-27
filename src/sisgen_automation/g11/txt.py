from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from pathlib import Path

from sisgen_automation.g11.catalog import load_g11_catalog
from sisgen_automation.g11.sources import G11HydroRow, G11ThermalRow, validate_g11_sources


MONTH_NAMES_ES = {
    1: "Enero",
    2: "Febrero",
    3: "Marzo",
    4: "Abril",
    5: "Mayo",
    6: "Junio",
    7: "Julio",
    8: "Agosto",
    9: "Setiembre",
    10: "Octubre",
    11: "Noviembre",
    12: "Diciembre",
}


@dataclass(frozen=True)
class G11TxtResult:
    period: str
    output_path: Path
    hydro_count: int
    thermal_count: int
    warnings_count: int


def default_g11_output_path(period: str) -> Path:
    return Path("reports") / "g11" / f"G11_{period.replace('-', '_')}.txt"


def _period_parts(period: str) -> tuple[int, int]:
    try:
        year_text, month_text = period.split("-", maxsplit=1)
    except ValueError as exc:
        raise ValueError("El periodo debe tener formato YYYY-MM, por ejemplo 2026-01.") from exc

    if len(year_text) != 4 or len(month_text) != 2:
        raise ValueError("El periodo debe tener formato YYYY-MM, por ejemplo 2026-01.")

    year = int(year_text)
    month = int(month_text)

    if not 1 <= month <= 12:
        raise ValueError("El mes del periodo debe estar entre 01 y 12.")

    return year, month


def _format_decimal(value: Decimal, decimals: int = 2) -> str:
    return f"{value:,.{decimals}f}"


def _line(char: str = "-", width: int = 116) -> str:
    return char * width


def _row(values: list[str], widths: list[int]) -> str:
    cells = []

    for value, width in zip(values, widths, strict=True):
        text = str(value)

        if len(text) > width:
            text = text[: width - 1] + "…"

        cells.append(text.ljust(width))

    return " | ".join(cells)


def _thermal_lines(rows: list[G11ThermalRow]) -> list[str]:
    widths = [25, 21, 20, 18, 18]

    lines = [
        "CENTRALES TERMOELECTRICAS",
        _line(),
        _row(
            [
                "Nombre de la Central",
                "Tipo de Combustible",
                "Volumen Inicial (Gl)",
                "Adquisición Mes (Gl)",
                "Total (Gl)",
            ],
            widths,
        ),
        _line(),
    ]

    for row in rows:
        lines.append(
            _row(
                [
                    row.cnomcen,
                    row.cdescom,
                    _format_decimal(row.nvolalm),
                    _format_decimal(row.nadqmes),
                    _format_decimal(row.total),
                ],
                widths,
            )
        )

    lines.extend(
        [
            _line(),
            "(1) Para Central Térmica : D1 : Diesel 1 (Galones)",
            "                            D2 : Diesel 2 (Galones)",
            "                            R5 : Residual 5 (Galones)",
            "                            R6 : Residual 6 (Galones)",
            "                            RQ : Residual 500 (Galones)",
            "                            CA : Carbon (Toneladas)",
            "                            GN : Gas Natural (Metros Cúbicos)",
        ]
    )

    return lines


def _hydro_lines(rows: list[G11HydroRow]) -> list[str]:
    widths = [25, 30, 22, 24]

    lines = [
        "CENTRALES HIDROELECTRICAS",
        _line(),
        _row(
            [
                "Nombre de la Central",
                "Cuenca del Recurso Hídrico",
                "Caudal Medio (m3/s)",
                "Volumen Útil Final (Mm3)",
            ],
            widths,
        ),
        _line(),
    ]

    for row in rows:
        lines.append(
            _row(
                [
                    row.cnomcen,
                    row.cnomcue,
                    _format_decimal(row.ncamedi),
                    _format_decimal(row.nalvout),
                ],
                widths,
            )
        )

    lines.append(_line())

    return lines


def create_g11_txt(
    *,
    cacehi_path: Path,
    cacete_path: Path,
    period: str,
    catalog_path: Path,
    output_path: Path | None = None,
) -> G11TxtResult:
    validation = validate_g11_sources(
        cacehi_path=cacehi_path,
        cacete_path=cacete_path,
        period=period,
        catalog_path=catalog_path,
    )

    if validation.has_errors:
        preview = "\n".join(
            f"{issue.severity.value} | {issue.section} | {issue.source} | "
            f"{issue.field or ''} | {issue.message} | {issue.value or ''}"
            for issue in validation.errors[:20]
        )
        raise ValueError(
            "Las fuentes G11 tienen errores. Revisa validate-g11-sources antes de generar G11."
            f"\n{preview}"
        )

    catalog = load_g11_catalog(catalog_path)
    year, month = _period_parts(period)

    if output_path is None:
        output_path = default_g11_output_path(period)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    today = date.today().strftime("%d-%m-%Y")
    month_name = MONTH_NAMES_ES[month]

    lines = [
        f"Ministerio de Energía y Minas{'Fecha : ' + today:>82}",
        "Dirección General de Electricidad",
        "Información de Empresas Generadoras y Autoproductores",
        "Volumen Util de los Embalses y Volumen Almacenado de Combustibles",
        "Formato de Información Mensual Formato G11",
        _line("="),
        f"Empresa : {catalog.company.name}",
        f"Año : {year}    Mes : {month_name}",
        _line("="),
        "",
        *_thermal_lines(validation.thermal_rows),
        "",
        *_hydro_lines(validation.hydro_rows),
        "",
    ]

    output_path.write_text("\n".join(lines), encoding="utf-8")

    return G11TxtResult(
        period=period,
        output_path=output_path,
        hydro_count=len(validation.hydro_rows),
        thermal_count=len(validation.thermal_rows),
        warnings_count=len(validation.warnings),
    )