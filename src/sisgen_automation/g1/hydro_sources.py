from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Literal, Mapping

from dbfread import DBF  # type: ignore[import-untyped]

from sisgen_automation.cenhid.catalog import load_cenhid_catalog
from sisgen_automation.cenhid.template import parse_period

IssueSeverity = Literal["ERROR", "WARNING"]

NET_PRODUCTION_TOLERANCE = Decimal("0.05")


@dataclass(frozen=True)
class G1HydroIssue:
    severity: IssueSeverity
    source: str
    field: str | None
    message: str
    value: str | None = None


@dataclass
class HydroCentralSummary:
    ccodcon: str
    central_name: str
    group_count: int = 0
    installed_power: Decimal = Decimal("0")
    effective_power: Decimal = Decimal("0")
    peak_energy: Decimal = Decimal("0")
    offpeak_energy: Decimal = Decimal("0")
    gross_energy: Decimal = Decimal("0")
    maintenance_hours: Decimal = Decimal("0")
    operation_hours: Decimal = Decimal("0")
    forced_outage_hours: Decimal = Decimal("0")
    own_consumption: Decimal | None = None
    net_production: Decimal | None = None
    max_demand: Decimal | None = None


@dataclass(frozen=True)
class G1HydroSourcesValidationResult:
    cenhid_path: Path
    dacoce_path: Path
    catalog_path: Path
    period: str
    cenhid_group_rows: int
    dacoce_hydro_rows: int
    central_count: int
    summaries: list[HydroCentralSummary]
    issues: list[G1HydroIssue]

    @property
    def errors(self) -> list[G1HydroIssue]:
        return [issue for issue in self.issues if issue.severity == "ERROR"]

    @property
    def warnings(self) -> list[G1HydroIssue]:
        return [issue for issue in self.issues if issue.severity == "WARNING"]

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


def _add_issue(
    issues: list[G1HydroIssue],
    severity: IssueSeverity,
    source: str,
    field: str | None,
    message: str,
    value: object | None = None,
) -> None:
    issues.append(
        G1HydroIssue(
            severity=severity,
            source=source,
            field=field,
            message=message,
            value=None if value is None else str(value),
        )
    )


def _catalog_central_names(catalog_path: Path) -> dict[str, str]:
    catalog = load_cenhid_catalog(catalog_path)

    central_names: dict[str, str] = {}

    for unit in catalog.values():
        existing_name = central_names.get(unit.ccodcon)

        if existing_name is not None and existing_name != unit.central:
            raise ValueError(
                "El catálogo CENHID tiene nombres de central inconsistentes para "
                f"CCODCON={unit.ccodcon}: {existing_name} / {unit.central}"
            )

        central_names[unit.ccodcon] = unit.central

    return central_names


def _display_central_name(raw_name: str) -> str:
    normalized = raw_name.strip()

    if normalized.upper().startswith("CHARCANI"):
        return f"C. H. {normalized.title()}"

    return normalized


def _read_cenhid_period_rows(cenhid_path: Path, period: str) -> list[Mapping[str, object]]:
    year, month = parse_period(period)
    table = DBF(str(cenhid_path), load=True, char_decode_errors="ignore")

    rows: list[Mapping[str, object]] = []

    for record in table:
        if _clean_text(record.get("CANOREG")) == year and _clean_text(record.get("CMESREG")) == month:
            rows.append(record)

    return rows


def _read_dacoce_hydro_period_rows(dacoce_path: Path, period: str) -> list[Mapping[str, object]]:
    year, month = parse_period(period)
    table = DBF(str(dacoce_path), load=True, char_decode_errors="ignore")

    rows: list[Mapping[str, object]] = []

    for record in table:
        is_period = (
            _clean_text(record.get("CANOREG")) == year
            and _clean_text(record.get("CMESREG")) == month
        )
        is_hydro = _clean_upper(record.get("CTIPCEN")) == "H"

        if is_period and is_hydro:
            rows.append(record)

    return rows


def _require_decimal(
    record: Mapping[str, object],
    field_name: str,
    issues: list[G1HydroIssue],
    source: str,
) -> Decimal:
    value = record.get(field_name)
    decimal_value = _to_decimal(value)

    if decimal_value is None:
        _add_issue(
            issues,
            "ERROR",
            source,
            field_name,
            "Valor numérico obligatorio vacío o inválido.",
            value,
        )
        return Decimal("0")

    return decimal_value


def _build_cenhid_summaries(
    rows: list[Mapping[str, object]],
    central_names: dict[str, str],
    issues: list[G1HydroIssue],
) -> dict[str, HydroCentralSummary]:
    summaries: dict[str, HydroCentralSummary] = {}

    for row in rows:
        ccodcon = _clean_text(row.get("CCODCON"))
        ctipgru = _clean_upper(row.get("CTIPGRU"))

        if not ccodcon:
            _add_issue(issues, "ERROR", "CENHID", "CCODCON", "Código de central vacío.")
            continue

        if ctipgru != "HI":
            _add_issue(
                issues,
                "ERROR",
                "CENHID",
                "CTIPGRU",
                "Registro CENHID del periodo no es hidroeléctrico.",
                ctipgru,
            )
            continue

        central_name = central_names.get(ccodcon)

        if central_name is None:
            _add_issue(
                issues,
                "ERROR",
                "CENHID",
                "CCODCON",
                "Central CENHID no existe en el catálogo local.",
                ccodcon,
            )
            central_name = ccodcon

        summary = summaries.setdefault(
            ccodcon,
            HydroCentralSummary(
                ccodcon=ccodcon,
                central_name=_display_central_name(central_name),
            ),
        )

        summary.group_count += 1
        summary.installed_power += _require_decimal(row, "NPOTINS", issues, "CENHID")
        summary.effective_power += _require_decimal(row, "NPOTEFE", issues, "CENHID")
        summary.peak_energy += _require_decimal(row, "NHORPUN", issues, "CENHID")
        summary.offpeak_energy += _require_decimal(row, "NFUHOPU", issues, "CENHID")
        summary.gross_energy += _require_decimal(row, "NTOPRBR", issues, "CENHID")
        summary.maintenance_hours += _require_decimal(row, "CHRSMAN", issues, "CENHID")
        summary.operation_hours += _require_decimal(row, "CHRSOPE", issues, "CENHID")
        summary.forced_outage_hours += _require_decimal(row, "CHRSSAL", issues, "CENHID")

    return summaries


def _index_dacoce_rows(
    rows: list[Mapping[str, object]],
    issues: list[G1HydroIssue],
) -> dict[str, Mapping[str, object]]:
    indexed_rows: dict[str, Mapping[str, object]] = {}

    for row in rows:
        ccodcon = _clean_text(row.get("CCODCON"))

        if not ccodcon:
            _add_issue(issues, "ERROR", "DACOCE", "CCODCON", "Código de central vacío.")
            continue

        if ccodcon in indexed_rows:
            _add_issue(
                issues,
                "ERROR",
                "DACOCE",
                "CCODCON",
                "DACOCE tiene más de un registro hidroeléctrico para la misma central y periodo.",
                ccodcon,
            )
            continue

        indexed_rows[ccodcon] = row

    return indexed_rows


def _attach_dacoce_values(
    summaries: dict[str, HydroCentralSummary],
    dacoce_rows_by_central: dict[str, Mapping[str, object]],
    issues: list[G1HydroIssue],
) -> None:
    cenhid_centrals = set(summaries)
    dacoce_centrals = set(dacoce_rows_by_central)

    missing_in_dacoce = cenhid_centrals - dacoce_centrals
    extra_in_dacoce = dacoce_centrals - cenhid_centrals

    for ccodcon in sorted(missing_in_dacoce):
        _add_issue(
            issues,
            "ERROR",
            "G1",
            "CCODCON",
            "Central presente en CENHID pero ausente en DACOCE. No se puede completar G1.",
            ccodcon,
        )

    for ccodcon in sorted(extra_in_dacoce):
        _add_issue(
            issues,
            "WARNING",
            "G1",
            "CCODCON",
            "Central presente en DACOCE pero ausente en CENHID. No se incluirá en G1 hidro.",
            ccodcon,
        )

    for ccodcon, summary in summaries.items():
        dacoce_row = dacoce_rows_by_central.get(ccodcon)

        if dacoce_row is None:
            continue

        own_consumption = _require_decimal(dacoce_row, "NCONPRO", issues, "DACOCE")
        net_production = _require_decimal(dacoce_row, "NPRONET", issues, "DACOCE")
        max_demand = _require_decimal(dacoce_row, "NMAXDEM", issues, "DACOCE")

        summary.own_consumption = own_consumption
        summary.net_production = net_production
        summary.max_demand = max_demand

        expected_net = summary.gross_energy - own_consumption
        difference = abs(expected_net - net_production)

        if difference > NET_PRODUCTION_TOLERANCE:
            _add_issue(
                issues,
                "ERROR",
                "G1",
                "NPRONET",
                "La producción neta DACOCE no cuadra con Producción Bruta CENHID - Consumo Propio DACOCE.",
                (
                    f"CCODCON={ccodcon}; bruto={summary.gross_energy}; "
                    f"consumo={own_consumption}; neta={net_production}; "
                    f"diferencia={difference}"
                ),
            )


def validate_g1_hydro_sources(
    cenhid_path: Path,
    dacoce_path: Path,
    period: str,
    catalog_path: Path,
) -> G1HydroSourcesValidationResult:
    parse_period(period)

    issues: list[G1HydroIssue] = []

    central_names = _catalog_central_names(catalog_path)
    cenhid_rows = _read_cenhid_period_rows(cenhid_path, period)
    dacoce_rows = _read_dacoce_hydro_period_rows(dacoce_path, period)

    if not cenhid_rows:
        _add_issue(
            issues,
            "ERROR",
            "CENHID",
            None,
            "No se encontraron registros CENHID para el periodo solicitado.",
            period,
        )

    if not dacoce_rows:
        _add_issue(
            issues,
            "ERROR",
            "DACOCE",
            None,
            "No se encontraron registros hidroeléctricos DACOCE para el periodo solicitado.",
            period,
        )

    summaries_by_central = _build_cenhid_summaries(
        rows=cenhid_rows,
        central_names=central_names,
        issues=issues,
    )
    dacoce_rows_by_central = _index_dacoce_rows(dacoce_rows, issues)

    _attach_dacoce_values(
        summaries=summaries_by_central,
        dacoce_rows_by_central=dacoce_rows_by_central,
        issues=issues,
    )

    summaries = sorted(
        summaries_by_central.values(),
        key=lambda item: item.central_name,
    )

    return G1HydroSourcesValidationResult(
        cenhid_path=cenhid_path,
        dacoce_path=dacoce_path,
        catalog_path=catalog_path,
        period=period,
        cenhid_group_rows=len(cenhid_rows),
        dacoce_hydro_rows=len(dacoce_rows),
        central_count=len(summaries),
        summaries=summaries,
        issues=issues,
    )


def _format_decimal(value: Decimal | None, decimals: int = 3) -> str:
    if value is None:
        return ""

    return f"{value:.{decimals}f}"


def g1_hydro_sources_validation_to_markdown(
    result: G1HydroSourcesValidationResult,
    max_issue_rows: int = 300,
) -> str:
    lines: list[str] = []

    lines.append(f"# Validación de fuentes G1 hidro: `{result.period}`")
    lines.append("")
    lines.append("## Resumen")
    lines.append("")
    lines.append("| Métrica | Valor |")
    lines.append("|---|---:|")
    lines.append(f"| CENHID | `{result.cenhid_path}` |")
    lines.append(f"| DACOCE | `{result.dacoce_path}` |")
    lines.append(f"| Catálogo | `{result.catalog_path}` |")
    lines.append(f"| Periodo | {result.period} |")
    lines.append(f"| Filas CENHID del periodo | {result.cenhid_group_rows} |")
    lines.append(f"| Filas DACOCE hidro del periodo | {result.dacoce_hydro_rows} |")
    lines.append(f"| Centrales hidro detectadas | {result.central_count} |")
    lines.append(f"| Errores | {len(result.errors)} |")
    lines.append(f"| Advertencias | {len(result.warnings)} |")
    lines.append("")
    lines.append("## Resumen por central")
    lines.append("")
    lines.append(
        "| Código | Central | Grupos | Pot. Inst. | Pot. Efec. | H.P. | H.F.P. | "
        "Bruta | Consumo propio | Neta | Máx. demanda |"
    )
    lines.append("|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|")

    for item in result.summaries:
        lines.append(
            f"| {item.ccodcon} | {item.central_name} | {item.group_count} | "
            f"{_format_decimal(item.installed_power)} | "
            f"{_format_decimal(item.effective_power)} | "
            f"{_format_decimal(item.peak_energy)} | "
            f"{_format_decimal(item.offpeak_energy)} | "
            f"{_format_decimal(item.gross_energy)} | "
            f"{_format_decimal(item.own_consumption)} | "
            f"{_format_decimal(item.net_production)} | "
            f"{_format_decimal(item.max_demand)} |"
        )

    lines.append("")
    lines.append("## Hallazgos")
    lines.append("")

    if not result.issues:
        lines.append("- No se detectaron errores ni advertencias.")
        lines.append("")
        return "\n".join(lines)

    lines.append("| Severidad | Fuente | Campo | Mensaje | Valor |")
    lines.append("|---|---|---|---|---|")

    for issue in result.issues[:max_issue_rows]:
        field = "" if issue.field is None else issue.field
        value = "" if issue.value is None else issue.value
        lines.append(
            f"| {issue.severity} | {issue.source} | {field} | {issue.message} | {value} |"
        )

    if len(result.issues) > max_issue_rows:
        lines.append("")
        lines.append(
            f"> El reporte muestra los primeros {max_issue_rows} hallazgos de "
            f"{len(result.issues)} encontrados."
        )

    lines.append("")

    return "\n".join(lines)


def write_g1_hydro_sources_validation_markdown(
    result: G1HydroSourcesValidationResult,
    output_path: Path,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(g1_hydro_sources_validation_to_markdown(result), encoding="utf-8")