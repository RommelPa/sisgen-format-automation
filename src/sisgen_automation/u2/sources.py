from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from enum import Enum
from pathlib import Path
from typing import Any

from dbfread import DBF

from sisgen_automation.u2.catalog import U2Catalog, load_u2_catalog


REQUIRED_FIELDS = {
    "CANOREG",
    "CMESREG",
    "CCODGEN",
    "CCODREG",
    "CCODDEP",
    "CCODCIU",
    "CDESCIU",
    "NUSULIB",
    "NCONLIB",
    "NFACTOT",
}

DBF_ENCODING = "cp850"


class IssueSeverity(str, Enum):
    ERROR = "ERROR"
    WARNING = "WARNING"


@dataclass(frozen=True)
class U2SourceIssue:
    severity: IssueSeverity
    row: int | None
    ciiu_code: str | None
    field: str | None
    message: str
    value: object | None = None


@dataclass(frozen=True)
class U2SourceRow:
    row_number: int
    ciiu_code: str
    description: str
    free_clients: Decimal
    consumption_mwh: Decimal
    billing_s: Decimal


@dataclass(frozen=True)
class U2SourceTotals:
    free_clients: Decimal
    consumption_mwh: Decimal
    billing_s: Decimal


@dataclass(frozen=True)
class U2SourcesValidationResult:
    period: str
    rows: tuple[U2SourceRow, ...]
    totals: U2SourceTotals
    issues: tuple[U2SourceIssue, ...]

    @property
    def errors(self) -> tuple[U2SourceIssue, ...]:
        return tuple(issue for issue in self.issues if issue.severity == IssueSeverity.ERROR)

    @property
    def warnings(self) -> tuple[U2SourceIssue, ...]:
        return tuple(issue for issue in self.issues if issue.severity == IssueSeverity.WARNING)

    @property
    def has_errors(self) -> bool:
        return bool(self.errors)


def parse_period(period: str) -> tuple[str, str]:
    parts = period.strip().split("-")
    if len(parts) != 2:
        raise ValueError("El periodo debe tener formato YYYY-MM.")

    year, month = parts
    if len(year) != 4 or len(month) != 2:
        raise ValueError("El periodo debe tener formato YYYY-MM.")

    month_number = int(month)
    if not 1 <= month_number <= 12:
        raise ValueError("El mes debe estar entre 01 y 12.")

    return year[-2:], month


def _decimal(value: Any, *, default: Decimal = Decimal("0")) -> Decimal:
    if value is None:
        return default

    text = str(value).strip()
    if not text:
        return default

    try:
        return Decimal(text)
    except InvalidOperation:
        return default


def _round_clients(value: Decimal) -> Decimal:
    return value.quantize(Decimal("1"), rounding=ROUND_HALF_UP)


def _round_mwh(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)


def _round_money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _validate_structure(ciugen_path: Path) -> list[U2SourceIssue]:
    table = DBF(str(ciugen_path), load=False, char_decode_errors="ignore")
    fields = {field.name.upper() for field in table.fields}
    missing = sorted(REQUIRED_FIELDS - fields)

    return [
        U2SourceIssue(
            severity=IssueSeverity.ERROR,
            row=None,
            ciiu_code=None,
            field=field,
            message="Campo requerido ausente en CIUGEN.DBF.",
            value=None,
        )
        for field in missing
    ]


def _add_mismatch_error(
    issues: list[U2SourceIssue],
    *,
    row_number: int,
    ciiu_code: str,
    field: str,
    expected: str,
    actual: str,
) -> None:
    if actual != expected:
        issues.append(
            U2SourceIssue(
                severity=IssueSeverity.ERROR,
                row=row_number,
                ciiu_code=ciiu_code,
                field=field,
                message=f"Valor invalido. Se esperaba {expected}.",
                value=actual,
            )
        )


def _build_row(
    *,
    row_number: int,
    record: dict[str, Any],
    catalog: U2Catalog,
    issues: list[U2SourceIssue],
) -> U2SourceRow | None:
    ciiu_code = str(record.get("CCODCIU", "")).strip()
    item = catalog.ciiu_by_code.get(ciiu_code)

    if item is None:
        issues.append(
            U2SourceIssue(
                severity=IssueSeverity.ERROR,
                row=row_number,
                ciiu_code=ciiu_code,
                field="CCODCIU",
                message="Codigo CIIU no existe en catalogo U2.",
                value=ciiu_code,
            )
        )
        return None

    _add_mismatch_error(
        issues,
        row_number=row_number,
        ciiu_code=ciiu_code,
        field="CCODGEN",
        expected=catalog.company.ccodgen,
        actual=str(record.get("CCODGEN", "")).strip(),
    )
    _add_mismatch_error(
        issues,
        row_number=row_number,
        ciiu_code=ciiu_code,
        field="CCODREG",
        expected=catalog.location.ccodreg,
        actual=str(record.get("CCODREG", "")).strip(),
    )
    _add_mismatch_error(
        issues,
        row_number=row_number,
        ciiu_code=ciiu_code,
        field="CCODDEP",
        expected=catalog.location.ccoddep,
        actual=str(record.get("CCODDEP", "")).strip(),
    )

    description = str(record.get("CDESCIU", "")).strip()
    if description != item.description:
        issues.append(
            U2SourceIssue(
                severity=IssueSeverity.WARNING,
                row=row_number,
                ciiu_code=ciiu_code,
                field="CDESCIU",
                message="Descripcion CIIU distinta al catalogo. Se usara descripcion del catalogo.",
                value=description,
            )
        )

    free_clients = _decimal(record.get("NUSULIB"))
    consumption_mwh = _decimal(record.get("NCONLIB"))
    billing_s = _decimal(record.get("NFACTOT"))

    for field, value in [
        ("NUSULIB", free_clients),
        ("NCONLIB", consumption_mwh),
        ("NFACTOT", billing_s),
    ]:
        if value < 0:
            issues.append(
                U2SourceIssue(
                    severity=IssueSeverity.ERROR,
                    row=row_number,
                    ciiu_code=ciiu_code,
                    field=field,
                    message="El valor no puede ser negativo.",
                    value=value,
                )
            )

    if free_clients != _round_clients(free_clients):
        issues.append(
            U2SourceIssue(
                severity=IssueSeverity.WARNING,
                row=row_number,
                ciiu_code=ciiu_code,
                field="NUSULIB",
                message="Numero de clientes libres no es entero.",
                value=free_clients,
            )
        )

    return U2SourceRow(
        row_number=row_number,
        ciiu_code=ciiu_code,
        description=item.description,
        free_clients=_round_clients(free_clients),
        consumption_mwh=_round_mwh(consumption_mwh),
        billing_s=_round_money(billing_s),
    )


def _sum(rows: tuple[U2SourceRow, ...], field: str) -> Decimal:
    return sum((getattr(row, field) for row in rows), Decimal("0"))


def _build_totals(rows: tuple[U2SourceRow, ...]) -> U2SourceTotals:
    return U2SourceTotals(
        free_clients=_round_clients(_sum(rows, "free_clients")),
        consumption_mwh=_round_mwh(_sum(rows, "consumption_mwh")),
        billing_s=_round_money(_sum(rows, "billing_s")),
    )


def validate_u2_sources(
    *,
    ciugen_path: Path,
    period: str,
    catalog_path: Path,
) -> U2SourcesValidationResult:
    if not ciugen_path.exists():
        raise FileNotFoundError(f"No existe CIUGEN.DBF: {ciugen_path}")

    catalog = load_u2_catalog(catalog_path)
    year, month = parse_period(period)

    issues = _validate_structure(ciugen_path)
    if any(issue.severity == IssueSeverity.ERROR for issue in issues):
        return U2SourcesValidationResult(
            period=period,
            rows=(),
            totals=_build_totals(()),
            issues=tuple(issues),
        )

    table = DBF(
        str(ciugen_path),
        load=True,
        encoding=DBF_ENCODING,
        char_decode_errors="ignore",
    )

    rows: list[U2SourceRow] = []
    seen_codes: set[str] = set()

    for row_number, record in enumerate(table, start=1):
        record_year = str(record.get("CANOREG", "")).strip()
        record_month = str(record.get("CMESREG", "")).strip().zfill(2)

        if record_year != year or record_month != month:
            continue

        ciiu_code = str(record.get("CCODCIU", "")).strip()
        if ciiu_code in seen_codes:
            issues.append(
                U2SourceIssue(
                    severity=IssueSeverity.ERROR,
                    row=row_number,
                    ciiu_code=ciiu_code,
                    field="CCODCIU",
                    message="Codigo CIIU duplicado para el periodo.",
                    value=ciiu_code,
                )
            )
            continue

        seen_codes.add(ciiu_code)

        row = _build_row(
            row_number=row_number,
            record=dict(record),
            catalog=catalog,
            issues=issues,
        )
        if row is not None:
            rows.append(row)

    rows_by_code = {row.ciiu_code: row for row in rows}
    ordered_rows = tuple(
        rows_by_code[item.ccodciu]
        for item in catalog.ciiu
        if item.ccodciu in rows_by_code
    )

    if not ordered_rows:
        issues.append(
            U2SourceIssue(
                severity=IssueSeverity.ERROR,
                row=None,
                ciiu_code=None,
                field=None,
                message="No se encontraron registros CIUGEN para el periodo.",
                value=period,
            )
        )

    return U2SourcesValidationResult(
        period=period,
        rows=ordered_rows,
        totals=_build_totals(ordered_rows),
        issues=tuple(issues),
    )
