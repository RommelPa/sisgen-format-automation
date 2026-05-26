from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

from sisgen_automation.g2.sources import G2SaleRow, validate_g2_sources


@dataclass(frozen=True)
class G2TxtResult:
    period: str
    output_path: Path
    row_count: int
    distributor_count: int
    warnings_count: int


MONTH_NAMES = {
    "01": "Enero",
    "02": "Febrero",
    "03": "Marzo",
    "04": "Abril",
    "05": "Mayo",
    "06": "Junio",
    "07": "Julio",
    "08": "Agosto",
    "09": "Septiembre",
    "10": "Octubre",
    "11": "Noviembre",
    "12": "Diciembre",
}


def default_g2_output_path(period: str) -> Path:
    return Path("reports") / "g2" / f"G2_{period.replace('-', '_')}.txt"


def _period_parts(period: str) -> tuple[str, str, str]:
    year_text, month_text = period.split("-", maxsplit=1)
    return year_text, month_text, MONTH_NAMES.get(month_text, month_text)


def _num(value: Decimal, decimals: int = 3) -> str:
    return f"{value:.{decimals}f}"


def _money(value: Decimal) -> str:
    return f"{value:.2f}"


def _int(value: Decimal) -> str:
    return f"{value:.0f}"


def _client_type_label(client_type: str) -> str:
    normalized = client_type.strip().upper()

    if normalized == "R":
        return "Cliente Regulado"

    if normalized == "L":
        return "Cliente Libre"

    return f"Cliente {client_type}" if client_type else "Cliente sin tipo"


def _sum_decimal(rows: list[G2SaleRow], attr: str) -> Decimal:
    return sum((getattr(row, attr) for row in rows), Decimal("0"))


def _format_row(columns: list[str], widths: list[int]) -> str:
    values: list[str] = []

    for value, width in zip(columns, widths, strict=True):
        text = str(value)

        if len(text) > width:
            text = text[: width - 1] + "…"

        values.append(text.ljust(width))

    return " | ".join(values)


def _bar_row(row: G2SaleRow, widths: list[int]) -> str:
    name = row.delivery_bar_name

    if row.client_type:
        name = f"{name} ({row.client_type})"

    return _format_row(
        [
            name,
            _num(row.voltage_kv, 1),
            _num(row.ppb, 4),
            _num(row.pebp, 4),
            _num(row.pebf, 4),
            _num(row.energy_hp_mwh, 3),
            _num(row.energy_hfp_mwh, 3),
            _num(row.energy_total_mwh, 3),
            _int(row.contracted_power_hp_kw),
            _int(row.contracted_power_hfp_kw),
            _int(row.max_demand_hp_kw),
            _int(row.max_demand_hfp_kw),
            _money(row.billing_power_pen),
            _money(row.billing_energy_pen),
            _money(row.billing_total_pen),
        ],
        widths,
    )


def _total_row(label: str, rows: list[G2SaleRow], widths: list[int]) -> str:
    energy_hp = _sum_decimal(rows, "energy_hp_mwh")
    energy_hfp = _sum_decimal(rows, "energy_hfp_mwh")
    energy_total = energy_hp + energy_hfp

    return _format_row(
        [
            label,
            "",
            "",
            "",
            "",
            _num(energy_hp, 3),
            _num(energy_hfp, 3),
            _num(energy_total, 3),
            _int(_sum_decimal(rows, "contracted_power_hp_kw")),
            _int(_sum_decimal(rows, "contracted_power_hfp_kw")),
            "",
            "",
            _money(_sum_decimal(rows, "billing_power_pen")),
            _money(_sum_decimal(rows, "billing_energy_pen")),
            _money(sum((row.billing_total_pen for row in rows), Decimal("0"))),
        ],
        widths,
    )


def _group_rows_by_distributor(rows: list[G2SaleRow]) -> dict[str, list[G2SaleRow]]:
    grouped: dict[str, list[G2SaleRow]] = {}

    for row in rows:
        grouped.setdefault(row.distributor_code, []).append(row)

    return grouped

def _ordered_distributor_codes(
    grouped: dict[str, list[G2SaleRow]],
    distributor_order: list[str],
) -> list[str]:
    ordered = [code for code in distributor_order if code in grouped]
    ordered_set = set(ordered)
    remaining = sorted(code for code in grouped if code not in ordered_set)
    return ordered + remaining

def _g2_to_text(
    *,
    period: str,
    rows: list[G2SaleRow],
    distributor_order: list[str],
) -> str:
    year_text, _, month_name = _period_parts(period)

    widths = [30, 7, 8, 8, 8, 11, 11, 12, 10, 10, 8, 8, 14, 14, 15]

    lines: list[str] = []

    lines.append("Ministerio de Energía y Minas")
    lines.append("Dirección General de Electricidad")
    lines.append("Información de Empresas Generadoras y Autoproductores")
    lines.append("Venta Mensual de Potencia y Energía a Empresas Distribuidoras")
    lines.append("Formato de Información Mensual Formato G2")
    lines.append("")
    lines.append("Empresa : Emp. de Generación Eléctrica de Arequipa S. A.")
    lines.append(f"Año     : {year_text}")
    lines.append(f"Mes     : {month_name}")
    lines.append("")
    lines.append(
        _format_row(
            [
                "Barra de Entrega",
                "Tensión",
                "PPB",
                "PEBP",
                "PEBF",
                "HP",
                "HFP",
                "Total",
                "Pot HP",
                "Pot HFP",
                "MD HP",
                "MD HFP",
                "Fact. Pot.",
                "Fact. Energ.",
                "Fact. Total",
            ],
            widths,
        )
    )
    lines.append(
        _format_row(
            [
                "Nombre",
                "(kV)",
                "",
                "",
                "",
                "(MWh)",
                "(MWh)",
                "(MWh)",
                "(kW)",
                "(kW)",
                "(kW)",
                "(kW)",
                "(S/.)",
                "(S/.)",
                "(S/.)",
            ],
            widths,
        )
    )
    lines.append("-" * (sum(widths) + 3 * (len(widths) - 1)))

    grouped = _group_rows_by_distributor(rows)

    total_regulated_rows: list[G2SaleRow] = []
    total_free_rows: list[G2SaleRow] = []

    for distributor_code in _ordered_distributor_codes(grouped, distributor_order):
        distributor_rows = grouped[distributor_code]
        distributor_name = distributor_rows[0].distributor_name

        regulated_rows = [
            row for row in distributor_rows if row.client_type.strip().upper() == "R"
        ]
        free_rows = [
            row for row in distributor_rows if row.client_type.strip().upper() == "L"
        ]

        other_rows = [
            row
            for row in distributor_rows
            if row.client_type.strip().upper() not in {"R", "L"}
        ]

        lines.append("")
        lines.append(distributor_name)
        lines.append("-" * len(distributor_name))

        for row in distributor_rows:
            lines.append(_bar_row(row, widths))

        if regulated_rows:
            lines.append(_total_row("Total Cliente Regulado", regulated_rows, widths))
            total_regulated_rows.extend(regulated_rows)
        else:
            lines.append(_total_row("Total Cliente Regulado", [], widths))

        lines.append("Con Factor".ljust(widths[0]) + " | 1.00")

        if free_rows:
            lines.append(_total_row("Total Cliente Libre", free_rows, widths))
            total_free_rows.extend(free_rows)
        else:
            lines.append(_total_row("Total Cliente Libre", [], widths))

        if other_rows:
            lines.append(_total_row("Total Otros Clientes", other_rows, widths))

        lines.append(_total_row("- T o t a l -", distributor_rows, widths))

    lines.append("")
    lines.append("=" * (sum(widths) + 3 * (len(widths) - 1)))
    lines.append(_total_row("Total Clientes Regulados", total_regulated_rows, widths))
    lines.append("Con Factor".ljust(widths[0]) + " |")
    lines.append(_total_row("Total Clientes Libres", total_free_rows, widths))
    lines.append(_total_row("T o t a l  G e n e r a l", rows, widths))
    lines.append("=" * (sum(widths) + 3 * (len(widths) - 1)))
    lines.append("")
    lines.append("(1) : A nivel de Empresa Distribuidora, Sub Estación y Mercado Libre ó Regulado")
    lines.append("(2) : PPB = Precio de Potencia en la Barra ( S/. /kW )")
    lines.append("(3) : PEBP = Precio de Energía en la Barra en horas punta ( Céntimo de S/. /kWh )")
    lines.append("(4) : PEBF = Precio de Energía en la Barra en horas fuera de punta ( Céntimo de S/. /kWh )")
    lines.append("(5) : La Facturación no incluye IGV ni otros recargos")
    lines.append("")

    return "\n".join(lines)


def create_g2_txt(
    *,
    vepoen_path: Path,
    period: str,
    catalog_path: Path,
    output_path: Path | None = None,
) -> G2TxtResult:
    validation = validate_g2_sources(
        vepoen_path=vepoen_path,
        catalog_path=catalog_path,
        period=period,
    )

    if validation.has_errors:
        raise ValueError("Las fuentes G2 tienen errores. Revisa validate-g2-sources.")

    if output_path is None:
        output_path = default_g2_output_path(period)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        _g2_to_text(
            period=period,
            rows=validation.rows,
            distributor_order=validation.distributor_order,
        ),
        encoding="utf-8",
    )

    distributor_count = len({row.distributor_code for row in validation.rows})

    return G2TxtResult(
        period=period,
        output_path=output_path,
        row_count=len(validation.rows),
        distributor_count=distributor_count,
        warnings_count=len(validation.warnings),
    )