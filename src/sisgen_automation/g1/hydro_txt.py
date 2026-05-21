from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

from dbfread import DBF  # type: ignore[import-untyped]

from sisgen_automation.cenhid.catalog import load_cenhid_catalog
from sisgen_automation.cenhid.template import parse_period
from sisgen_automation.g1.hydro_sources import validate_g1_hydro_sources

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

def _default_report_date(period: str) -> date:
    year_text, month_text = period.split("-")
    year = int(year_text)
    month = int(month_text)

    if month == 12:
        return date(year + 1, 1, 20)

    return date(year, month + 1, 20)

@dataclass(frozen=True)
class HydroGroupReportRow:
    ccodcon: str
    central_name: str
    group_name: str
    status: str
    installed_power: Decimal
    effective_power: Decimal
    peak_energy: Decimal
    offpeak_energy: Decimal
    gross_energy: Decimal
    maintenance_hours: Decimal
    operation_hours: Decimal
    forced_outage_hours: Decimal


@dataclass(frozen=True)
class DacoceHydroRow:
    ccodcon: str
    own_consumption: Decimal
    net_production: Decimal
    max_demand: Decimal


@dataclass(frozen=True)
class HydroCentralReportBlock:
    ccodcon: str
    central_name: str
    groups: list[HydroGroupReportRow]
    dacoce: DacoceHydroRow

    @property
    def group_count(self) -> int:
        return len(self.groups)

    @property
    def installed_power(self) -> Decimal:
        return sum((row.installed_power for row in self.groups), Decimal("0"))

    @property
    def effective_power(self) -> Decimal:
        return sum((row.effective_power for row in self.groups), Decimal("0"))

    @property
    def peak_energy(self) -> Decimal:
        return sum((row.peak_energy for row in self.groups), Decimal("0"))

    @property
    def offpeak_energy(self) -> Decimal:
        return sum((row.offpeak_energy for row in self.groups), Decimal("0"))

    @property
    def gross_energy(self) -> Decimal:
        return sum((row.gross_energy for row in self.groups), Decimal("0"))


@dataclass(frozen=True)
class G1HydroTxtResult:
    output_path: Path
    period: str
    central_count: int
    group_count: int
    warnings_count: int


def _clean_text(value: object) -> str:
    if value is None:
        return ""

    return str(value).strip()


def _clean_upper(value: object) -> str:
    return _clean_text(value).upper()


def _to_decimal(value: object) -> Decimal:
    if value is None:
        raise ValueError("Valor numérico vacío.")

    text = str(value).strip()

    if not text:
        raise ValueError("Valor numérico vacío.")

    try:
        return Decimal(text)
    except InvalidOperation as error:
        raise ValueError(f"Valor numérico inválido: {value}") from error


def _format_decimal(value: Decimal, width: int, decimals: int = 3) -> str:
    return f"{value:.{decimals}f}".rjust(width)


def _format_blank(width: int) -> str:
    return " " * width


def _display_central_name(raw_name: str) -> str:
    roman_tokens = {"I", "II", "III", "IV", "V", "VI", "VII", "VIII"}

    parts = []
    for token in raw_name.strip().split():
        upper_token = token.upper()
        if upper_token in roman_tokens:
            parts.append(upper_token)
        else:
            parts.append(token.title())

    display_name = " ".join(parts)

    if display_name.upper().startswith("CHARCANI"):
        return f"C. H. {display_name}"

    return display_name


def _group_order(group_name: str) -> tuple[int, str]:
    text = group_name.strip().upper()

    if text.startswith("G-"):
        number_text = text.replace("G-", "", 1)
        if number_text.isdigit():
            return int(number_text), text

    return 999, text


def _status_to_g1(value: object) -> str:
    status = _clean_upper(value)

    if status == "S":
        return "OP"

    if status == "N":
        return "NO"

    return status


def _read_cenhid_group_rows(
    cenhid_path: Path,
    period: str,
    catalog_path: Path,
) -> list[HydroGroupReportRow]:
    year, month = parse_period(period)
    catalog = load_cenhid_catalog(catalog_path)
    table = DBF(str(cenhid_path), load=True, char_decode_errors="ignore")

    rows: list[HydroGroupReportRow] = []

    for record in table:
        if _clean_text(record.get("CANOREG")) != year:
            continue

        if _clean_text(record.get("CMESREG")) != month:
            continue

        if _clean_upper(record.get("CTIPGRU")) != "HI":
            continue

        ccodcon = _clean_text(record.get("CCODCON"))
        cnomnum = _clean_text(record.get("CNOMNUM"))
        unit = catalog.get((ccodcon, cnomnum))

        if unit is None:
            central_name = ccodcon
        else:
            central_name = _display_central_name(unit.central)

        rows.append(
            HydroGroupReportRow(
                ccodcon=ccodcon,
                central_name=central_name,
                group_name=cnomnum,
                status=_status_to_g1(record.get("CESTGRU")),
                installed_power=_to_decimal(record.get("NPOTINS")),
                effective_power=_to_decimal(record.get("NPOTEFE")),
                peak_energy=_to_decimal(record.get("NHORPUN")),
                offpeak_energy=_to_decimal(record.get("NFUHOPU")),
                gross_energy=_to_decimal(record.get("NTOPRBR")),
                maintenance_hours=_to_decimal(record.get("CHRSMAN")),
                operation_hours=_to_decimal(record.get("CHRSOPE")),
                forced_outage_hours=_to_decimal(record.get("CHRSSAL")),
            )
        )

    return rows


def _read_dacoce_hydro_rows(
    dacoce_path: Path,
    period: str,
) -> dict[str, DacoceHydroRow]:
    year, month = parse_period(period)
    table = DBF(str(dacoce_path), load=True, char_decode_errors="ignore")

    rows: dict[str, DacoceHydroRow] = {}

    for record in table:
        if _clean_text(record.get("CANOREG")) != year:
            continue

        if _clean_text(record.get("CMESREG")) != month:
            continue

        if _clean_upper(record.get("CTIPCEN")) != "H":
            continue

        ccodcon = _clean_text(record.get("CCODCON"))

        if not ccodcon:
            continue

        rows[ccodcon] = DacoceHydroRow(
            ccodcon=ccodcon,
            own_consumption=_to_decimal(record.get("NCONPRO")),
            net_production=_to_decimal(record.get("NPRONET")),
            max_demand=_to_decimal(record.get("NMAXDEM")),
        )

    return rows


def _build_blocks(
    cenhid_rows: list[HydroGroupReportRow],
    dacoce_rows: dict[str, DacoceHydroRow],
) -> list[HydroCentralReportBlock]:
    rows_by_central: dict[str, list[HydroGroupReportRow]] = {}

    for row in cenhid_rows:
        rows_by_central.setdefault(row.ccodcon, []).append(row)

    blocks: list[HydroCentralReportBlock] = []

    for ccodcon in sorted(rows_by_central):
        group_rows = sorted(rows_by_central[ccodcon], key=lambda item: _group_order(item.group_name))
        first_group = group_rows[0]
        dacoce = dacoce_rows.get(ccodcon)

        if dacoce is None:
            raise ValueError(f"No existe DACOCE hidro para la central {ccodcon}.")

        blocks.append(
            HydroCentralReportBlock(
                ccodcon=ccodcon,
                central_name=first_group.central_name,
                groups=group_rows,
                dacoce=dacoce,
            )
        )

    return blocks


def _line() -> str:
    return "-" * 162


def _header(period: str, report_date: date) -> list[str]:
    year, month = period.split("-")
    return [
        f"Ministerio de Energía y Minas{'Fecha : ' + report_date.strftime('%d-%m-%Y'):>120}",
        "Dirección General de Electricidad".ljust(140) + "Pag   :   1",
        "",
        "Información de Empresas Generadoras y Autoproductores",
        "Datos de Generación",
        "",
        "Formato de Información Mensual".ljust(140) + "Formato G1",
        _line(),
        "",
        "Empresa : Emp. de Generación Eléctrica de Arequipa S. A.",
        f"Año : {year}    Mes : {MONTH_NAMES[month]}",
        "",
    ]


def _hydro_table_header() -> list[str]:
    return [
        "CENTRALES HIDROELECTRICAS".center(162),
        _line(),
        (
            f"{'Nombre de la Central':32} {'Grupo':10} {'Est':>2} "
            f"{'Pot.Inst':>10} {'Pot.Efec':>10} "
            f"{'H.P.':>13} {'H.F.P.':>13} {'Total':>13} "
            f"{'Cons.Propio':>13} {'Prod.Neta':>13} {'Max.Dem':>13} "
            f"{'Mant.':>10} {'Oper.':>10} {'Salidas':>10}"
        ),
        (
            f"{'':32} {'':10} {'':>2} "
            f"{'(MW)':>10} {'(MW)':>10} "
            f"{'(MWh)':>13} {'(MWh)':>13} {'(MWh)':>13} "
            f"{'(MWh)':>13} {'(MWh)':>13} {'(MW)':>13} "
            f"{'(h)':>10} {'(h)':>10} {'(h)':>10}"
        ),
        _line(),
    ]


def _group_line(row: HydroGroupReportRow) -> str:
    return (
        f"{row.central_name[:32]:32} "
        f"{row.group_name[:10]:10} "
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
        f"{_format_decimal(row.forced_outage_hours, 10, decimals=2)}"
    )


def _central_total_line(block: HydroCentralReportBlock) -> str:
    return (
        f"{'Total Central':32} "
        f"{str(block.group_count):10} "
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
        f"{_format_blank(10)}"
    )


def _general_total_line(blocks: list[HydroCentralReportBlock]) -> str:
    group_count = sum(block.group_count for block in blocks)
    installed_power = sum((block.installed_power for block in blocks), Decimal("0"))
    effective_power = sum((block.effective_power for block in blocks), Decimal("0"))
    peak_energy = sum((block.peak_energy for block in blocks), Decimal("0"))
    offpeak_energy = sum((block.offpeak_energy for block in blocks), Decimal("0"))
    gross_energy = sum((block.gross_energy for block in blocks), Decimal("0"))
    own_consumption = sum((block.dacoce.own_consumption for block in blocks), Decimal("0"))
    net_production = sum((block.dacoce.net_production for block in blocks), Decimal("0"))
    max_demand = sum((block.dacoce.max_demand for block in blocks), Decimal("0"))

    return (
        f"{'T o t a l   G e n e r a l':32} "
        f"{str(group_count):10} "
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
        f"{_format_blank(10)}"
    )


def _render_txt(period: str, blocks: list[HydroCentralReportBlock], report_date: date) -> str:
    lines: list[str] = []

    lines.extend(_header(period=period, report_date=report_date))
    lines.extend(_hydro_table_header())

    for block in blocks:
        for row in block.groups:
            lines.append(_group_line(row))

        lines.append(_line())
        lines.append(_central_total_line(block))
        lines.append(_line())

    lines.append(_general_total_line(blocks))
    lines.append(_line())
    lines.append("")
    lines.append("Nota (2) : OP = Operativo")
    lines.append("NO = No Operativo")
    lines.append("Nota (3) : Información suministrada sólo por las empresas que pertenecen a un COES")
    lines.append("")

    return "\n".join(lines)


def create_g1_hydro_txt(
    cenhid_path: Path,
    dacoce_path: Path,
    period: str,
    catalog_path: Path,
    output_path: Path | None = None,
    report_date: date | None = None,
) -> G1HydroTxtResult:
    validation_result = validate_g1_hydro_sources(
        cenhid_path=cenhid_path,
        dacoce_path=dacoce_path,
        period=period,
        catalog_path=catalog_path,
    )

    if validation_result.has_errors:
        raise ValueError(
            "Las fuentes CENHID + DACOCE tienen errores. "
            "Corrige las fuentes antes de generar G1 hidro."
        )

    if output_path is None:
        output_path = Path("reports") / f"G1_HYDRO_{period.replace('-', '_')}.txt"

    if report_date is None:
        report_date = _default_report_date(period)

    cenhid_rows = _read_cenhid_group_rows(
        cenhid_path=cenhid_path,
        period=period,
        catalog_path=catalog_path,
    )
    dacoce_rows = _read_dacoce_hydro_rows(
        dacoce_path=dacoce_path,
        period=period,
    )
    blocks = _build_blocks(
        cenhid_rows=cenhid_rows,
        dacoce_rows=dacoce_rows,
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        _render_txt(period=period, blocks=blocks, report_date=report_date),
        encoding="utf-8",
    )

    return G1HydroTxtResult(
        output_path=output_path,
        period=period,
        central_count=len(blocks),
        group_count=sum(block.group_count for block in blocks),
        warnings_count=len(validation_result.warnings),
    )