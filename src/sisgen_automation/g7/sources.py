from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from enum import Enum
from pathlib import Path
from typing import Any

from dbfread import DBF  # type: ignore[import-untyped]

from sisgen_automation.g7.catalog import G7Catalog, load_g7_catalog


DBF_ENCODING = "cp850"
TOTAL_TOLERANCE = Decimal("0.00010")


class G7SourceSeverity(str, Enum):
    ERROR = "ERROR"
    WARNING = "WARNING"


@dataclass(frozen=True)
class G7SourceIssue:
    severity: G7SourceSeverity
    section: str
    source: str
    field: str | None
    message: str
    value: object | None = None


@dataclass(frozen=True)
class G7EnergyRow:
    canoreg: str
    cmesreg: str
    ccosisi: str
    ccodeemp: str
    ccodgen: str
    cdesgen: str
    nenhopu: Decimal
    nenfuho: Decimal
    nenetot: Decimal
    nvahopu: Decimal
    nvafuho: Decimal
    nvaltot: Decimal


@dataclass(frozen=True)
class G7NetCommitmentRow:
    canoreg: str
    cmesreg: str
    ccodeemp: str
    ccoddis: str
    cnomdis: str
    ncomnet: Decimal


@dataclass(frozen=True)
class G7PowerTransferRow:
    canoreg: str
    cmesreg: str
    ccodeemp: str
    ccodgen: str
    cnomgen: str
    ntrapot: Decimal


@dataclass(frozen=True)
class G7TransferValuationRow:
    canoreg: str
    cmesreg: str
    ccodeemp: str
    ccodgen: str
    cnomgen: str
    nvaltra: Decimal


@dataclass(frozen=True)
class G7SourcesValidationResult:
    period: str
    comene_path: Path
    venene_path: Path
    comnet_path: Path
    traene_path: Path
    valene_path: Path
    purchases: list[G7EnergyRow]
    sales: list[G7EnergyRow]
    net_commitments: list[G7NetCommitmentRow]
    power_transfers: list[G7PowerTransferRow]
    transfer_valuations: list[G7TransferValuationRow]
    issues: list[G7SourceIssue]

    @property
    def errors(self) -> list[G7SourceIssue]:
        return [issue for issue in self.issues if issue.severity == G7SourceSeverity.ERROR]

    @property
    def warnings(self) -> list[G7SourceIssue]:
        return [issue for issue in self.issues if issue.severity == G7SourceSeverity.WARNING]

    @property
    def has_errors(self) -> bool:
        return bool(self.errors)


def parse_period(period: str) -> tuple[str, str]:
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

    return f"{year % 100:02d}", f"{month:02d}"


def _clean_text(value: object) -> str:
    if value is None:
        return ""

    return str(value).strip()


def _parse_decimal(value: object) -> Decimal | None:
    if value is None or str(value).strip() == "":
        return None

    try:
        return Decimal(str(value).strip())
    except InvalidOperation:
        return None


def _read_period_records(path: Path, period: str) -> list[dict[str, Any]]:
    expected_year, expected_month = parse_period(period)

    if not path.exists():
        raise ValueError(f"No existe el DBF fuente G7: {path}")

    table = DBF(
        str(path),
        load=True,
        encoding=DBF_ENCODING,
        char_decode_errors="ignore",
    )

    rows: list[dict[str, Any]] = []

    for record in table:
        year = _clean_text(record.get("CANOREG"))
        month = _clean_text(record.get("CMESREG")).zfill(2)

        if not year and not month:
            continue

        if year == expected_year and month == expected_month:
            rows.append(dict(record))

    return rows


def _add_issue(
    issues: list[G7SourceIssue],
    *,
    severity: G7SourceSeverity,
    section: str,
    source: str,
    field: str | None,
    message: str,
    value: object | None = None,
) -> None:
    issues.append(
        G7SourceIssue(
            severity=severity,
            section=section,
            source=source,
            field=field,
            message=message,
            value=value,
        )
    )


def _require_decimal(
    *,
    row: dict[str, Any],
    field: str,
    issues: list[G7SourceIssue],
    section: str,
    source: str,
) -> Decimal:
    value = _parse_decimal(row.get(field))

    if value is None:
        _add_issue(
            issues,
            severity=G7SourceSeverity.ERROR,
            section=section,
            source=source,
            field=field,
            message="Valor numérico obligatorio vacío o inválido.",
            value=row.get(field),
        )
        return Decimal("0")

    if value < Decimal("0"):
        _add_issue(
            issues,
            severity=G7SourceSeverity.ERROR,
            section=section,
            source=source,
            field=field,
            message="El valor no puede ser negativo.",
            value=value,
        )

    return value


def _validate_total(
    *,
    actual: Decimal,
    expected: Decimal,
    issues: list[G7SourceIssue],
    section: str,
    source: str,
    field: str,
) -> None:
    if abs(actual - expected) > TOTAL_TOLERANCE:
        _add_issue(
            issues,
            severity=G7SourceSeverity.ERROR,
            section=section,
            source=source,
            field=field,
            message="Total no coincide con la suma de sus componentes.",
            value=f"actual={actual}; esperado={expected}",
        )


def _validate_energy_rows(
    *,
    rows: list[dict[str, Any]],
    period: str,
    catalog: G7Catalog,
    expected_parties,
    section: str,
    issues: list[G7SourceIssue],
) -> list[G7EnergyRow]:
    expected_year, expected_month = parse_period(period)
    expected_by_code = {item.ccodgen: item for item in expected_parties}

    result: list[G7EnergyRow] = []
    seen: set[str] = set()

    for row in rows:
        ccosisi = _clean_text(row.get("CCOSISI"))
        ccodeemp = _clean_text(row.get("CCODEMP"))
        ccodgen = _clean_text(row.get("CCODGEN"))
        cdesgen = _clean_text(row.get("CDESGEN"))

        source = f"{expected_year}-{expected_month} / {ccodgen} / {cdesgen}"
        initial_error_count = len(issues)

        if ccosisi != catalog.system.ccosisi:
            _add_issue(
                issues,
                severity=G7SourceSeverity.ERROR,
                section=section,
                source=source,
                field="CCOSISI",
                message="CCOSISI no coincide con el catálogo G7.",
                value=ccosisi,
            )

        if ccodeemp != catalog.company.ccodeemp:
            _add_issue(
                issues,
                severity=G7SourceSeverity.ERROR,
                section=section,
                source=source,
                field="CCODEMP",
                message="CCODEMP no coincide con el catálogo G7.",
                value=ccodeemp,
            )

        party = expected_by_code.get(ccodgen)

        if party is None:
            _add_issue(
                issues,
                severity=G7SourceSeverity.ERROR,
                section=section,
                source=source,
                field="CCODGEN",
                message="CCODGEN no existe en la sección esperada del catálogo G7.",
                value=ccodgen,
            )
        elif cdesgen != party.cdesgen:
            _add_issue(
                issues,
                severity=G7SourceSeverity.ERROR,
                section=section,
                source=source,
                field="CDESGEN",
                message="CDESGEN no coincide con el catálogo G7.",
                value=cdesgen,
            )

        nenhopu = _require_decimal(row=row, field="NENHOPU", issues=issues, section=section, source=source)
        nenfuho = _require_decimal(row=row, field="NENFUHO", issues=issues, section=section, source=source)
        nenetot = _require_decimal(row=row, field="NENETOT", issues=issues, section=section, source=source)
        nvahopu = _require_decimal(row=row, field="NVAHOPU", issues=issues, section=section, source=source)
        nvafuho = _require_decimal(row=row, field="NVAFUHO", issues=issues, section=section, source=source)
        nvaltot = _require_decimal(row=row, field="NVALTOT", issues=issues, section=section, source=source)

        _validate_total(
            actual=nenetot,
            expected=nenhopu + nenfuho,
            issues=issues,
            section=section,
            source=source,
            field="NENETOT",
        )
        _validate_total(
            actual=nvaltot,
            expected=nvahopu + nvafuho,
            issues=issues,
            section=section,
            source=source,
            field="NVALTOT",
        )

        if ccodgen in seen:
            _add_issue(
                issues,
                severity=G7SourceSeverity.ERROR,
                section=section,
                source=source,
                field="CCODGEN",
                message="CCODGEN duplicado para el periodo.",
                value=ccodgen,
            )

        seen.add(ccodgen)

        final_error_count = len(issues)

        if final_error_count == initial_error_count:
            result.append(
                G7EnergyRow(
                    canoreg=expected_year,
                    cmesreg=expected_month,
                    ccosisi=ccosisi,
                    ccodeemp=ccodeemp,
                    ccodgen=ccodgen,
                    cdesgen=cdesgen,
                    nenhopu=nenhopu,
                    nenfuho=nenfuho,
                    nenetot=nenetot,
                    nvahopu=nvahopu,
                    nvafuho=nvafuho,
                    nvaltot=nvaltot,
                )
            )

    expected_keys = set(expected_by_code)

    for ccodgen in sorted(expected_keys - seen):
        _add_issue(
            issues,
            severity=G7SourceSeverity.ERROR,
            section=section,
            source=section,
            field="CCODGEN",
            message="Falta generador esperado para el periodo.",
            value=ccodgen,
        )

    for ccodgen in sorted(seen - expected_keys):
        _add_issue(
            issues,
            severity=G7SourceSeverity.ERROR,
            section=section,
            source=section,
            field="CCODGEN",
            message="Generador no esperado por catálogo G7.",
            value=ccodgen,
        )

    return result


def _validate_comnet_rows(
    *,
    rows: list[dict[str, Any]],
    period: str,
    catalog: G7Catalog,
    issues: list[G7SourceIssue],
) -> list[G7NetCommitmentRow]:
    expected_year, expected_month = parse_period(period)
    expected_by_code = {item.ccoddis: item for item in catalog.net_commitments}

    result: list[G7NetCommitmentRow] = []
    seen: set[str] = set()

    for row in rows:
        ccodeemp = _clean_text(row.get("CCODEMP"))
        ccoddis = _clean_text(row.get("CCODDIS"))
        cnomdis = _clean_text(row.get("CNOMDIS"))

        source = f"{expected_year}-{expected_month} / {ccoddis} / {cnomdis}"
        initial_error_count = len(issues)

        if ccodeemp != catalog.company.ccodeemp:
            _add_issue(
                issues,
                severity=G7SourceSeverity.ERROR,
                section="COMNET",
                source=source,
                field="CCODEMP",
                message="CCODEMP no coincide con el catálogo G7.",
                value=ccodeemp,
            )

        party = expected_by_code.get(ccoddis)

        if party is None:
            _add_issue(
                issues,
                severity=G7SourceSeverity.ERROR,
                section="COMNET",
                source=source,
                field="CCODDIS",
                message="CCODDIS no existe en net_commitments del catálogo G7.",
                value=ccoddis,
            )
        elif cnomdis != party.cnomdis:
            _add_issue(
                issues,
                severity=G7SourceSeverity.WARNING,
                section="COMNET",
                source=source,
                field="CNOMDIS",
                message="CNOMDIS no coincide con el catálogo G7.",
                value=cnomdis,
            )

        ncomnet = _require_decimal(row=row, field="NCOMNET", issues=issues, section="COMNET", source=source)

        if ccoddis in seen:
            _add_issue(
                issues,
                severity=G7SourceSeverity.ERROR,
                section="COMNET",
                source=source,
                field="CCODDIS",
                message="CCODDIS duplicado para el periodo.",
                value=ccoddis,
            )

        seen.add(ccoddis)

        final_error_count = len(issues)

        if final_error_count == initial_error_count:
            result.append(
                G7NetCommitmentRow(
                    canoreg=expected_year,
                    cmesreg=expected_month,
                    ccodeemp=ccodeemp,
                    ccoddis=ccoddis,
                    cnomdis=cnomdis,
                    ncomnet=ncomnet,
                )
            )

    expected_keys = set(expected_by_code)

    for ccoddis in sorted(expected_keys - seen):
        _add_issue(
            issues,
            severity=G7SourceSeverity.WARNING,
            section="COMNET",
            source="COMNET",
            field="CCODDIS",
            message="Distribuidora del catalogo sin registro COMNET para el periodo.",
            value=ccoddis,
        )

    for ccoddis in sorted(seen - expected_keys):
        _add_issue(
            issues,
            severity=G7SourceSeverity.ERROR,
            section="COMNET",
            source="COMNET",
            field="CCODDIS",
            message="Distribuidora no esperada por catálogo G7.",
            value=ccoddis,
        )

    return result


def _validate_transfer_rows(
    *,
    rows: list[dict[str, Any]],
    period: str,
    catalog: G7Catalog,
    expected_parties,
    section: str,
    value_field: str,
    issues: list[G7SourceIssue],
) -> list[G7PowerTransferRow] | list[G7TransferValuationRow]:
    expected_year, expected_month = parse_period(period)
    expected_by_code = {item.ccodgen: item for item in expected_parties}

    result: list[G7PowerTransferRow] | list[G7TransferValuationRow] = []
    seen: set[str] = set()

    for row in rows:
        ccodeemp = _clean_text(row.get("CCODEMP"))
        ccodgen = _clean_text(row.get("CCODGEN"))
        cnomgen = _clean_text(row.get("CNOMGEN"))

        source = f"{expected_year}-{expected_month} / {ccodgen} / {cnomgen}"
        initial_error_count = len(issues)

        if ccodeemp != catalog.company.ccodeemp:
            _add_issue(
                issues,
                severity=G7SourceSeverity.ERROR,
                section=section,
                source=source,
                field="CCODEMP",
                message="CCODEMP no coincide con el catálogo G7.",
                value=ccodeemp,
            )

        party = expected_by_code.get(ccodgen)

        if party is None:
            _add_issue(
                issues,
                severity=G7SourceSeverity.ERROR,
                section=section,
                source=source,
                field="CCODGEN",
                message="CCODGEN no existe en la sección esperada del catálogo G7.",
                value=ccodgen,
            )
        elif cnomgen != party.cnomgen:
            _add_issue(
                issues,
                severity=G7SourceSeverity.ERROR,
                section=section,
                source=source,
                field="CNOMGEN",
                message="CNOMGEN no coincide con el catálogo G7.",
                value=cnomgen,
            )

        value = _require_decimal(
            row=row,
            field=value_field,
            issues=issues,
            section=section,
            source=source,
        )

        if ccodgen in seen:
            _add_issue(
                issues,
                severity=G7SourceSeverity.ERROR,
                section=section,
                source=source,
                field="CCODGEN",
                message="CCODGEN duplicado para el periodo.",
                value=ccodgen,
            )

        seen.add(ccodgen)

        final_error_count = len(issues)

        if final_error_count == initial_error_count:
            if section == "TRAENE":
                result.append(
                    G7PowerTransferRow(
                        canoreg=expected_year,
                        cmesreg=expected_month,
                        ccodeemp=ccodeemp,
                        ccodgen=ccodgen,
                        cnomgen=cnomgen,
                        ntrapot=value,
                    )
                )
            else:
                result.append(
                    G7TransferValuationRow(
                        canoreg=expected_year,
                        cmesreg=expected_month,
                        ccodeemp=ccodeemp,
                        ccodgen=ccodgen,
                        cnomgen=cnomgen,
                        nvaltra=value,
                    )
                )

    expected_keys = set(expected_by_code)

    for ccodgen in sorted(expected_keys - seen):
        _add_issue(
            issues,
            severity=G7SourceSeverity.ERROR,
            section=section,
            source=section,
            field="CCODGEN",
            message="Falta generador esperado para el periodo.",
            value=ccodgen,
        )

    for ccodgen in sorted(seen - expected_keys):
        _add_issue(
            issues,
            severity=G7SourceSeverity.ERROR,
            section=section,
            source=section,
            field="CCODGEN",
            message="Generador no esperado por catálogo G7.",
            value=ccodgen,
        )

    return result


def validate_g7_sources(
    *,
    comene_path: Path,
    venene_path: Path,
    comnet_path: Path,
    traene_path: Path,
    valene_path: Path,
    period: str,
    catalog_path: Path,
) -> G7SourcesValidationResult:
    catalog = load_g7_catalog(catalog_path)
    issues: list[G7SourceIssue] = []

    comene_records = _read_period_records(comene_path, period)
    venene_records = _read_period_records(venene_path, period)
    comnet_records = _read_period_records(comnet_path, period)
    traene_records = _read_period_records(traene_path, period)
    valene_records = _read_period_records(valene_path, period)

    purchases = _validate_energy_rows(
        rows=comene_records,
        period=period,
        catalog=catalog,
        expected_parties=catalog.energy_purchases,
        section="COMENE",
        issues=issues,
    )
    sales = _validate_energy_rows(
        rows=venene_records,
        period=period,
        catalog=catalog,
        expected_parties=catalog.energy_sales,
        section="VENENE",
        issues=issues,
    )
    net_commitments = _validate_comnet_rows(
        rows=comnet_records,
        period=period,
        catalog=catalog,
        issues=issues,
    )
    power_transfers = _validate_transfer_rows(
        rows=traene_records,
        period=period,
        catalog=catalog,
        expected_parties=catalog.power_transfers,
        section="TRAENE",
        value_field="NTRAPOT",
        issues=issues,
    )
    transfer_valuations = _validate_transfer_rows(
        rows=valene_records,
        period=period,
        catalog=catalog,
        expected_parties=catalog.transfer_valuations,
        section="VALENE",
        value_field="NVALTRA",
        issues=issues,
    )

    return G7SourcesValidationResult(
        period=period,
        comene_path=comene_path,
        venene_path=venene_path,
        comnet_path=comnet_path,
        traene_path=traene_path,
        valene_path=valene_path,
        purchases=purchases,
        sales=sales,
        net_commitments=net_commitments,
        power_transfers=power_transfers,  # type: ignore[arg-type]
        transfer_valuations=transfer_valuations,  # type: ignore[arg-type]
        issues=issues,
    )
