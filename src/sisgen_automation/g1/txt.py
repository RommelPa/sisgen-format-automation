from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Literal

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

Align = Literal["left", "center", "right"]

THERMAL_WIDTHS = [32, 3, 17, 2, 10, 10, 13, 13, 13, 13, 13, 13, 10, 11, 10, 5, 10, 12]
HYDRO_WIDTHS = [32, 16, 2, 10, 10, 13, 13, 13, 13, 13, 13, 10, 11, 10]

THERMAL_ALIGNS: list[Align] = [
    "left",
    "left",
    "left",
    "left",
    "right",
    "right",
    "right",
    "right",
    "right",
    "right",
    "right",
    "right",
    "right",
    "right",
    "right",
    "left",
    "right",
    "right",
]

HYDRO_ALIGNS: list[Align] = [
    "left",
    "left",
    "left",
    "right",
    "right",
    "right",
    "right",
    "right",
    "right",
    "right",
    "right",
    "right",
    "right",
    "right",
]


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


def _full_width(widths: list[int]) -> int:
    return sum(widths) + len(widths) + 1


def _fit(text: str, width: int, align: Align = "left") -> str:
    value = str(text)

    if len(value) > width:
        value = value[:width]

    if align == "right":
        return value.rjust(width)

    if align == "center":
        return value.center(width)

    return value.ljust(width)


def _box_rule(widths: list[int], left: str, middle: str, right: str) -> str:
    return left + middle.join("─" * width for width in widths) + right


def _box_title(title: str, widths: list[int]) -> list[str]:
    total_width = _full_width(widths)
    inner_width = total_width - 2

    return [
        "┌" + "─" * inner_width + "┐",
        "│" + title.center(inner_width) + "│",
        _box_rule(widths, "├", "┬", "┤"),
    ]


def _box_row(
    values: list[str],
    widths: list[int],
    aligns: list[Align] | None = None,
) -> str:
    if aligns is None:
        aligns = ["left"] * len(widths)

    cells = [
        _fit(value, width, align)
        for value, width, align in zip(values, widths, aligns)
    ]

    return "│" + "│".join(cells) + "│"


def _box_mid(widths: list[int]) -> str:
    return _box_rule(widths, "├", "┼", "┤")


def _box_bottom(widths: list[int]) -> str:
    return _box_rule(widths, "└", "┴", "┘")


def _num(value: Decimal, width: int, decimals: int = 3) -> str:
    return f"{value:.{decimals}f}".rjust(width)


def _num2(value: Decimal, width: int) -> str:
    return f"{value:.2f}".rjust(width)


def _blank(width: int) -> str:
    return " " * width


def _header(period: str, report_date: date) -> list[str]:
    year, month = period.split("-")

    return [
        f"Ministerio de Energía y Minas{'Fecha : ' + report_date.strftime('%d-%m-%Y'):>182}",
        "Dirección General de Electricidad".ljust(205) + "Pag   :   1",
        "",
        "Información de Empresas Generadoras y Autoproductores",
        "Datos de Generación",
        "",
        "Formato de Información Mensual".ljust(207) + "Formato G1",
        "─" * 231,
        "",
        *_company_period_box(year=year, month=MONTH_NAMES[month]),
        "",
    ]


def _company_period_box(year: str, month: str) -> list[str]:
    company_text = "Empresa : Emp. de Generación Eléctrica de Arequipa S. A."
    company_width = 88
    year_width = 10
    month_width = 17
    filler_width = company_width - year_width - month_width - 2

    return [
        "┌" + "─" * company_width + "┐",
        "│" + _fit(company_text, company_width) + "│",
        "├" + "─" * year_width + "┬" + "─" * month_width + "┬" + "─" * filler_width + "┘",
        "│" + _fit(f"Año :{year}", year_width) + "│" + _fit(f" Mes : {month}", month_width) + "│",
        "└" + "─" * year_width + "┴" + "─" * month_width + "┘",
        "",
    ]


def _thermal_header() -> list[str]:
    return [
        *_box_title("C E N T R A L E S   T E R M O E L E C T R I C A S", THERMAL_WIDTHS),
        _box_row(
            [
                "",
                "",
                "GRUPO",
                "",
                "POTENCIA",
                "",
                "PROCCION",
                "BRUTA",
                "",
                "Consumo",
                "Producción",
                "Máxima",
                "Horas de",
                "Horas",
                "Horas de",
                "Consumo de",
                "",
                "Consumo de",
            ],
            THERMAL_WIDTHS,
            ["center"] * len(THERMAL_WIDTHS),
        ),
        _box_row(
            [
                "Nombre de la Central",
                "Tipo",
                "Nombre",
                "Est.",
                "Instalada",
                "Efectiva",
                "H.P. (3)",
                "H.F.P. (3)",
                "Total",
                "Propio",
                "Neta",
                "Demanda",
                "Mant.",
                "de",
                "Salidas",
                "Tipo",
                "Cantidad",
                "Lubricante",
            ],
            THERMAL_WIDTHS,
            ["center"] * len(THERMAL_WIDTHS),
        ),
        _box_row(
            [
                "",
                "(1)",
                "o Número",
                "(2)",
                "(MW)",
                "(MW)",
                "(MWh)",
                "(MWh)",
                "(MWh)",
                "(MWh)",
                "(MWh)",
                "(MW)",
                "Program.",
                "Operación",
                "Forzadas",
                "(4)",
                "",
                "(Galones)",
            ],
            THERMAL_WIDTHS,
            ["center"] * len(THERMAL_WIDTHS),
        ),
        _box_mid(THERMAL_WIDTHS),
    ]


def _hydro_header() -> list[str]:
    return [
        *_box_title("C E N T R A L E S   H I D R O E L E C T R I C A S", HYDRO_WIDTHS),
        _box_row(
            [
                "",
                "GRUPO",
                "",
                "POTENCIA",
                "",
                "PRODUCCION",
                "BRUTA",
                "",
                "Consumo",
                "Producción",
                "Máxima",
                "Horas de",
                "Horas",
                "Horas de",
            ],
            HYDRO_WIDTHS,
            ["center"] * len(HYDRO_WIDTHS),
        ),
        _box_row(
            [
                "Nombre de la Central",
                "Nombre",
                "Estado",
                "Instalada",
                "Efectiva",
                "H.P. (3)",
                "H.F.P. (3)",
                "Total",
                "Propio",
                "Neta",
                "Demanda",
                "Mant.",
                "de",
                "Salidas",
            ],
            HYDRO_WIDTHS,
            ["center"] * len(HYDRO_WIDTHS),
        ),
        _box_row(
            [
                "",
                "o Número",
                "(2)",
                "(MW)",
                "(MW)",
                "(MWh)",
                "(MWh)",
                "(MWh)",
                "(MWh)",
                "(MWh)",
                "(MW)",
                "Program.",
                "Operación",
                "Forzadas",
            ],
            HYDRO_WIDTHS,
            ["center"] * len(HYDRO_WIDTHS),
        ),
        _box_mid(HYDRO_WIDTHS),
    ]


def _thermal_group_row(row: G1GroupRow) -> str:
    return _box_row(
        [
            row.central_name,
            row.ctipgru,
            row.group_name,
            row.status,
            _num(row.installed_power, 10),
            _num(row.effective_power, 10),
            _num(row.peak_energy, 13),
            _num(row.offpeak_energy, 13),
            _num(row.gross_energy, 13),
            _blank(13),
            _blank(13),
            _blank(13),
            _num2(row.maintenance_hours, 10),
            _num2(row.operation_hours, 11),
            _num2(row.forced_outage_hours, 10),
            "",
            "",
            _num2(row.lubricant_consumption or Decimal("0"), 12),
        ],
        THERMAL_WIDTHS,
        THERMAL_ALIGNS,
    )


def _hydro_group_row(row: G1GroupRow) -> str:
    return _box_row(
        [
            row.central_name,
            row.group_name,
            row.status,
            _num(row.installed_power, 10),
            _num(row.effective_power, 10),
            _num(row.peak_energy, 13),
            _num(row.offpeak_energy, 13),
            _num(row.gross_energy, 13),
            _blank(13),
            _blank(13),
            _blank(13),
            _num2(row.maintenance_hours, 10),
            _num2(row.operation_hours, 11),
            _num2(row.forced_outage_hours, 10),
        ],
        HYDRO_WIDTHS,
        HYDRO_ALIGNS,
    )


def _thermal_total_row(label: str, block: G1CentralBlock | None, blocks: list[G1CentralBlock] | None = None) -> str:
    if block is not None:
        source_blocks = [block]
        group_count = block.group_count
    else:
        source_blocks = blocks or []
        group_count = sum(item.group_count for item in source_blocks)

    installed_power = sum((item.installed_power for item in source_blocks), Decimal("0"))
    effective_power = sum((item.effective_power for item in source_blocks), Decimal("0"))
    peak_energy = sum((item.peak_energy for item in source_blocks), Decimal("0"))
    offpeak_energy = sum((item.offpeak_energy for item in source_blocks), Decimal("0"))
    gross_energy = sum((item.gross_energy for item in source_blocks), Decimal("0"))
    own_consumption = sum((item.dacoce.own_consumption for item in source_blocks), Decimal("0"))
    net_production = sum((item.dacoce.net_production for item in source_blocks), Decimal("0"))
    max_demand = sum((item.dacoce.max_demand for item in source_blocks), Decimal("0"))
    lubricant = sum((item.lubricant_consumption for item in source_blocks), Decimal("0"))

    return _box_row(
        [
            label,
            "",
            str(group_count),
            "",
            _num(installed_power, 10),
            _num(effective_power, 10),
            _num(peak_energy, 13),
            _num(offpeak_energy, 13),
            _num(gross_energy, 13),
            _num(own_consumption, 13),
            _num(net_production, 13),
            _num(max_demand, 13),
            "",
            "",
            "",
            "",
            "",
            _num2(lubricant, 12),
        ],
        THERMAL_WIDTHS,
        THERMAL_ALIGNS,
    )


def _hydro_total_row(label: str, block: G1CentralBlock | None, blocks: list[G1CentralBlock] | None = None) -> str:
    if block is not None:
        source_blocks = [block]
        group_count = block.group_count
    else:
        source_blocks = blocks or []
        group_count = sum(item.group_count for item in source_blocks)

    installed_power = sum((item.installed_power for item in source_blocks), Decimal("0"))
    effective_power = sum((item.effective_power for item in source_blocks), Decimal("0"))
    peak_energy = sum((item.peak_energy for item in source_blocks), Decimal("0"))
    offpeak_energy = sum((item.offpeak_energy for item in source_blocks), Decimal("0"))
    gross_energy = sum((item.gross_energy for item in source_blocks), Decimal("0"))
    own_consumption = sum((item.dacoce.own_consumption for item in source_blocks), Decimal("0"))
    net_production = sum((item.dacoce.net_production for item in source_blocks), Decimal("0"))
    max_demand = sum((item.dacoce.max_demand for item in source_blocks), Decimal("0"))

    return _box_row(
        [
            label,
            str(group_count),
            "",
            _num(installed_power, 10),
            _num(effective_power, 10),
            _num(peak_energy, 13),
            _num(offpeak_energy, 13),
            _num(gross_energy, 13),
            _num(own_consumption, 13),
            _num(net_production, 13),
            _num(max_demand, 13),
            "",
            "",
            "",
        ],
        HYDRO_WIDTHS,
        HYDRO_ALIGNS,
    )


def _render_thermal_section(blocks: list[G1CentralBlock]) -> list[str]:
    lines = _thermal_header()

    for block in blocks:
        for row in block.groups:
            lines.append(_thermal_group_row(row))

        lines.append(_box_mid(THERMAL_WIDTHS))
        lines.append(_thermal_total_row("Total Central", block=block))
        lines.append(_box_mid(THERMAL_WIDTHS))

    lines.append(_thermal_total_row("  T o t a l   G e n e r a l", block=None, blocks=blocks))
    lines.append(_box_bottom(THERMAL_WIDTHS))
    lines.append("")

    return lines


def _render_hydro_section(blocks: list[G1CentralBlock]) -> list[str]:
    lines = _hydro_header()

    for block in blocks:
        for row in block.groups:
            lines.append(_hydro_group_row(row))

        lines.append(_box_mid(HYDRO_WIDTHS))
        lines.append(_hydro_total_row("Total Central", block=block))
        lines.append(_box_mid(HYDRO_WIDTHS))

    lines.append(_hydro_total_row("  T o t a l   G e n e r a l", block=None, blocks=blocks))
    lines.append(_box_bottom(HYDRO_WIDTHS))
    lines.append("")

    return lines


def _thermal_notes() -> list[str]:
    return [
        "Nota (1) : EL = Electrogeno                   Nota (2) : OP = Operativo                  Nota (3) : Información suministrada                Nota (4) : D1 = Diesel 1     ( Galones )",
        "TV = Turbo Vapor                              NO = No Operativo                          sólo por las empresas                              D2 = Diesel 2     ( Galones )",
        "TG = Turbo Gas                                                                           que pertenecen a un COES                           R5 = Residual 5   ( Galones )",
        "CC = Ciclo combinado                                                                                                                        R6 = Residual 6   ( Galones )",
        "OT = Otros                                                                                                                                  RQ = Residual 500 ( Galones )",
        "CA = Carbón       ( Toneladas )",
        "GN = Gas Natural  ( Metros Cúbicos )",
        "BZ = Bagazo       ( Toneladas )",
        "NE = No Especificado",
        "",
    ]


def _hydro_notes() -> list[str]:
    return [
        "Nota (2) : OP = Operativo                  Nota (3) : Información suministrada",
        "NO = No Operativo                          sólo por las empresas",
        "que pertenecen a un COES",
        "",
    ]


def _render_txt(
    period: str,
    hydro_blocks: list[G1CentralBlock],
    thermal_blocks: list[G1CentralBlock],
    report_date: date,
) -> str:
    lines: list[str] = []

    lines.extend(_header(period=period, report_date=report_date))
    lines.extend(_render_thermal_section(thermal_blocks))
    lines.extend(_thermal_notes())
    lines.extend(_render_hydro_section(hydro_blocks))
    lines.extend(_hydro_notes())

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