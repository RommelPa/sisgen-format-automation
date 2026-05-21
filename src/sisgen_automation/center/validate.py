from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Literal, Mapping

from dbfread import DBF  # type: ignore[import-untyped]

from sisgen_automation.center.catalog import CenterUnit, load_center_catalog
from sisgen_automation.dbf.profile import DbfField, read_dbf_profile

IssueSeverity = Literal["ERROR", "WARNING"]

EXPECTED_FIELDS = [
    DbfField("CANOREG", "C", 2, 0),
    DbfField("CMESREG", "C", 2, 0),
    DbfField("CCODEMP", "C", 6, 0),
    DbfField("CCODCON", "C", 8, 0),
    DbfField("CCODCEN", "C", 8, 0),
    DbfField("CTIPGRU", "C", 2, 0),
    DbfField("CNOMNUM", "C", 30, 0),
    DbfField("CESTGRU", "C", 1, 0),
    DbfField("NPOTINS", "N", 19, 5),
    DbfField("NPOTEFE", "N", 19, 5),
    DbfField("NHORPUN", "N", 19, 5),
    DbfField("NFUHOPU", "N", 19, 5),
    DbfField("NTOPRBR", "N", 19, 5),
    DbfField("CHRSMAN", "N", 19, 5),
    DbfField("CHRSOPE", "N", 19, 5),
    DbfField("CHRSSAL", "N", 19, 5),
    DbfField("NCONLUB", "N", 19, 5),
]

NUMERIC_FIELDS = [
    "NPOTINS",
    "NPOTEFE",
    "NHORPUN",
    "NFUHOPU",
    "NTOPRBR",
    "CHRSMAN",
    "CHRSOPE",
    "CHRSSAL",
    "NCONLUB",
]

MONTHS = {f"{month:02d}" for month in range(1, 13)}
STATUS_VALUES = {"S", "N"}
THERMAL_GROUP_TYPES = {"EL", "TV", "TG", "CC", "OT", "CA"}
DECIMAL_TOLERANCE = Decimal("0.01")


@dataclass(frozen=True)
class CenterValidationIssue:
    severity: IssueSeverity
    row_number: int | None
    field: str | None
    message: str
    value: str | None = None


@dataclass(frozen=True)
class CenterValidationResult:
    dbf_path: Path
    catalog_path: Path
    record_count: int
    catalog_unit_count: int
    period_counts: dict[str, int]
    issues: list[CenterValidationIssue]

    @property
    def errors(self) -> list[CenterValidationIssue]:
        return [issue for issue in self.issues if issue.severity == "ERROR"]

    @property
    def warnings(self) -> list[CenterValidationIssue]:
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
    issues: list[CenterValidationIssue],
    severity: IssueSeverity,
    row_number: int | None,
    field: str | None,
    message: str,
    value: object | None = None,
) -> None:
    issues.append(
        CenterValidationIssue(
            severity=severity,
            row_number=row_number,
            field=field,
            message=message,
            value=None if value is None else str(value),
        )
    )


def _validate_structure(dbf_path: Path, issues: list[CenterValidationIssue]) -> None:
    profile = read_dbf_profile(dbf_path)

    for warning in profile.warnings:
        _add_issue(issues, "WARNING", None, None, warning)

    if len(profile.fields) != len(EXPECTED_FIELDS):
        _add_issue(
            issues,
            "ERROR",
            None,
            None,
            "La cantidad de campos no coincide con la estructura esperada. "
            f"Esperado: {len(EXPECTED_FIELDS)}. Encontrado: {len(profile.fields)}.",
        )
        return

    for index, expected_field in enumerate(EXPECTED_FIELDS):
        actual_field = profile.fields[index]

        if actual_field != expected_field:
            _add_issue(
                issues,
                "ERROR",
                None,
                actual_field.name,
                "La definición del campo no coincide con la estructura esperada. "
                f"Esperado: {expected_field}. Encontrado: {actual_field}.",
            )


def _validate_required_text(
    record: Mapping[str, object],
    row_number: int,
    field: str,
    issues: list[CenterValidationIssue],
) -> str:
    value = _clean_text(record.get(field))

    if not value:
        _add_issue(issues, "ERROR", row_number, field, "Campo obligatorio vacío.", value)

    return value


def _validate_numeric_fields(
    record: Mapping[str, object],
    row_number: int,
    issues: list[CenterValidationIssue],
) -> dict[str, Decimal]:
    parsed_values: dict[str, Decimal] = {}

    for field in NUMERIC_FIELDS:
        value = record.get(field)
        decimal_value = _to_decimal(value)

        if decimal_value is None:
            _add_issue(
                issues,
                "ERROR",
                row_number,
                field,
                "Valor numérico inválido o vacío.",
                value,
            )
            continue

        parsed_values[field] = decimal_value

        if decimal_value < 0:
            _add_issue(
                issues,
                "ERROR",
                row_number,
                field,
                "Valor negativo no permitido.",
                decimal_value,
            )

    return parsed_values


def _validate_catalog_match(
    record: Mapping[str, object],
    row_number: int,
    catalog: dict[tuple[str, str, str], CenterUnit],
    issues: list[CenterValidationIssue],
) -> tuple[str, str, str]:
    ccodcon = _validate_required_text(record, row_number, "CCODCON", issues)
    ctipgru = _validate_required_text(record, row_number, "CTIPGRU", issues).upper()
    cnomnum = _validate_required_text(record, row_number, "CNOMNUM", issues)

    key = (ccodcon, ctipgru, cnomnum)

    if key not in catalog:
        _add_issue(
            issues,
            "WARNING",
            row_number,
            "CCODCON/CTIPGRU/CNOMNUM",
            "La unidad no existe en el catálogo CENTER actual. Puede ser histórica o debe revisarse.",
            f"{ccodcon} / {ctipgru} / {cnomnum}",
        )

    return key


def _validate_record(
    record: Mapping[str, object],
    row_number: int,
    catalog: dict[tuple[str, str, str], CenterUnit],
    issues: list[CenterValidationIssue],
) -> tuple[str | None, tuple[str, str, str] | None]:
    year = _validate_required_text(record, row_number, "CANOREG", issues)
    month = _validate_required_text(record, row_number, "CMESREG", issues)

    if not year.isdigit() or len(year) != 2:
        _add_issue(
            issues,
            "ERROR",
            row_number,
            "CANOREG",
            "El año debe tener dos dígitos.",
            year,
        )

    if month not in MONTHS:
        _add_issue(
            issues,
            "ERROR",
            row_number,
            "CMESREG",
            "El mes debe estar entre 01 y 12.",
            month,
        )

    if _clean_upper(record.get("CCODEMP")) != "EGASA":
        _add_issue(
            issues,
            "ERROR",
            row_number,
            "CCODEMP",
            "La empresa debe ser EGASA.",
            record.get("CCODEMP"),
        )

    ccodcon = _clean_text(record.get("CCODCON"))
    ccodcen = _clean_text(record.get("CCODCEN"))

    if ccodcen != ccodcon:
        _add_issue(
            issues,
            "ERROR",
            row_number,
            "CCODCEN",
            "CCODCEN debe ser igual a CCODCON.",
            f"CCODCON={ccodcon}, CCODCEN={ccodcen}",
        )

    ctipgru = _clean_upper(record.get("CTIPGRU"))

    if ctipgru not in THERMAL_GROUP_TYPES:
        _add_issue(
            issues,
            "WARNING",
            row_number,
            "CTIPGRU",
            "Tipo térmico no reconocido en la lista base. Revisar si corresponde.",
            ctipgru,
        )

    status = _clean_upper(record.get("CESTGRU"))

    if status not in STATUS_VALUES:
        _add_issue(
            issues,
            "ERROR",
            row_number,
            "CESTGRU",
            "El estado del grupo debe ser S o N.",
            record.get("CESTGRU"),
        )

    numeric_values = _validate_numeric_fields(record, row_number, issues)
    unit_key = _validate_catalog_match(record, row_number, catalog, issues)

    nhorpun = numeric_values.get("NHORPUN")
    nfuhopu = numeric_values.get("NFUHOPU")
    ntoprbr = numeric_values.get("NTOPRBR")

    if nhorpun is not None and nfuhopu is not None and ntoprbr is not None:
        calculated_total = nhorpun + nfuhopu

        if abs(calculated_total - ntoprbr) > DECIMAL_TOLERANCE:
            _add_issue(
                issues,
                "ERROR",
                row_number,
                "NTOPRBR",
                "La energía total no coincide con NHORPUN + NFUHOPU.",
                f"NHORPUN + NFUHOPU = {calculated_total}; NTOPRBR = {ntoprbr}",
            )

    period = None

    if year.isdigit() and len(year) == 2 and month in MONTHS:
        period = f"20{year}-{month}"

    return period, unit_key


def validate_center_dbf(dbf_path: Path, catalog_path: Path) -> CenterValidationResult:
    issues: list[CenterValidationIssue] = []
    catalog = load_center_catalog(catalog_path)

    _validate_structure(dbf_path, issues)

    table = DBF(str(dbf_path), load=True, char_decode_errors="ignore")

    period_counts: dict[str, int] = {}
    period_units: dict[str, set[tuple[str, str, str]]] = {}
    record_count = 0

    for row_number, record in enumerate(table, start=1):
        record_count += 1
        period, unit_key = _validate_record(record, row_number, catalog, issues)

        if period is None or unit_key is None:
            continue

        period_counts[period] = period_counts.get(period, 0) + 1
        period_units.setdefault(period, set())

        if unit_key in period_units[period]:
            _add_issue(
                issues,
                "WARNING",
                row_number,
                "CCODCON/CTIPGRU/CNOMNUM",
                "Unidad duplicada dentro del mismo periodo.",
                f"{period}: {unit_key[0]} / {unit_key[1]} / {unit_key[2]}",
            )

        period_units[period].add(unit_key)

    return CenterValidationResult(
        dbf_path=dbf_path,
        catalog_path=catalog_path,
        record_count=record_count,
        catalog_unit_count=len(catalog),
        period_counts=period_counts,
        issues=issues,
    )


def center_validation_to_markdown(
    result: CenterValidationResult,
    max_issue_rows: int = 300,
) -> str:
    lines: list[str] = []

    lines.append(f"# Validación CENTER: `{result.dbf_path.name}`")
    lines.append("")
    lines.append("## Resumen")
    lines.append("")
    lines.append("| Métrica | Valor |")
    lines.append("|---|---:|")
    lines.append(f"| Archivo DBF | `{result.dbf_path}` |")
    lines.append(f"| Catálogo usado | `{result.catalog_path}` |")
    lines.append(f"| Registros leídos | {result.record_count} |")
    lines.append(f"| Unidades en catálogo | {result.catalog_unit_count} |")
    lines.append(f"| Periodos válidos detectados | {len(result.period_counts)} |")
    lines.append(f"| Errores | {len(result.errors)} |")
    lines.append(f"| Advertencias | {len(result.warnings)} |")
    lines.append("")
    lines.append("## Registros por periodo")
    lines.append("")
    lines.append("| Periodo | Registros |")
    lines.append("|---|---:|")

    for period, count in sorted(result.period_counts.items()):
        lines.append(f"| {period} | {count} |")

    lines.append("")
    lines.append("## Hallazgos")
    lines.append("")

    if not result.issues:
        lines.append("- No se detectaron errores ni advertencias.")
        lines.append("")
        return "\n".join(lines)

    lines.append("| Severidad | Fila | Campo | Mensaje | Valor |")
    lines.append("|---|---:|---|---|---|")

    for issue in result.issues[:max_issue_rows]:
        row_number = "" if issue.row_number is None else str(issue.row_number)
        field = "" if issue.field is None else issue.field
        value = "" if issue.value is None else issue.value
        lines.append(
            f"| {issue.severity} | {row_number} | {field} | {issue.message} | {value} |"
        )

    if len(result.issues) > max_issue_rows:
        lines.append("")
        lines.append(
            f"> El reporte muestra los primeros {max_issue_rows} hallazgos de "
            f"{len(result.issues)} encontrados."
        )

    lines.append("")

    return "\n".join(lines)


def write_center_validation_markdown(
    result: CenterValidationResult,
    output_path: Path,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(center_validation_to_markdown(result), encoding="utf-8")