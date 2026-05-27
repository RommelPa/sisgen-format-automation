from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from enum import Enum
from pathlib import Path
from typing import Any

from dbfread import DBF  # type: ignore[import-untyped]

from sisgen_automation.g11.catalog import G11Catalog, load_g11_catalog


DBF_ENCODING = "cp850"


class G11SourceSeverity(str, Enum):
    ERROR = "ERROR"
    WARNING = "WARNING"


@dataclass(frozen=True)
class G11SourceIssue:
    severity: G11SourceSeverity
    section: str
    source: str
    field: str | None
    message: str
    value: object | None = None


@dataclass(frozen=True)
class G11HydroRow:
    canoreg: str
    cmesreg: str
    ccodgen: str
    ccodcen: str
    cnomcen: str
    cnomcue: str
    ncamedi: Decimal
    nalvout: Decimal


@dataclass(frozen=True)
class G11ThermalRow:
    canoreg: str
    cmesreg: str
    ccodgen: str
    ccodcen: str
    cnomcen: str
    ctipcom: str
    cdescom: str
    nvolalm: Decimal
    nadqmes: Decimal

    @property
    def total(self) -> Decimal:
        return self.nvolalm + self.nadqmes


@dataclass(frozen=True)
class G11SourcesValidationResult:
    period: str
    cacehi_path: Path
    cacete_path: Path
    hydro_rows: list[G11HydroRow]
    thermal_rows: list[G11ThermalRow]
    issues: list[G11SourceIssue]

    @property
    def errors(self) -> list[G11SourceIssue]:
        return [issue for issue in self.issues if issue.severity == G11SourceSeverity.ERROR]

    @property
    def warnings(self) -> list[G11SourceIssue]:
        return [issue for issue in self.issues if issue.severity == G11SourceSeverity.WARNING]

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
        raise ValueError(f"No existe el DBF fuente G11: {path}")

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

        if year == expected_year and month == expected_month:
            rows.append(dict(record))

    return rows


def _add_issue(
    issues: list[G11SourceIssue],
    *,
    severity: G11SourceSeverity,
    section: str,
    source: str,
    field: str | None,
    message: str,
    value: object | None = None,
) -> None:
    issues.append(
        G11SourceIssue(
            severity=severity,
            section=section,
            source=source,
            field=field,
            message=message,
            value=value,
        )
    )


def _validate_hydro_rows(
    *,
    rows: list[dict[str, Any]],
    period: str,
    catalog: G11Catalog,
    issues: list[G11SourceIssue],
) -> list[G11HydroRow]:
    expected_year, expected_month = parse_period(period)
    hydro_catalog = {item.ccodcen: item for item in catalog.hydro}

    result: list[G11HydroRow] = []
    seen: set[str] = set()

    for row in rows:
        ccodgen = _clean_text(row.get("CCODGEN"))
        ccodcen = _clean_text(row.get("CCODCEN"))
        cnomcen = _clean_text(row.get("CNOMCEN"))
        cnomcue = _clean_text(row.get("CNOMCUE"))

        source_value = f"{expected_year}-{expected_month} / {ccodcen} / {cnomcen}"

        row_has_error = False

        if ccodgen != catalog.company.ccodgen:
            row_has_error = True
            _add_issue(
                issues,
                severity=G11SourceSeverity.ERROR,
                section="CACEHI",
                source=source_value,
                field="CCODGEN",
                message="CCODGEN no coincide con el catálogo G11.",
                value=ccodgen,
            )

        unit = hydro_catalog.get(ccodcen)

        if unit is None:
            row_has_error = True
            _add_issue(
                issues,
                severity=G11SourceSeverity.ERROR,
                section="CACEHI",
                source=source_value,
                field="CCODCEN",
                message="CCODCEN no existe en el catálogo G11 hidro.",
                value=ccodcen,
            )
        else:
            if cnomcen != unit.cnomcen:
                row_has_error = True
                _add_issue(
                    issues,
                    severity=G11SourceSeverity.ERROR,
                    section="CACEHI",
                    source=source_value,
                    field="CNOMCEN",
                    message="CNOMCEN no coincide con el catálogo G11.",
                    value=cnomcen,
                )

            if cnomcue != unit.cnomcue:
                row_has_error = True
                _add_issue(
                    issues,
                    severity=G11SourceSeverity.ERROR,
                    section="CACEHI",
                    source=source_value,
                    field="CNOMCUE",
                    message="CNOMCUE no coincide con el catálogo G11.",
                    value=cnomcue,
                )

        ncamedi = _parse_decimal(row.get("NCAMEDI"))
        nalvout = _parse_decimal(row.get("NALVOUT"))

        if ncamedi is None:
            row_has_error = True
            _add_issue(
                issues,
                severity=G11SourceSeverity.ERROR,
                section="CACEHI",
                source=source_value,
                field="NCAMEDI",
                message="Valor numérico obligatorio vacío o inválido.",
                value=row.get("NCAMEDI"),
            )
            ncamedi = Decimal("0")

        if nalvout is None:
            row_has_error = True
            _add_issue(
                issues,
                severity=G11SourceSeverity.ERROR,
                section="CACEHI",
                source=source_value,
                field="NALVOUT",
                message="Valor numérico obligatorio vacío o inválido.",
                value=row.get("NALVOUT"),
            )
            nalvout = Decimal("0")

        if ncamedi < Decimal("0"):
            row_has_error = True
            _add_issue(
                issues,
                severity=G11SourceSeverity.ERROR,
                section="CACEHI",
                source=source_value,
                field="NCAMEDI",
                message="El valor no puede ser negativo.",
                value=ncamedi,
            )

        if nalvout < Decimal("0"):
            row_has_error = True
            _add_issue(
                issues,
                severity=G11SourceSeverity.ERROR,
                section="CACEHI",
                source=source_value,
                field="NALVOUT",
                message="El valor no puede ser negativo.",
                value=nalvout,
            )

        if ccodcen in seen:
            row_has_error = True
            _add_issue(
                issues,
                severity=G11SourceSeverity.ERROR,
                section="CACEHI",
                source=source_value,
                field="CCODCEN",
                message="Central hidro duplicada para el periodo.",
                value=ccodcen,
            )

        seen.add(ccodcen)

        if not row_has_error:
            result.append(
                G11HydroRow(
                    canoreg=expected_year,
                    cmesreg=expected_month,
                    ccodgen=ccodgen,
                    ccodcen=ccodcen,
                    cnomcen=cnomcen,
                    cnomcue=cnomcue,
                    ncamedi=ncamedi,
                    nalvout=nalvout,
                )
            )

    expected_keys = set(hydro_catalog)

    missing = sorted(expected_keys - seen)
    extra = sorted(seen - expected_keys)

    for ccodcen in missing:
        _add_issue(
            issues,
            severity=G11SourceSeverity.ERROR,
            section="CACEHI",
            source="CACEHI.DBF",
            field="CCODCEN",
            message="Falta central hidro esperada para el periodo.",
            value=ccodcen,
        )

    for ccodcen in extra:
        _add_issue(
            issues,
            severity=G11SourceSeverity.ERROR,
            section="CACEHI",
            source="CACEHI.DBF",
            field="CCODCEN",
            message="Central hidro no esperada por catálogo G11.",
            value=ccodcen,
        )

    return result


def _validate_thermal_rows(
    *,
    rows: list[dict[str, Any]],
    period: str,
    catalog: G11Catalog,
    issues: list[G11SourceIssue],
) -> list[G11ThermalRow]:
    expected_year, expected_month = parse_period(period)
    thermal_catalog = {
        (item.ccodcen, item.ctipcom): item
        for item in catalog.thermal_fuels
    }

    result: list[G11ThermalRow] = []
    seen: set[tuple[str, str]] = set()

    for row in rows:
        ccodgen = _clean_text(row.get("CCODGEN"))
        ccodcen = _clean_text(row.get("CCODCEN"))
        cnomcen = _clean_text(row.get("CNOMCEN"))
        ctipcom = _clean_text(row.get("CTIPCOM"))
        cdescom = _clean_text(row.get("CDESCOM"))

        key = (ccodcen, ctipcom)
        source_value = f"{expected_year}-{expected_month} / {ccodcen} / {ctipcom}"

        row_has_error = False

        if ccodgen != catalog.company.ccodgen:
            row_has_error = True
            _add_issue(
                issues,
                severity=G11SourceSeverity.ERROR,
                section="CACETE",
                source=source_value,
                field="CCODGEN",
                message="CCODGEN no coincide con el catálogo G11.",
                value=ccodgen,
            )

        fuel = thermal_catalog.get(key)

        if fuel is None:
            row_has_error = True
            _add_issue(
                issues,
                severity=G11SourceSeverity.ERROR,
                section="CACETE",
                source=source_value,
                field="CLAVE",
                message="CCODCEN/CTIPCOM no existe en el catálogo G11 térmico.",
                value=f"{ccodcen} / {ctipcom}",
            )
        else:
            if cnomcen != fuel.cnomcen:
                row_has_error = True
                _add_issue(
                    issues,
                    severity=G11SourceSeverity.ERROR,
                    section="CACETE",
                    source=source_value,
                    field="CNOMCEN",
                    message="CNOMCEN no coincide con el catálogo G11.",
                    value=cnomcen,
                )

            if cdescom != fuel.cdescom:
                row_has_error = True
                _add_issue(
                    issues,
                    severity=G11SourceSeverity.ERROR,
                    section="CACETE",
                    source=source_value,
                    field="CDESCOM",
                    message="CDESCOM no coincide con el catálogo G11.",
                    value=cdescom,
                )

        nvolalm = _parse_decimal(row.get("NVOLALM"))
        nadqmes = _parse_decimal(row.get("NADQMES"))

        if nvolalm is None:
            row_has_error = True
            _add_issue(
                issues,
                severity=G11SourceSeverity.ERROR,
                section="CACETE",
                source=source_value,
                field="NVOLALM",
                message="Valor numérico obligatorio vacío o inválido.",
                value=row.get("NVOLALM"),
            )
            nvolalm = Decimal("0")

        if nadqmes is None:
            row_has_error = True
            _add_issue(
                issues,
                severity=G11SourceSeverity.ERROR,
                section="CACETE",
                source=source_value,
                field="NADQMES",
                message="Valor numérico obligatorio vacío o inválido.",
                value=row.get("NADQMES"),
            )
            nadqmes = Decimal("0")

        if nvolalm < Decimal("0"):
            row_has_error = True
            _add_issue(
                issues,
                severity=G11SourceSeverity.ERROR,
                section="CACETE",
                source=source_value,
                field="NVOLALM",
                message="El valor no puede ser negativo.",
                value=nvolalm,
            )

        if nadqmes < Decimal("0"):
            row_has_error = True
            _add_issue(
                issues,
                severity=G11SourceSeverity.ERROR,
                section="CACETE",
                source=source_value,
                field="NADQMES",
                message="El valor no puede ser negativo.",
                value=nadqmes,
            )

        if key in seen:
            row_has_error = True
            _add_issue(
                issues,
                severity=G11SourceSeverity.ERROR,
                section="CACETE",
                source=source_value,
                field="CLAVE",
                message="Central térmica/combustible duplicado para el periodo.",
                value=f"{ccodcen} / {ctipcom}",
            )

        seen.add(key)

        if not row_has_error:
            result.append(
                G11ThermalRow(
                    canoreg=expected_year,
                    cmesreg=expected_month,
                    ccodgen=ccodgen,
                    ccodcen=ccodcen,
                    cnomcen=cnomcen,
                    ctipcom=ctipcom,
                    cdescom=cdescom,
                    nvolalm=nvolalm,
                    nadqmes=nadqmes,
                )
            )

    expected_keys = set(thermal_catalog)

    missing = sorted(expected_keys - seen)
    extra = sorted(seen - expected_keys)

    for ccodcen, ctipcom in missing:
        _add_issue(
            issues,
            severity=G11SourceSeverity.ERROR,
            section="CACETE",
            source="CACETE.DBF",
            field="CLAVE",
            message="Falta central térmica/combustible esperado para el periodo.",
            value=f"{ccodcen} / {ctipcom}",
        )

    for ccodcen, ctipcom in extra:
        _add_issue(
            issues,
            severity=G11SourceSeverity.ERROR,
            section="CACETE",
            source="CACETE.DBF",
            field="CLAVE",
            message="Central térmica/combustible no esperado por catálogo G11.",
            value=f"{ccodcen} / {ctipcom}",
        )

    return result


def validate_g11_sources(
    *,
    cacehi_path: Path,
    cacete_path: Path,
    period: str,
    catalog_path: Path,
) -> G11SourcesValidationResult:
    catalog = load_g11_catalog(catalog_path)

    issues: list[G11SourceIssue] = []

    cacehi_records = _read_period_records(cacehi_path, period)
    cacete_records = _read_period_records(cacete_path, period)

    hydro_rows = _validate_hydro_rows(
        rows=cacehi_records,
        period=period,
        catalog=catalog,
        issues=issues,
    )
    thermal_rows = _validate_thermal_rows(
        rows=cacete_records,
        period=period,
        catalog=catalog,
        issues=issues,
    )

    return G11SourcesValidationResult(
        period=period,
        cacehi_path=cacehi_path,
        cacete_path=cacete_path,
        hydro_rows=hydro_rows,
        thermal_rows=thermal_rows,
        issues=issues,
    )