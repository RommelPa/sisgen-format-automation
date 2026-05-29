from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from pathlib import Path

from sisgen_automation.g8.catalog import load_g8_catalog
from sisgen_automation.g8.sources import (
    G8SourceRow,
    G8SourceTotals,
    validate_g8_sources,
)


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

VOLTAGE_SECTION_ORDER = [
    ("MAT", "Muy Alta Tensión"),
    ("AT", "Alta Tensión"),
    ("MT", "Media Tensión"),
    ("BT", "Baja Tensión"),
]


@dataclass(frozen=True)
class G8TxtResult:
    period: str
    output_path: Path
    rows_count: int
    warnings_count: int
    active_total_mwh: Decimal
    billing_total_s: Decimal
    average_price_cents_kwh: Decimal


def default_g8_output_path(period: str) -> Path:
    return Path("reports") / "g8" / f"G8_{period.replace('-', '_')}.txt"


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


def _format_decimal(value: Decimal, decimals: int) -> str:
    return f"{value:.{decimals}f}"


def _format_money(value: Decimal) -> str:
    return f"{value:.2f}"


def _line(char: str = "-", width: int = 188) -> str:
    return char * width


def _row(values: list[str], widths: list[int]) -> str:
    cells = []

    for value, width in zip(values, widths, strict=True):
        text = str(value)

        if len(text) > width:
            text = text[:width]

        cells.append(text.ljust(width))

    return " | ".join(cells)


def _empty_totals() -> G8SourceTotals:
    zero = Decimal("0")
    return G8SourceTotals(
        contracted_hp_mw=zero,
        contracted_hfp_mw=zero,
        excess_hp_mw=zero,
        excess_hfp_mw=zero,
        active_hp_mwh=zero,
        active_hfp_mwh=zero,
        active_total_mwh=zero,
        reactive_mvarh=zero,
        billing_power_s=zero,
        billing_excess_s=zero,
        billing_active_s=zero,
        billing_reactive_s=zero,
        billing_others_s=zero,
        billing_total_s=zero,
        average_price_cents_kwh=zero,
    )


def _sum_rows(rows: list[G8SourceRow], field: str) -> Decimal:
    return sum((getattr(row, field) for row in rows), Decimal("0"))


def _section_totals(rows: list[G8SourceRow]) -> G8SourceTotals:
    if not rows:
        return _empty_totals()

    active_total = _sum_rows(rows, "active_total_mwh")
    billing_others = _sum_rows(rows, "billing_others_s")
    billing_total = _sum_rows(rows, "billing_total_s")

    if active_total > 0:
        average_price = (billing_total - billing_others) / (active_total * Decimal("10"))
    else:
        average_price = Decimal("0")

    return G8SourceTotals(
        contracted_hp_mw=_sum_rows(rows, "contracted_hp_mw"),
        contracted_hfp_mw=_sum_rows(rows, "contracted_hfp_mw"),
        excess_hp_mw=_sum_rows(rows, "excess_hp_mw"),
        excess_hfp_mw=_sum_rows(rows, "excess_hfp_mw"),
        active_hp_mwh=_sum_rows(rows, "active_hp_mwh"),
        active_hfp_mwh=_sum_rows(rows, "active_hfp_mwh"),
        active_total_mwh=active_total,
        reactive_mvarh=_sum_rows(rows, "reactive_mvarh"),
        billing_power_s=_sum_rows(rows, "billing_power_s"),
        billing_excess_s=_sum_rows(rows, "billing_excess_s"),
        billing_active_s=_sum_rows(rows, "billing_active_s"),
        billing_reactive_s=_sum_rows(rows, "billing_reactive_s"),
        billing_others_s=billing_others,
        billing_total_s=billing_total,
        average_price_cents_kwh=average_price,
    )


def _power_energy_header() -> list[str]:
    widths = [31, 7, 4, 12, 12, 12, 12, 10, 10, 10, 10, 9, 9, 9, 9, 9, 10]
    return [
        _row(
            [
                "Cliente Libre",
                "Tensión",
                "PC/MD",
                "PC HP MW",
                "PC HFP MW",
                "Exceso HP",
                "Exceso HFP",
                "Energía HP",
                "Energía HFP",
                "Total MWh",
                "MVArh",
                "P Pot HP",
                "P Pot HFP",
                "P Exceso",
                "P En HP",
                "P En HFP",
                "P Reactiva",
            ],
            widths,
        ),
        _line(),
    ]


def _power_energy_row(row: G8SourceRow) -> str:
    widths = [31, 7, 4, 12, 12, 12, 12, 10, 10, 10, 10, 9, 9, 9, 9, 9, 10]
    return _row(
        [
            row.client_name,
            _format_decimal(row.voltage, 1),
            row.power_type,
            _format_decimal(row.contracted_hp_mw, 6),
            _format_decimal(row.contracted_hfp_mw, 6),
            _format_decimal(row.excess_hp_mw, 6),
            _format_decimal(row.excess_hfp_mw, 6),
            _format_decimal(row.active_hp_mwh, 3),
            _format_decimal(row.active_hfp_mwh, 3),
            _format_decimal(row.active_total_mwh, 3),
            _format_decimal(row.reactive_mvarh, 3),
            _format_decimal(row.power_hp_price_s_kw, 4),
            _format_decimal(row.power_hfp_price_s_kw, 4),
            _format_decimal(row.excess_price_s_kw, 4),
            _format_decimal(row.active_hp_price_cents, 4),
            _format_decimal(row.active_hfp_price_cents, 4),
            _format_decimal(row.reactive_price_cents, 4),
        ],
        widths,
    )


def _power_energy_subtotal(totals: G8SourceTotals) -> str:
    widths = [31, 7, 4, 12, 12, 12, 12, 10, 10, 10, 10, 9, 9, 9, 9, 9, 10]
    return _row(
        [
            "Sub - Total",
            "",
            "",
            _format_decimal(totals.contracted_hp_mw, 6),
            _format_decimal(totals.contracted_hfp_mw, 6),
            _format_decimal(totals.excess_hp_mw, 6),
            _format_decimal(totals.excess_hfp_mw, 6),
            _format_decimal(totals.active_hp_mwh, 3),
            _format_decimal(totals.active_hfp_mwh, 3),
            _format_decimal(totals.active_total_mwh, 3),
            _format_decimal(totals.reactive_mvarh, 3),
            "",
            "",
            "",
            "",
            "",
            "",
        ],
        widths,
    )


def _billing_header() -> list[str]:
    widths = [31, 7, 13, 13, 13, 13, 13, 13, 10]
    return [
        _row(
            [
                "Cliente Libre",
                "Tensión",
                "Potencia S/",
                "Exceso S/",
                "Energía S/",
                "Reactiva S/",
                "Otros S/",
                "Total S/",
                "Precio Med",
            ],
            widths,
        ),
        _line(),
    ]


def _billing_row(row: G8SourceRow) -> str:
    widths = [31, 7, 13, 13, 13, 13, 13, 13, 10]
    return _row(
        [
            row.client_name,
            _format_decimal(row.voltage, 1),
            _format_money(row.billing_power_s),
            _format_money(row.billing_excess_s),
            _format_money(row.billing_active_s),
            _format_money(row.billing_reactive_s),
            _format_money(row.billing_others_s),
            _format_money(row.billing_total_s),
            _format_decimal(row.average_price_cents_kwh, 2),
        ],
        widths,
    )


def _billing_subtotal(totals: G8SourceTotals) -> str:
    widths = [31, 7, 13, 13, 13, 13, 13, 13, 10]
    return _row(
        [
            "Sub - Total",
            "",
            _format_money(totals.billing_power_s),
            _format_money(totals.billing_excess_s),
            _format_money(totals.billing_active_s),
            _format_money(totals.billing_reactive_s),
            _format_money(totals.billing_others_s),
            _format_money(totals.billing_total_s),
            _format_decimal(totals.average_price_cents_kwh, 2),
        ],
        widths,
    )


def _group_rows(rows: tuple[G8SourceRow, ...]) -> dict[str, list[G8SourceRow]]:
    grouped: dict[str, list[G8SourceRow]] = {code: [] for code, _ in VOLTAGE_SECTION_ORDER}

    for row in rows:
        grouped.setdefault(row.voltage_level, []).append(row)

    return grouped


def _power_energy_lines(rows: tuple[G8SourceRow, ...], totals: G8SourceTotals) -> list[str]:
    grouped = _group_rows(rows)
    lines = [
        "BLOQUE 1: POTENCIA, ENERGÍA Y PRECIOS",
        _line("="),
        *_power_energy_header(),
    ]

    for code, title in VOLTAGE_SECTION_ORDER:
        section_rows = grouped.get(code, [])
        section_totals = _section_totals(section_rows)

        lines.append(title)
        lines.append(_line())
        for row in section_rows:
            lines.append(_power_energy_row(row))
        lines.append(_power_energy_subtotal(section_totals))
        lines.append(_line())

    lines.append("T o t a l   G e n e r a l")
    lines.append(_power_energy_subtotal(totals))
    lines.append(_line("="))

    return lines


def _billing_lines(rows: tuple[G8SourceRow, ...], totals: G8SourceTotals) -> list[str]:
    grouped = _group_rows(rows)
    lines = [
        "BLOQUE 2: FACTURACIÓN",
        _line("="),
        *_billing_header(),
    ]

    for code, title in VOLTAGE_SECTION_ORDER:
        section_rows = grouped.get(code, [])
        section_totals = _section_totals(section_rows)

        lines.append(title)
        lines.append(_line())
        for row in section_rows:
            lines.append(_billing_row(row))
        lines.append(_billing_subtotal(section_totals))
        lines.append(_line())

    lines.append("T o t a l   G e n e r a l")
    lines.append(_billing_subtotal(totals))
    lines.append(_line("="))
    lines.append("(1) Otros incluye demás cargos, excepto IGV.")
    lines.append("(2) Precio Medio = Facturación Total sin Otros / Total Energía Activa.")

    return lines


def create_g8_txt(
    *,
    vefame_path: Path,
    period: str,
    catalog_path: Path,
    output_path: Path | None = None,
) -> G8TxtResult:
    validation = validate_g8_sources(
        vefame_path=vefame_path,
        period=period,
        catalog_path=catalog_path,
    )

    if validation.has_errors:
        preview = "\n".join(
            f"{issue.severity.value} | fila {issue.row or 'general'} | "
            f"{issue.client_code or ''} | {issue.field or ''} | {issue.message} | "
            f"{issue.value or ''}"
            for issue in validation.errors[:20]
        )
        raise ValueError(
            "Las fuentes G8 tienen errores. Revisa validate-g8-sources antes de generar G8."
            f"\n{preview}"
        )

    catalog = load_g8_catalog(catalog_path)
    year, month = _period_parts(period)

    if output_path is None:
        output_path = default_g8_output_path(period)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    today = date.today().strftime("%d-%m-%Y")
    month_name = MONTH_NAMES_ES[month]

    lines = [
        f"Ministerio de Energía y Minas{'Fecha : ' + today:>82}",
        "Dirección General de Electricidad",
        "Información de Empresas Generadoras y Autoproductores",
        "Venta y Facturación de Energía Eléctrica a Clientes Libres",
        "Formato de Información Mensual Formato G8",
        _line("="),
        f"Empresa : {catalog.company.name}",
        f"Año : {year}    Mes : {month_name}",
        _line("="),
        "",
        *_power_energy_lines(validation.rows, validation.totals),
        "",
        *_billing_lines(validation.rows, validation.totals),
        "",
    ]

    output_path.write_text("\n".join(lines), encoding="utf-8-sig")

    return G8TxtResult(
        period=period,
        output_path=output_path,
        rows_count=len(validation.rows),
        warnings_count=len(validation.warnings),
        active_total_mwh=validation.totals.active_total_mwh,
        billing_total_s=validation.totals.billing_total_s,
        average_price_cents_kwh=validation.totals.average_price_cents_kwh,
    )
