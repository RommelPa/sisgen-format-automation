from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Literal, Mapping

from dbfread import DBF  # type: ignore[import-untyped]

from sisgen_automation.dbf.profile import DbfField, read_dbf_profile

IssueSeverity = Literal["ERROR", "WARNING"]

EXPECTED_FIELDS = [
    DbfField("CANOREG", "C", 2, 0),
    DbfField("CMESREG", "C", 2, 0),
    DbfField("CCODEMP", "C", 6, 0),
    DbfField("CCODCON", "C", 8, 0),
    DbfField("CTIPCEN", "C", 1, 0),
    DbfField("NCONPRO", "N", 19, 5),
    DbfField("NPRONET", "N", 19, 5),
    DbfField("NMAXDEM", "N", 19, 5),
]

REQUIRED_NON_NEGATIVE_FIELDS = ["NCONPRO", "NMAXDEM"]
OPTIONAL_SIGNED_FIELDS = ["NPRONET"]
NUMERIC_FIELDS = REQUIRED_NON_NEGATIVE_FIELDS + OPTIONAL_SIGNED_FIELDS
CENTER_TYPES = {"H", "T"}
MONTHS = {f"{month:02d}" for month in range(1, 13)}


@dataclass(frozen=True)
class DacoceValidationIssue:
    severity: IssueSeverity
    row_number: int | None
    field: str | None
    message: str
    value: str | None = None


@dataclass(frozen=True)
class DacoceValidationResult:
    dbf_path: Path
    record_count: int
    period_counts: dict[str, int]
    hydro_record_count: int
    thermal_record_count: int
    issues: list[DacoceValidationIssue]

    @property
    def errors(self) -> list[DacoceValidationIssue]:
        return [issue for issue in self.issues if issue.severity == "ERROR"]

    @property
    def warnings(self) -> list[DacoceValidationIssue]:
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
    issues: list[DacoceValidationIssue],
    severity: IssueSeverity,
    row_number: int | None,
    field: str | None,
    message: str,
    value: object | None = None,
) -> None:
    issues.append(
        DacoceValidationIssue(
            severity=severity,
            row_number=row_number,
            field=field,
            message=message,
            value=None if value is None else str(value),
        )
    )


def _validate_structure(dbf_path: Path, issues: list[DacoceValidationIssue]) -> None:
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
    issues: list[DacoceValidationIssue],
) -> str:
    value = _clean_text(record.get(field))

    if not value:
        _add_issue(issues, "ERROR", row_number, field, "Campo obligatorio vacío.", value)

    return value


def _validate_numeric_fields(
    record: Mapping[str, object],
    row_number: int,
    issues: list[DacoceValidationIssue],
) -> None:
    for field in REQUIRED_NON_NEGATIVE_FIELDS:
        value = record.get(field)
        decimal_value = _to_decimal(value)

        if decimal_value is None:
            _add_issue(
                issues,
                "ERROR",
                row_number,
                field,
                "Valor numérico obligatorio inválido o vacío.",
                value,
            )
            continue

        if decimal_value < 0:
            _add_issue(
                issues,
                "ERROR",
                row_number,
                field,
                "Valor negativo no permitido.",
                decimal_value,
            )

    for field in OPTIONAL_SIGNED_FIELDS:
        value = record.get(field)
        decimal_value = _to_decimal(value)

        if decimal_value is None:
            _add_issue(
                issues,
                "WARNING",
                row_number,
                field,
                "Valor numérico vacío. Se revisará al generar reportes.",
                value,
            )

def _validate_record(
    record: Mapping[str, object],
    row_number: int,
    issues: list[DacoceValidationIssue],
) -> tuple[str | None, tuple[str, str, str] | None, str | None]:
    year = _validate_required_text(record, row_number, "CANOREG", issues)
    month = _validate_required_text(record, row_number, "CMESREG", issues)
    ccodcon = _validate_required_text(record, row_number, "CCODCON", issues)
    ctipcen = _clean_upper(record.get("CTIPCEN"))

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

    if ctipcen not in CENTER_TYPES:
        _add_issue(
            issues,
            "ERROR",
            row_number,
            "CTIPCEN",
            "El tipo de central debe ser H o T.",
            record.get("CTIPCEN"),
        )

    _validate_numeric_fields(record, row_number, issues)

    period = None

    if year.isdigit() and len(year) == 2 and month in MONTHS:
        period = f"20{year}-{month}"

    key = None

    if period is not None and ccodcon and ctipcen in CENTER_TYPES:
        key = (period, ccodcon, ctipcen)

    return period, key, ctipcen if ctipcen in CENTER_TYPES else None


def validate_dacoce_dbf(dbf_path: Path) -> DacoceValidationResult:
    issues: list[DacoceValidationIssue] = []

    _validate_structure(dbf_path, issues)

    table = DBF(str(dbf_path), load=True, char_decode_errors="ignore")

    record_count = 0
    hydro_record_count = 0
    thermal_record_count = 0
    period_counts: dict[str, int] = {}
    seen_keys: set[tuple[str, str, str]] = set()

    for row_number, record in enumerate(table, start=1):
        record_count += 1
        period, key, center_type = _validate_record(record, row_number, issues)

        if center_type == "H":
            hydro_record_count += 1
        elif center_type == "T":
            thermal_record_count += 1

        if period is not None:
            period_counts[period] = period_counts.get(period, 0) + 1

        if key is None:
            continue

        if key in seen_keys:
            _add_issue(
                issues,
                "WARNING",
                row_number,
                "CANOREG/CMESREG/CCODCON/CTIPCEN",
                "Registro duplicado para el mismo periodo, código y tipo de central.",
                f"{key[0]} / {key[1]} / {key[2]}",
            )

        seen_keys.add(key)

    return DacoceValidationResult(
        dbf_path=dbf_path,
        record_count=record_count,
        period_counts=period_counts,
        hydro_record_count=hydro_record_count,
        thermal_record_count=thermal_record_count,
        issues=issues,
    )


def dacoce_validation_to_markdown(
    result: DacoceValidationResult,
    max_issue_rows: int = 300,
) -> str:
    lines: list[str] = []

    lines.append(f"# Validación DACOCE: `{result.dbf_path.name}`")
    lines.append("")
    lines.append("## Resumen")
    lines.append("")
    lines.append("| Métrica | Valor |")
    lines.append("|---|---:|")
    lines.append(f"| Archivo DBF | `{result.dbf_path}` |")
    lines.append(f"| Registros leídos | {result.record_count} |")
    lines.append(f"| Registros hidroeléctricos | {result.hydro_record_count} |")
    lines.append(f"| Registros termoeléctricos | {result.thermal_record_count} |")
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


def write_dacoce_validation_markdown(
    result: DacoceValidationResult,
    output_path: Path,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(dacoce_validation_to_markdown(result), encoding="utf-8")