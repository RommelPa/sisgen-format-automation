from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from pathlib import Path

from sisgen_automation.u2.catalog import load_u2_catalog
from sisgen_automation.u2.sources import U2SourceRow, U2SourceTotals, validate_u2_sources


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
class U2TxtResult:
    period: str
    output_path: Path
    rows_count: int
    warnings_count: int
    free_clients: Decimal
    consumption_mwh: Decimal
    billing_s: Decimal


def default_u2_output_path(period: str) -> Path:
    return Path("reports") / "u2" / f"U2_{period.replace('-', '_')}.txt"


def _period_parts(period: str) -> tuple[int, int]:
    try:
        year_text, month_text = period.split("-", maxsplit=1)
    except ValueError as exc:
        raise ValueError("El periodo debe tener formato YYYY-MM, por ejemplo 2025-11.") from exc

    if len(year_text) != 4 or len(month_text) != 2:
        raise ValueError("El periodo debe tener formato YYYY-MM, por ejemplo 2025-11.")

    year = int(year_text)
    month = int(month_text)

    if not 1 <= month <= 12:
        raise ValueError("El mes del periodo debe estar entre 01 y 12.")

    return year, month


def _line(char: str = "-", width: int = 105) -> str:
    return char * width


def _format_int(value: Decimal) -> str:
    return f"{value:.0f}"


def _format_mwh(value: Decimal) -> str:
    return f"{value:,.3f}"


def _format_money(value: Decimal) -> str:
    return f"{value:,.2f}"


def _row(description: str, users: str, consumption: str, billing: str) -> str:
    return (
        f"{description:<60}"
        f"{users:>10}"
        f"{consumption:>17}"
        f"{billing:>17}"
    )


def _table_lines(rows: tuple[U2SourceRow, ...], totals: U2SourceTotals) -> list[str]:
    lines = [
        _line("="),
        _row("Clasificacion CIIU", "Numero", "Consumo (MWh)", "Facturacion S/."),
        _line("-"),
    ]

    for row in rows:
        lines.append(
            _row(
                row.description,
                _format_int(row.free_clients),
                _format_mwh(row.consumption_mwh),
                _format_money(row.billing_s),
            )
        )

    lines.extend(
        [
            _line("-"),
            _row(
                "T O T A L   G E N E R A L",
                _format_int(totals.free_clients),
                _format_mwh(totals.consumption_mwh),
                _format_money(totals.billing_s),
            ),
            _line("="),
        ]
    )

    return lines


def create_u2_txt(
    *,
    ciugen_path: Path,
    period: str,
    catalog_path: Path,
    output_path: Path | None = None,
) -> U2TxtResult:
    validation = validate_u2_sources(
        ciugen_path=ciugen_path,
        period=period,
        catalog_path=catalog_path,
    )

    if validation.has_errors:
        preview = "\n".join(
            f"{issue.severity.value} | fila {issue.row or 'general'} | "
            f"{issue.ciiu_code or ''} | {issue.field or ''} | {issue.message} | "
            f"{issue.value or ''}"
            for issue in validation.errors[:20]
        )
        raise ValueError(
            "Las fuentes U2 tienen errores. Revisa validate-u2-sources antes de generar U2."
            f"\n{preview}"
        )

    catalog = load_u2_catalog(catalog_path)
    year, month = _period_parts(period)

    if output_path is None:
        output_path = default_u2_output_path(period)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    today = date.today().strftime("%d-%m-%Y")
    month_name = MONTH_NAMES_ES[month]

    lines = [
        f"Ministerio de Energia y Minas{'Fecha : ' + today:>60}",
        "Direccion General de Electricidad",
        "Informacion de Empresas Generadoras y Autoproductoras",
        "Usuarios por Clasificacion CIIU",
        "Formato de Informacion Mensual Formato U2",
        _line("="),
        f"Empresa : {catalog.company.name}",
        f"Anio : {year}    Mes : {month_name}",
        _line("="),
        f"Region : {catalog.location.region_name}",
        f"Departamento : {catalog.location.department_name}",
        *_table_lines(validation.rows, validation.totals),
        "",
    ]

    output_path.write_text("\n".join(lines), encoding="utf-8-sig")

    return U2TxtResult(
        period=period,
        output_path=output_path,
        rows_count=len(validation.rows),
        warnings_count=len(validation.warnings),
        free_clients=validation.totals.free_clients,
        consumption_mwh=validation.totals.consumption_mwh,
        billing_s=validation.totals.billing_s,
    )
