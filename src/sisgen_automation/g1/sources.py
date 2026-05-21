from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Literal

from dbfread import DBF  # type: ignore[import-untyped]

from sisgen_automation.cenhid.catalog import load_cenhid_catalog
from sisgen_automation.cenhid.template import parse_period
from sisgen_automation.center.catalog import load_center_catalog

IssueSeverity = Literal["ERROR", "WARNING"]
SectionName = Literal["HIDRO", "TERMO"]

NET_PRODUCTION_TOLERANCE = Decimal("0.05")


@dataclass(frozen=True)
class G1SourceIssue:
    severity: IssueSeverity
    section: str
    source: str
    field: str | None
    message: str
    value: str | None = None


@dataclass(frozen=True)
class G1GroupRow:
    section: SectionName
    ccodcon: str
    central_name: str
    ctipgru: str
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
    lubricant_consumption: Decimal | None = None


@dataclass(frozen=True)
class G1DacoceRow:
    ccodcon: str
    center_type: Literal["H", "T"]
    own_consumption: Decimal
    net_production: Decimal
    max_demand: Decimal


@dataclass(frozen=True)
class G1CentralBlock:
    section: SectionName
    ccodcon: str
    central_name: str
    groups: list[G1GroupRow]
    dacoce: G1DacoceRow

    @property
    def group_count(self) -> int:
        return len(self.groups)

    @property
    def installed_power(self) -> Decimal:
        return sum((item.installed_power for item in self.groups), Decimal("0"))

    @property
    def effective_power(self) -> Decimal:
        return sum((item.effective_power for item in self.groups), Decimal("0"))

    @property
    def peak_energy(self) -> Decimal:
        return sum((item.peak_energy for item in self.groups), Decimal("0"))

    @property
    def offpeak_energy(self) -> Decimal:
        return sum((item.offpeak_energy for item in self.groups), Decimal("0"))

    @property
    def gross_energy(self) -> Decimal:
        return sum((item.gross_energy for item in self.groups), Decimal("0"))

    @property
    def maintenance_hours(self) -> Decimal:
        return sum((item.maintenance_hours for item in self.groups), Decimal("0"))

    @property
    def operation_hours(self) -> Decimal:
        return sum((item.operation_hours for item in self.groups), Decimal("0"))

    @property
    def forced_outage_hours(self) -> Decimal:
        return sum((item.forced_outage_hours for item in self.groups), Decimal("0"))

    @property
    def lubricant_consumption(self) -> Decimal:
        return sum(
            (
                item.lubricant_consumption
                for item in self.groups
                if item.lubricant_consumption is not None
            ),
            Decimal("0"),
        )


@dataclass(frozen=True)
class G1SourcesValidationResult:
    cenhid_path: Path
    center_path: Path
    dacoce_path: Path
    cenhid_catalog_path: Path
    center_catalog_path: Path
    period: str
    hydro_group_count: int
    thermal_group_count: int
    dacoce_hydro_count: int
    dacoce_thermal_count: int
    hydro_blocks: list[G1CentralBlock]
    thermal_blocks: list[G1CentralBlock]
    issues: list[G1SourceIssue]

    @property
    def errors(self) -> list[G1SourceIssue]:
        return [item for item in self.issues if item.severity == "ERROR"]

    @property
    def warnings(self) -> list[G1SourceIssue]:
        return [item for item in self.issues if item.severity == "WARNING"]

    @property
    def has_errors(self) -> bool:
        return bool(self.errors)


def _clean_text(value: object) -> str:
    if value is None:
        return ""

    return str(value).strip()


def _clean_upper(value: object) -> str:
    return _clean_text(value).upper()


def _to_decimal(value: object) -> Decimal | None:
    if value is None:
        return None

    text = str(value).strip()

    if not text:
        return None

    try:
        return Decimal(text)
    except InvalidOperation:
        return None


def _require_decimal(
    value: object,
    issues: list[G1SourceIssue],
    section: str,
    source: str,
    field: str,
    context: str,
) -> Decimal:
    parsed_value = _to_decimal(value)

    if parsed_value is None:
        _add_issue(
            issues,
            "ERROR",
            section,
            source,
            field,
            "Valor numérico obligatorio vacío o inválido.",
            context,
        )
        return Decimal("0")

    return parsed_value


def _add_issue(
    issues: list[G1SourceIssue],
    severity: IssueSeverity,
    section: str,
    source: str,
    field: str | None,
    message: str,
    value: object | None = None,
) -> None:
    issues.append(
        G1SourceIssue(
            severity=severity,
            section=section,
            source=source,
            field=field,
            message=message,
            value=None if value is None else str(value),
        )
    )

def _title_preserve_roman(text: str) -> str:
    roman_tokens = {"I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"}

    parts = []
    for token in text.strip().split():
        upper_token = token.upper()
        if upper_token in roman_tokens:
            parts.append(upper_token)
        else:
            parts.append(token.title())

    return " ".join(parts)

def _display_hydro_name(raw_name: str) -> str:
    normalized = _title_preserve_roman(raw_name)

    if normalized.upper().startswith("CHARCANI"):
        return f"C. H. {normalized}"

    return normalized


def _display_thermal_name(raw_name: str) -> str:
    normalized = _title_preserve_roman(raw_name)

    if normalized.upper().startswith("C. T."):
        return normalized

    return f"C. T. {normalized}"


def _group_order(group_name: str) -> tuple[int, str]:
    text = group_name.strip().upper()

    if text.startswith("G-"):
        number_text = text.replace("G-", "", 1)
        if number_text.isdigit():
            return int(number_text), text

    if text.startswith("GRUPO "):
        number_text = text.replace("GRUPO ", "", 1)
        if number_text.isdigit():
            return int(number_text), text

    return 999, text

ROMAN_ORDER = {
    "I": 1,
    "II": 2,
    "III": 3,
    "IV": 4,
    "V": 5,
    "VI": 6,
    "VII": 7,
    "VIII": 8,
    "IX": 9,
    "X": 10,
}

def _central_sort_key(central_name: str) -> tuple[str, int, str]:
    normalized = (
        central_name.upper()
        .replace("C. H.", "")
        .replace("C. T.", "")
        .strip()
    )

    tokens = normalized.split()

    if tokens and tokens[-1] in ROMAN_ORDER:
        return (" ".join(tokens[:-1]), ROMAN_ORDER[tokens[-1]], normalized)

    return (normalized, 0, normalized)

def _status_to_g1(value: object) -> str:
    status = _clean_upper(value)

    if status == "S":
        return "OP"

    if status == "N":
        return "NO"

    return status


def _read_cenhid_groups(
    cenhid_path: Path,
    period: str,
    catalog_path: Path,
    issues: list[G1SourceIssue],
) -> list[G1GroupRow]:
    year, month = parse_period(period)
    catalog = load_cenhid_catalog(catalog_path)
    table = DBF(str(cenhid_path), load=True, char_decode_errors="ignore")

    rows: list[G1GroupRow] = []

    for record in table:
        if _clean_text(record.get("CANOREG")) != year:
            continue

        if _clean_text(record.get("CMESREG")) != month:
            continue

        if _clean_upper(record.get("CTIPGRU")) != "HI":
            _add_issue(
                issues,
                "ERROR",
                "HIDRO",
                "CENHID",
                "CTIPGRU",
                "Registro CENHID del periodo no es hidroeléctrico.",
                record.get("CTIPGRU"),
            )
            continue

        ccodcon = _clean_text(record.get("CCODCON"))
        cnomnum = _clean_text(record.get("CNOMNUM"))
        unit = catalog.get((ccodcon, cnomnum))

        if unit is None:
            _add_issue(
                issues,
                "ERROR",
                "HIDRO",
                "CENHID",
                "CCODCON/CNOMNUM",
                "Unidad hidroeléctrica no existe en catálogo CENHID.",
                f"{ccodcon} / {cnomnum}",
            )
            central_name = ccodcon
        else:
            central_name = _display_hydro_name(unit.central)

        context = f"{ccodcon} / {cnomnum}"

        rows.append(
            G1GroupRow(
                section="HIDRO",
                ccodcon=ccodcon,
                central_name=central_name,
                ctipgru="HI",
                group_name=cnomnum,
                status=_status_to_g1(record.get("CESTGRU")),
                installed_power=_require_decimal(record.get("NPOTINS"), issues, "HIDRO", "CENHID", "NPOTINS", context),
                effective_power=_require_decimal(record.get("NPOTEFE"), issues, "HIDRO", "CENHID", "NPOTEFE", context),
                peak_energy=_require_decimal(record.get("NHORPUN"), issues, "HIDRO", "CENHID", "NHORPUN", context),
                offpeak_energy=_require_decimal(record.get("NFUHOPU"), issues, "HIDRO", "CENHID", "NFUHOPU", context),
                gross_energy=_require_decimal(record.get("NTOPRBR"), issues, "HIDRO", "CENHID", "NTOPRBR", context),
                maintenance_hours=_require_decimal(record.get("CHRSMAN"), issues, "HIDRO", "CENHID", "CHRSMAN", context),
                operation_hours=_require_decimal(record.get("CHRSOPE"), issues, "HIDRO", "CENHID", "CHRSOPE", context),
                forced_outage_hours=_require_decimal(record.get("CHRSSAL"), issues, "HIDRO", "CENHID", "CHRSSAL", context),
            )
        )

    return rows


def _read_center_groups(
    center_path: Path,
    period: str,
    catalog_path: Path,
    issues: list[G1SourceIssue],
) -> list[G1GroupRow]:
    year, month = parse_period(period)
    catalog = load_center_catalog(catalog_path)
    table = DBF(str(center_path), load=True, char_decode_errors="ignore")

    rows: list[G1GroupRow] = []

    for record in table:
        if _clean_text(record.get("CANOREG")) != year:
            continue

        if _clean_text(record.get("CMESREG")) != month:
            continue

        ccodcon = _clean_text(record.get("CCODCON"))
        ctipgru = _clean_upper(record.get("CTIPGRU"))
        cnomnum = _clean_text(record.get("CNOMNUM"))
        unit = catalog.get((ccodcon, ctipgru, cnomnum))

        if unit is None:
            _add_issue(
                issues,
                "ERROR",
                "TERMO",
                "CENTER",
                "CCODCON/CTIPGRU/CNOMNUM",
                "Unidad termoeléctrica no existe en catálogo CENTER.",
                f"{ccodcon} / {ctipgru} / {cnomnum}",
            )
            central_name = ccodcon
        else:
            central_name = _display_thermal_name(unit.central)

        context = f"{ccodcon} / {ctipgru} / {cnomnum}"

        rows.append(
            G1GroupRow(
                section="TERMO",
                ccodcon=ccodcon,
                central_name=central_name,
                ctipgru=ctipgru,
                group_name=cnomnum,
                status=_status_to_g1(record.get("CESTGRU")),
                installed_power=_require_decimal(record.get("NPOTINS"), issues, "TERMO", "CENTER", "NPOTINS", context),
                effective_power=_require_decimal(record.get("NPOTEFE"), issues, "TERMO", "CENTER", "NPOTEFE", context),
                peak_energy=_require_decimal(record.get("NHORPUN"), issues, "TERMO", "CENTER", "NHORPUN", context),
                offpeak_energy=_require_decimal(record.get("NFUHOPU"), issues, "TERMO", "CENTER", "NFUHOPU", context),
                gross_energy=_require_decimal(record.get("NTOPRBR"), issues, "TERMO", "CENTER", "NTOPRBR", context),
                maintenance_hours=_require_decimal(record.get("CHRSMAN"), issues, "TERMO", "CENTER", "CHRSMAN", context),
                operation_hours=_require_decimal(record.get("CHRSOPE"), issues, "TERMO", "CENTER", "CHRSOPE", context),
                forced_outage_hours=_require_decimal(record.get("CHRSSAL"), issues, "TERMO", "CENTER", "CHRSSAL", context),
                lubricant_consumption=_require_decimal(record.get("NCONLUB"), issues, "TERMO", "CENTER", "NCONLUB", context),
            )
        )

    return rows


def _read_dacoce_rows(
    dacoce_path: Path,
    period: str,
    issues: list[G1SourceIssue],
) -> dict[tuple[str, str], G1DacoceRow]:
    year, month = parse_period(period)
    table = DBF(str(dacoce_path), load=True, char_decode_errors="ignore")

    rows: dict[tuple[str, str], G1DacoceRow] = {}

    for record in table:
        if _clean_text(record.get("CANOREG")) != year:
            continue

        if _clean_text(record.get("CMESREG")) != month:
            continue

        ccodcon = _clean_text(record.get("CCODCON"))
        center_type = _clean_upper(record.get("CTIPCEN"))

        if center_type not in {"H", "T"}:
            _add_issue(
                issues,
                "ERROR",
                "G1",
                "DACOCE",
                "CTIPCEN",
                "Tipo de central DACOCE inválido.",
                f"{ccodcon} / {center_type}",
            )
            continue

        if not ccodcon:
            _add_issue(
                issues,
                "ERROR",
                "G1",
                "DACOCE",
                "CCODCON",
                "Código de central DACOCE vacío.",
            )
            continue

        key = (ccodcon, center_type)

        if key in rows:
            _add_issue(
                issues,
                "ERROR",
                "G1",
                "DACOCE",
                "CCODCON/CTIPCEN",
                "DACOCE tiene más de un registro para la misma central y tipo en el periodo.",
                f"{ccodcon} / {center_type}",
            )
            continue

        context = f"{ccodcon} / {center_type}"

        rows[key] = G1DacoceRow(
            ccodcon=ccodcon,
            center_type=center_type,  # type: ignore[arg-type]
            own_consumption=_require_decimal(record.get("NCONPRO"), issues, "G1", "DACOCE", "NCONPRO", context),
            net_production=_require_decimal(record.get("NPRONET"), issues, "G1", "DACOCE", "NPRONET", context),
            max_demand=_require_decimal(record.get("NMAXDEM"), issues, "G1", "DACOCE", "NMAXDEM", context),
        )

    return rows


def _build_blocks(
    section: SectionName,
    groups: list[G1GroupRow],
    dacoce_rows: dict[tuple[str, str], G1DacoceRow],
    issues: list[G1SourceIssue],
) -> list[G1CentralBlock]:
    center_type = "H" if section == "HIDRO" else "T"
    rows_by_central: dict[str, list[G1GroupRow]] = {}

    for group in groups:
        rows_by_central.setdefault(group.ccodcon, []).append(group)

    blocks: list[G1CentralBlock] = []

    for ccodcon in rows_by_central:
        central_groups = sorted(
            rows_by_central[ccodcon],
            key=lambda item: _group_order(item.group_name),
        )
        dacoce = dacoce_rows.get((ccodcon, center_type))
        gross_energy = sum((item.gross_energy for item in central_groups), Decimal("0"))

        if dacoce is None:
            if gross_energy == Decimal("0"):
                _add_issue(
                    issues,
                    "WARNING",
                    section,
                    "DACOCE",
                    "CCODCON/CTIPCEN",
                    "Central presente en generación con producción bruta cero y ausente en DACOCE. "
                    "Para G1 se usarán valores cero en consumo propio, producción neta y máxima demanda.",
                    f"{ccodcon} / {center_type}",
                )

                dacoce = G1DacoceRow(
                    ccodcon=ccodcon,
                    center_type=center_type,  # type: ignore[arg-type]
                    own_consumption=Decimal("0"),
                    net_production=Decimal("0"),
                    max_demand=Decimal("0"),
                )
            else:
                _add_issue(
                    issues,
                    "ERROR",
                    section,
                    "DACOCE",
                    "CCODCON/CTIPCEN",
                    "Central presente en generación pero ausente en DACOCE.",
                    f"{ccodcon} / {center_type}",
                )
                continue

        blocks.append(
            G1CentralBlock(
                section=section,
                ccodcon=ccodcon,
                central_name=central_groups[0].central_name,
                groups=central_groups,
                dacoce=dacoce,
            )
        )

        calculated_net = sum((item.gross_energy for item in central_groups), Decimal("0")) - dacoce.own_consumption
        difference = abs(calculated_net - dacoce.net_production)

        if difference > NET_PRODUCTION_TOLERANCE:
            _add_issue(
                issues,
                "WARNING",
                section,
                "DACOCE",
                "NPRONET",
                "DACOCE.NPRONET difiere de generación bruta - consumo propio. Para G1 se usará DACOCE.NPRONET.",
                (
                    f"CCODCON={ccodcon}; bruto={sum((item.gross_energy for item in central_groups), Decimal('0'))}; "
                    f"consumo={dacoce.own_consumption}; neta_dacoce={dacoce.net_production}; "
                    f"neta_calculada={calculated_net}; diferencia={difference}"
                ),
            )

    return sorted(blocks, key=lambda item: _central_sort_key(item.central_name))


def _warn_extra_dacoce_rows(
    hydro_blocks: list[G1CentralBlock],
    thermal_blocks: list[G1CentralBlock],
    dacoce_rows: dict[tuple[str, str], G1DacoceRow],
    issues: list[G1SourceIssue],
) -> None:
    used_keys = {
        *((block.ccodcon, "H") for block in hydro_blocks),
        *((block.ccodcon, "T") for block in thermal_blocks),
    }

    for key in sorted(set(dacoce_rows) - used_keys):
        section = "HIDRO" if key[1] == "H" else "TERMO"
        _add_issue(
            issues,
            "WARNING",
            section,
            "DACOCE",
            "CCODCON/CTIPCEN",
            "Central presente en DACOCE pero ausente en generación. No se incluirá en G1.",
            f"{key[0]} / {key[1]}",
        )


def validate_g1_sources(
    cenhid_path: Path,
    center_path: Path,
    dacoce_path: Path,
    period: str,
    cenhid_catalog_path: Path,
    center_catalog_path: Path,
) -> G1SourcesValidationResult:
    parse_period(period)
    issues: list[G1SourceIssue] = []

    hydro_groups = _read_cenhid_groups(
        cenhid_path=cenhid_path,
        period=period,
        catalog_path=cenhid_catalog_path,
        issues=issues,
    )
    thermal_groups = _read_center_groups(
        center_path=center_path,
        period=period,
        catalog_path=center_catalog_path,
        issues=issues,
    )
    dacoce_rows = _read_dacoce_rows(
        dacoce_path=dacoce_path,
        period=period,
        issues=issues,
    )

    if not hydro_groups:
        _add_issue(
            issues,
            "ERROR",
            "HIDRO",
            "CENHID",
            None,
            "No se encontraron registros CENHID para el periodo.",
            period,
        )

    if not thermal_groups:
        _add_issue(
            issues,
            "ERROR",
            "TERMO",
            "CENTER",
            None,
            "No se encontraron registros CENTER para el periodo.",
            period,
        )

    hydro_blocks = _build_blocks(
        section="HIDRO",
        groups=hydro_groups,
        dacoce_rows=dacoce_rows,
        issues=issues,
    )
    thermal_blocks = _build_blocks(
        section="TERMO",
        groups=thermal_groups,
        dacoce_rows=dacoce_rows,
        issues=issues,
    )
    _warn_extra_dacoce_rows(
        hydro_blocks=hydro_blocks,
        thermal_blocks=thermal_blocks,
        dacoce_rows=dacoce_rows,
        issues=issues,
    )

    return G1SourcesValidationResult(
        cenhid_path=cenhid_path,
        center_path=center_path,
        dacoce_path=dacoce_path,
        cenhid_catalog_path=cenhid_catalog_path,
        center_catalog_path=center_catalog_path,
        period=period,
        hydro_group_count=len(hydro_groups),
        thermal_group_count=len(thermal_groups),
        dacoce_hydro_count=sum(1 for _, center_type in dacoce_rows if center_type == "H"),
        dacoce_thermal_count=sum(1 for _, center_type in dacoce_rows if center_type == "T"),
        hydro_blocks=hydro_blocks,
        thermal_blocks=thermal_blocks,
        issues=issues,
    )


def _format_decimal(value: Decimal, decimals: int = 3) -> str:
    return f"{value:.{decimals}f}"


def g1_sources_validation_to_markdown(
    result: G1SourcesValidationResult,
    max_issue_rows: int = 300,
) -> str:
    lines: list[str] = []

    lines.append(f"# Validación de fuentes G1: `{result.period}`")
    lines.append("")
    lines.append("## Resumen")
    lines.append("")
    lines.append("| Métrica | Valor |")
    lines.append("|---|---:|")
    lines.append(f"| CENHID | `{result.cenhid_path}` |")
    lines.append(f"| CENTER | `{result.center_path}` |")
    lines.append(f"| DACOCE | `{result.dacoce_path}` |")
    lines.append(f"| Catálogo CENHID | `{result.cenhid_catalog_path}` |")
    lines.append(f"| Catálogo CENTER | `{result.center_catalog_path}` |")
    lines.append(f"| Periodo | {result.period} |")
    lines.append(f"| Grupos hidroeléctricos | {result.hydro_group_count} |")
    lines.append(f"| Centrales hidroeléctricas | {len(result.hydro_blocks)} |")
    lines.append(f"| Grupos termoeléctricos | {result.thermal_group_count} |")
    lines.append(f"| Centrales termoeléctricas | {len(result.thermal_blocks)} |")
    lines.append(f"| DACOCE hidro | {result.dacoce_hydro_count} |")
    lines.append(f"| DACOCE termo | {result.dacoce_thermal_count} |")
    lines.append(f"| Errores | {len(result.errors)} |")
    lines.append(f"| Advertencias | {len(result.warnings)} |")
    lines.append("")
    lines.append("## Resumen por central")
    lines.append("")
    lines.append(
        "| Sección | Código | Central | Grupos | Pot. Inst. | Pot. Efec. | H.P. | H.F.P. | "
        "Bruta | Consumo propio | Neta | Máx. demanda | Lubricantes |"
    )
    lines.append("|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")

    for block in [*result.hydro_blocks, *result.thermal_blocks]:
        lines.append(
            f"| {block.section} | {block.ccodcon} | {block.central_name} | {block.group_count} | "
            f"{_format_decimal(block.installed_power)} | "
            f"{_format_decimal(block.effective_power)} | "
            f"{_format_decimal(block.peak_energy)} | "
            f"{_format_decimal(block.offpeak_energy)} | "
            f"{_format_decimal(block.gross_energy)} | "
            f"{_format_decimal(block.dacoce.own_consumption)} | "
            f"{_format_decimal(block.dacoce.net_production)} | "
            f"{_format_decimal(block.dacoce.max_demand)} | "
            f"{_format_decimal(block.lubricant_consumption)} |"
        )

    lines.append("")
    lines.append("## Hallazgos")
    lines.append("")

    if not result.issues:
        lines.append("- No se detectaron errores ni advertencias.")
        lines.append("")
        return "\n".join(lines)

    lines.append("| Severidad | Sección | Fuente | Campo | Mensaje | Valor |")
    lines.append("|---|---|---|---|---|---|")

    for issue in result.issues[:max_issue_rows]:
        field = "" if issue.field is None else issue.field
        value = "" if issue.value is None else issue.value
        lines.append(
            f"| {issue.severity} | {issue.section} | {issue.source} | {field} | {issue.message} | {value} |"
        )

    if len(result.issues) > max_issue_rows:
        lines.append("")
        lines.append(
            f"> El reporte muestra los primeros {max_issue_rows} hallazgos de "
            f"{len(result.issues)} encontrados."
        )

    lines.append("")

    return "\n".join(lines)


def write_g1_sources_validation_markdown(
    result: G1SourcesValidationResult,
    output_path: Path,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(g1_sources_validation_to_markdown(result), encoding="utf-8")