from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from pathlib import Path

from sisgen_automation.g1.sources import G1CentralBlock, G1GroupRow, validate_g1_sources

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


@dataclass(frozen=True)
class G1TxtResult:
    output_path: Path
    period: str
    hydro_central_count: int
    hydro_group_count: int
    thermal_central_count: int
    thermal_group_count: int
    warnings_count: int


def _default_report_date(period: str) -> date:
    year_text, month_text = period.split("-")
    year = int(year_text)
    month = int(month_text)

    if month == 12:
        return date(year + 1, 1, 20)

    return date(year, month + 1, 20)


def _format_decimal(value: Decimal, width: int, decimals: int = 3) -> str:
    return f"{value:.{decimals}f}".rjust(width)


def _format_blank(width: int) -> str:
    return " " * width


def _line() -> str:
    return "-" * 180


def _header(period: str, report_date: date) -> list[str]:
    year, month = period.split("-")

    return [
        f"Ministerio de Energía y Minas{'Fecha : ' + report_date.strftime('%d-%m-%Y'):>138}",
        "Dirección General de Electricidad".ljust(158) + "Pag   :   1",
        "",
        "Información de Empresas Generadoras y Autoproductores",
        "Datos de Generación",
        "",
        "Formato de Información Mensual".ljust(158) + "Formato G1",
        _line(),
        "",
        "Empresa : Emp. de Generación Eléctrica de Arequipa S. A.",
        f"Año : {year}    Mes : {MONTH_NAMES[month]}",
        "",
    ]


def _table_header(title: str) -> list[str]:
    return [
        title.center(180),
        _line(),
        (
            f"{'Nombre de la Central':32} {'Grupo':12} {'Est':>2} "
            f"{'Pot.Inst':>10} {'Pot.Efec':>10} "
            f"{'H.P.':>13} {'H.F.P.':>13} {'Total':>13} "
            f"{'Cons.Propio':>13} {'Prod.Neta':>13} {'Max.Dem':>13} "
            f"{'Mant.':>10} {'Oper.':>10} {'Salidas':>10} {'Cons.Lub':>10}"
        ),
        (
            f"{'':32} {'':12} {'':>2} "
            f"{'(MW)':>10} {'(MW)':>10} "
            f"{'(MWh)':>13} {'(MWh)':>13} {'(MWh)':>13} "
            f"{'(MWh)':>13} {'(MWh)':>13} {'(MW)':>13} "
            f"{'(h)':>10} {'(h)':>10} {'(h)':>10} {'':>10}"
        ),
        _line(),
    ]


def _group_line(row: G1GroupRow) -> str:
    lubricant = (
        _format_decimal(row.lubricant_consumption, 10)
        if row.lubricant_consumption is not None
        else _format_blank(10)
    )

    return (
        f"{row.central_name[:32]:32} "
        f"{row.group_name[:12]:12} "
        f"{row.status:>2} "
        f"{_format_decimal(row.installed_power, 10)} "
        f"{_format_decimal(row.effective_power, 10)} "
        f"{_format_decimal(row.peak_energy, 13)} "
        f"{_format_decimal(row.offpeak_energy, 13)} "
        f"{_format_decimal(row.gross_energy, 13)} "
        f"{_format_blank(13)} "
        f"{_format_blank(13)} "
        f"{_format_blank(13)} "
        f"{_format_decimal(row.maintenance_hours, 10, decimals=2)} "
        f"{_format_decimal(row.operation_hours, 10, decimals=2)} "
        f"{_format_decimal(row.forced_outage_hours, 10, decimals=2)} "
        f"{lubricant}"
    )


def _central_total_line(block: G1CentralBlock) -> str:
    lubricant = (
        _format_decimal(block.lubricant_consumption, 10)
        if block.section == "TERMO"
        else _format_blank(10)
    )

    return (
        f"{'Total Central':32} "
        f"{str(block.group_count):12} "
        f"{'':>2} "
        f"{_format_decimal(block.installed_power, 10)} "
        f"{_format_decimal(block.effective_power, 10)} "
        f"{_format_decimal(block.peak_energy, 13)} "
        f"{_format_decimal(block.offpeak_energy, 13)} "
        f"{_format_decimal(block.gross_energy, 13)} "
        f"{_format_decimal(block.dacoce.own_consumption, 13)} "
        f"{_format_decimal(block.dacoce.net_production, 13)} "
        f"{_format_decimal(block.dacoce.max_demand, 13)} "
        f"{_format_blank(10)} "
        f"{_format_blank(10)} "
        f"{_format_blank(10)} "
        f"{lubricant}"
    )


def _section_total_line(label: str, blocks: list[G1CentralBlock]) -> str:
    group_count = sum(block.group_count for block in blocks)
    installed_power = sum((block.installed_power for block in blocks), Decimal("0"))
    effective_power = sum((block.effective_power for block in blocks), Decimal("0"))
    peak_energy = sum((block.peak_energy for block in blocks), Decimal("0"))
    offpeak_energy = sum((block.offpeak_energy for block in blocks), Decimal("0"))
    gross_energy = sum((block.gross_energy for block in blocks), Decimal("0"))
    own_consumption = sum((block.dacoce.own_consumption for block in blocks), Decimal("0"))
    net_production = sum((block.dacoce.net_production for block in blocks), Decimal("0"))
    max_demand = sum((block.dacoce.max_demand for block in blocks), Decimal("0"))
    lubricant = sum((block.lubricant_consumption for block in blocks), Decimal("0"))

    return (
        f"{label:32} "
        f"{str(group_count):12} "
        f"{'':>2} "
        f"{_format_decimal(installed_power, 10)} "
        f"{_format_decimal(effective_power, 10)} "
        f"{_format_decimal(peak_energy, 13)} "
        f"{_format_decimal(offpeak_energy, 13)} "
        f"{_format_decimal(gross_energy, 13)} "
        f"{_format_decimal(own_consumption, 13)} "
        f"{_format_decimal(net_production, 13)} "
        f"{_format_decimal(max_demand, 13)} "
        f"{_format_blank(10)} "
        f"{_format_blank(10)} "
        f"{_format_blank(10)} "
        f"{_format_decimal(lubricant, 10)}"
    )


def _render_section(title: str, blocks: list[G1CentralBlock], total_label: str) -> list[str]:
    lines: list[str] = []
    lines.extend(_table_header(title))

    for block in blocks:
        for row in block.groups:
            lines.append(_group_line(row))

        lines.append(_line())
        lines.append(_central_total_line(block))
        lines.append(_line())

    lines.append(_section_total_line(total_label, blocks))
    lines.append(_line())
    lines.append("")

    return lines


def _render_txt(
    period: str,
    hydro_blocks: list[G1CentralBlock],
    thermal_blocks: list[G1CentralBlock],
    report_date: date,
) -> str:
    lines: list[str] = []

    lines.extend(_header(period=period, report_date=report_date))
    lines.extend(
        _render_section(
            title="CENTRALES HIDROELECTRICAS",
            blocks=hydro_blocks,
            total_label="T o t a l   H i d r o",
        )
    )
    lines.extend(
        _render_section(
            title="CENTRALES TERMOELECTRICAS",
            blocks=thermal_blocks,
            total_label="T o t a l   T e r m o",
        )
    )

    all_blocks = [*hydro_blocks, *thermal_blocks]
    lines.append(_section_total_line("T o t a l   G e n e r a l", all_blocks))
    lines.append(_line())
    lines.append("")
    lines.append("Nota (2) : OP = Operativo")
    lines.append("NO = No Operativo")
    lines.append("Nota (3) : Información suministrada sólo por las empresas que pertenecen a un COES")
    lines.append("")

    return "\n".join(lines)


def create_g1_txt(
    cenhid_path: Path,
    center_path: Path,
    dacoce_path: Path,
    period: str,
    cenhid_catalog_path: Path,
    center_catalog_path: Path,
    output_path: Path | None = None,
    report_date: date | None = None,
) -> G1TxtResult:
    validation_result = validate_g1_sources(
        cenhid_path=cenhid_path,
        center_path=center_path,
        dacoce_path=dacoce_path,
        period=period,
        cenhid_catalog_path=cenhid_catalog_path,
        center_catalog_path=center_catalog_path,
    )

    if validation_result.has_errors:
        raise ValueError(
            "Las fuentes CENHID + CENTER + DACOCE tienen errores. "
            "Corrige las fuentes antes de generar el G1."
        )

    if output_path is None:
        output_path = Path("reports") / f"G1_{period.replace('-', '_')}.txt"

    if report_date is None:
        report_date = _default_report_date(period)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        _render_txt(
            period=period,
            hydro_blocks=validation_result.hydro_blocks,
            thermal_blocks=validation_result.thermal_blocks,
            report_date=report_date,
        ),
        encoding="utf-8-sig",
    )

    return G1TxtResult(
        output_path=output_path,
        period=period,
        hydro_central_count=len(validation_result.hydro_blocks),
        hydro_group_count=validation_result.hydro_group_count,
        thermal_central_count=len(validation_result.thermal_blocks),
        thermal_group_count=validation_result.thermal_group_count,
        warnings_count=len(validation_result.warnings),
    )