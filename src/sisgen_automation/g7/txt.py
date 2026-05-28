from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from pathlib import Path

from sisgen_automation.g7.catalog import load_g7_catalog
from sisgen_automation.g7.sources import (
    G7EnergyRow,
    G7NetCommitmentRow,
    G7PowerTransferRow,
    G7TransferValuationRow,
    validate_g7_sources,
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


@dataclass(frozen=True)
class G7TxtResult:
    period: str
    output_path: Path
    purchases_count: int
    sales_count: int
    net_commitments_count: int
    power_transfers_count: int
    transfer_valuations_count: int
    warnings_count: int


def default_g7_output_path(period: str) -> Path:
    return Path("reports") / "g7" / f"G7_{period.replace('-', '_')}.txt"


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


def _format_decimal(value: Decimal, decimals: int = 5) -> str:
    return f"{value:.{decimals}f}"


def _line(char: str = "-", width: int = 140) -> str:
    return char * width


def _row(values: list[str], widths: list[int]) -> str:
    cells = []

    for value, width in zip(values, widths, strict=True):
        text = str(value)

        if len(text) > width:
            text = text[:width]

        cells.append(text.ljust(width))

    return " | ".join(cells)


def _energy_lines(*, title: str, rows: list[G7EnergyRow]) -> list[str]:
    widths = [12, 45, 14, 14, 14, 14, 14, 14]

    lines = [
        title,
        _line(),
        _row(
            [
                "Código",
                "Empresa",
                "Energía HP",
                "Energía HFP",
                "Energía Total",
                "Valor HP",
                "Valor HFP",
                "Valor Total",
            ],
            widths,
        ),
        _line(),
    ]

    for row in rows:
        lines.append(
            _row(
                [
                    row.ccodgen,
                    row.cdesgen,
                    _format_decimal(row.nenhopu),
                    _format_decimal(row.nenfuho),
                    _format_decimal(row.nenetot),
                    _format_decimal(row.nvahopu),
                    _format_decimal(row.nvafuho),
                    _format_decimal(row.nvaltot),
                ],
                widths,
            )
        )

    lines.append(_line())
    return lines


def _net_commitment_lines(rows: list[G7NetCommitmentRow]) -> list[str]:
    widths = [12, 55, 18]

    lines = [
        "COMPROMISOS NETOS",
        _line(),
        _row(
            [
                "Código",
                "Empresa",
                "Compromiso Neto",
            ],
            widths,
        ),
        _line(),
    ]

    for row in rows:
        lines.append(
            _row(
                [
                    row.ccoddis,
                    row.cnomdis,
                    _format_decimal(row.ncomnet),
                ],
                widths,
            )
        )

    lines.append(_line())
    return lines


def _power_transfer_lines(rows: list[G7PowerTransferRow]) -> list[str]:
    widths = [12, 55, 18]

    lines = [
        "TRANSFERENCIAS DE POTENCIA",
        _line(),
        _row(
            [
                "Código",
                "Empresa",
                "Transferencia",
            ],
            widths,
        ),
        _line(),
    ]

    for row in rows:
        lines.append(
            _row(
                [
                    row.ccodgen,
                    row.cnomgen,
                    _format_decimal(row.ntrapot),
                ],
                widths,
            )
        )

    lines.append(_line())
    return lines


def _transfer_valuation_lines(rows: list[G7TransferValuationRow]) -> list[str]:
    widths = [12, 55, 18]

    lines = [
        "VALORIZACIÓN DE TRANSFERENCIAS",
        _line(),
        _row(
            [
                "Código",
                "Empresa",
                "Valorización",
            ],
            widths,
        ),
        _line(),
    ]

    for row in rows:
        lines.append(
            _row(
                [
                    row.ccodgen,
                    row.cnomgen,
                    _format_decimal(row.nvaltra),
                ],
                widths,
            )
        )

    lines.append(_line())
    return lines


def create_g7_txt(
    *,
    comene_path: Path,
    venene_path: Path,
    comnet_path: Path,
    traene_path: Path,
    valene_path: Path,
    period: str,
    catalog_path: Path,
    output_path: Path | None = None,
) -> G7TxtResult:
    validation = validate_g7_sources(
        comene_path=comene_path,
        venene_path=venene_path,
        comnet_path=comnet_path,
        traene_path=traene_path,
        valene_path=valene_path,
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
            "Las fuentes G7 tienen errores. Revisa validate-g7-sources antes de generar G7."
            f"\n{preview}"
        )

    catalog = load_g7_catalog(catalog_path)
    year, month = _period_parts(period)

    if output_path is None:
        output_path = default_g7_output_path(period)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    today = date.today().strftime("%d-%m-%Y")
    month_name = MONTH_NAMES_ES[month]

    lines = [
        f"Ministerio de Energía y Minas{'Fecha : ' + today:>82}",
        "Dirección General de Electricidad",
        "Información de Empresas Generadoras y Autoproductores",
        "Compra, venta, compromisos y transferencias de energía",
        "Formato de Información Mensual Formato G7",
        _line("="),
        f"Empresa : {catalog.company.name}",
        f"Año : {year}    Mes : {month_name}",
        _line("="),
        "",
        *_energy_lines(title="COMPRAS DE ENERGÍA", rows=validation.purchases),
        "",
        *_energy_lines(title="VENTAS DE ENERGÍA", rows=validation.sales),
        "",
        *_net_commitment_lines(validation.net_commitments),
        "",
        *_power_transfer_lines(validation.power_transfers),
        "",
        *_transfer_valuation_lines(validation.transfer_valuations),
        "",
    ]

    output_path.write_text("\n".join(lines), encoding="utf-8-sig")

    return G7TxtResult(
        period=period,
        output_path=output_path,
        purchases_count=len(validation.purchases),
        sales_count=len(validation.sales),
        net_commitments_count=len(validation.net_commitments),
        power_transfers_count=len(validation.power_transfers),
        transfer_valuations_count=len(validation.transfer_valuations),
        warnings_count=len(validation.warnings),
    )