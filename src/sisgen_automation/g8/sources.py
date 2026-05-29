from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from enum import Enum
from pathlib import Path
from typing import Any

from dbfread import DBF

from sisgen_automation.g8.catalog import G8Catalog, load_g8_catalog


REQUIRED_FIELDS = {
    "CANOREG",
    "CMESREG",
    "CCODEMP",
    "CNIVTEN",
    "CCOCLLI",
    "NTENELE",
    "CPOTMAX",
    "NHRSPUN",
    "NFUHOPU",
    "NEXHOPU",
    "NEXFUHO",
    "NENACHO",
    "NENACFU",
    "NENACTO",
    "NENREFA",
    "NPRENRE",
    "NPRPOHO",
    "NPRPOFU",
    "NPRPOEX",
    "NPRENHO",
    "NPRENFU",
    "NFACOTR",
    "NFACPOT",
    "NFACEXC",
}


class IssueSeverity(str, Enum):
    ERROR = "ERROR"
    WARNING = "WARNING"


@dataclass(frozen=True)
class G8SourceIssue:
    severity: IssueSeverity
    row: int | None
    client_code: str | None
    field: str | None
    message: str
    value: object | None = None


@dataclass(frozen=True)
class G8SourceRow:
    row_number: int
    client_code: str
    client_name: str
    voltage_level: str
    voltage: Decimal
    power_type: str
    contracted_hp_mw: Decimal
    contracted_hfp_mw: Decimal
    excess_hp_mw: Decimal
    excess_hfp_mw: Decimal
    active_hp_mwh: Decimal
    active_hfp_mwh: Decimal
    active_total_mwh: Decimal
    reactive_mvarh: Decimal
    reactive_price_cents: Decimal
    power_hp_price_s_kw: Decimal
    power_hfp_price_s_kw: Decimal
    excess_price_s_kw: Decimal
    active_hp_price_cents: Decimal
    active_hfp_price_cents: Decimal
    billing_others_s: Decimal
    billing_power_s: Decimal
    billing_excess_s: Decimal
    billing_active_s: Decimal
    billing_reactive_s: Decimal
    billing_total_s: Decimal
    average_price_cents_kwh: Decimal


@dataclass(frozen=True)
class G8SourceTotals:
    contracted_hp_mw: Decimal
    contracted_hfp_mw: Decimal
    excess_hp_mw: Decimal
    excess_hfp_mw: Decimal
    active_hp_mwh: Decimal
    active_hfp_mwh: Decimal
    active_total_mwh: Decimal
    reactive_mvarh: Decimal
    billing_power_s: Decimal
    billing_excess_s: Decimal
    billing_active_s: Decimal
    billing_reactive_s: Decimal
    billing_others_s: Decimal
    billing_total_s: Decimal
    average_price_cents_kwh: Decimal


@dataclass(frozen=True)
class G8SourcesValidationResult:
    period: str
    rows: tuple[G8SourceRow, ...]
    totals: G8SourceTotals
    issues: tuple[G8SourceIssue, ...]

    @property
    def errors(self) -> tuple[G8SourceIssue, ...]:
        return tuple(issue for issue in self.issues if issue.severity == IssueSeverity.ERROR)

    @property
    def warnings(self) -> tuple[G8SourceIssue, ...]:
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


def _money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _mwh(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)


def _mw(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)


def _avg(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _validate_structure(vefame_path: Path) -> list[G8SourceIssue]:
    table = DBF(str(vefame_path), load=False, char_decode_errors="ignore")
    fields = {field.name.upper() for field in table.fields}
    missing = sorted(REQUIRED_FIELDS - fields)

    return [
        G8SourceIssue(
            severity=IssueSeverity.ERROR,
            row=None,
            client_code=None,
            field=field,
            message="Campo requerido ausente en VEFAME.DBF.",
            value=None,
        )
        for field in missing
    ]


def _build_row(
    *,
    row_number: int,
    record: dict[str, Any],
    catalog: G8Catalog,
    issues: list[G8SourceIssue],
) -> G8SourceRow | None:
    client_code = str(record.get("CCOCLLI", "")).strip()
    client = catalog.clients_by_code.get(client_code)

    if client is None:
        issues.append(
            G8SourceIssue(
                severity=IssueSeverity.ERROR,
                row=row_number,
                client_code=client_code,
                field="CCOCLLI",
                message="Cliente libre no existe en catálogo G8.",
                value=client_code,
            )
        )
        return None

    company = str(record.get("CCODEMP", "")).strip()
    if company != catalog.company.ccodeemp:
        issues.append(
            G8SourceIssue(
                severity=IssueSeverity.ERROR,
                row=row_number,
                client_code=client_code,
                field="CCODEMP",
                message=f"Empresa inválida. Se esperaba {catalog.company.ccodeemp}.",
                value=company,
            )
        )

    voltage_level = str(record.get("CNIVTEN", "")).strip()
    if voltage_level != client.cnivten:
        issues.append(
            G8SourceIssue(
                severity=IssueSeverity.WARNING,
                row=row_number,
                client_code=client_code,
                field="CNIVTEN",
                message=f"Nivel de tensión distinto al catálogo ({client.cnivten}).",
                value=voltage_level,
            )
        )

    contracted_hp = _decimal(record.get("NHRSPUN"))
    contracted_hfp = _decimal(record.get("NFUHOPU"))
    excess_hp = _decimal(record.get("NEXHOPU"))
    excess_hfp = _decimal(record.get("NEXFUHO"))
    active_hp = _decimal(record.get("NENACHO"))
    active_hfp = _decimal(record.get("NENACFU"))
    active_total = _decimal(record.get("NENACTO"))
    reactive = _decimal(record.get("NENREFA"))

    expected_active_total = active_hp + active_hfp
    if abs(expected_active_total - active_total) > Decimal("0.005"):
        issues.append(
            G8SourceIssue(
                severity=IssueSeverity.WARNING,
                row=row_number,
                client_code=client_code,
                field="NENACTO",
                message="NENACTO difiere de NENACHO + NENACFU.",
                value=f"{active_total} != {expected_active_total}",
            )
        )

    reactive_price = _decimal(record.get("NPRENRE"))
    power_hp_price = _decimal(record.get("NPRPOHO"))
    power_hfp_price = _decimal(record.get("NPRPOFU"))
    excess_price = _decimal(record.get("NPRPOEX"))
    active_hp_price = _decimal(record.get("NPRENHO"))
    active_hfp_price = _decimal(record.get("NPRENFU"))
    billing_others = _decimal(record.get("NFACOTR"))

    billing_power = _money(
        (contracted_hp * Decimal("1000") * power_hp_price)
        + (contracted_hfp * Decimal("1000") * power_hfp_price)
    )
    billing_excess = _money(
        (excess_hp * Decimal("1000") * excess_price)
        + (excess_hfp * Decimal("1000") * excess_price)
    )
    billing_active = _money(
        (active_hp * Decimal("10") * active_hp_price)
        + (active_hfp * Decimal("10") * active_hfp_price)
    )
    billing_reactive = _money(reactive * Decimal("10") * reactive_price)
    billing_total = _money(
        billing_power + billing_excess + billing_active + billing_reactive + billing_others
    )

    if active_total > 0:
        average_price = _avg((billing_total - billing_others) / (active_total * Decimal("10")))
    else:
        average_price = Decimal("0.00")

    return G8SourceRow(
        row_number=row_number,
        client_code=client_code,
        client_name=client.name,
        voltage_level=voltage_level,
        voltage=_decimal(record.get("NTENELE")),
        power_type=str(record.get("CPOTMAX", "")).strip(),
        contracted_hp_mw=_mw(contracted_hp),
        contracted_hfp_mw=_mw(contracted_hfp),
        excess_hp_mw=_mw(excess_hp),
        excess_hfp_mw=_mw(excess_hfp),
        active_hp_mwh=_mwh(active_hp),
        active_hfp_mwh=_mwh(active_hfp),
        active_total_mwh=_mwh(active_total),
        reactive_mvarh=_mwh(reactive),
        reactive_price_cents=reactive_price,
        power_hp_price_s_kw=power_hp_price,
        power_hfp_price_s_kw=power_hfp_price,
        excess_price_s_kw=excess_price,
        active_hp_price_cents=active_hp_price,
        active_hfp_price_cents=active_hfp_price,
        billing_others_s=_money(billing_others),
        billing_power_s=billing_power,
        billing_excess_s=billing_excess,
        billing_active_s=billing_active,
        billing_reactive_s=billing_reactive,
        billing_total_s=billing_total,
        average_price_cents_kwh=average_price,
    )


def _sum(rows: tuple[G8SourceRow, ...], field: str) -> Decimal:
    return sum((getattr(row, field) for row in rows), Decimal("0"))


def _build_totals(rows: tuple[G8SourceRow, ...]) -> G8SourceTotals:
    active_total = _mwh(_sum(rows, "active_total_mwh"))
    billing_others = _money(_sum(rows, "billing_others_s"))
    billing_total = _money(_sum(rows, "billing_total_s"))

    if active_total > 0:
        average_price = _avg((billing_total - billing_others) / (active_total * Decimal("10")))
    else:
        average_price = Decimal("0.00")

    return G8SourceTotals(
        contracted_hp_mw=_mw(_sum(rows, "contracted_hp_mw")),
        contracted_hfp_mw=_mw(_sum(rows, "contracted_hfp_mw")),
        excess_hp_mw=_mw(_sum(rows, "excess_hp_mw")),
        excess_hfp_mw=_mw(_sum(rows, "excess_hfp_mw")),
        active_hp_mwh=_mwh(_sum(rows, "active_hp_mwh")),
        active_hfp_mwh=_mwh(_sum(rows, "active_hfp_mwh")),
        active_total_mwh=active_total,
        reactive_mvarh=_mwh(_sum(rows, "reactive_mvarh")),
        billing_power_s=_money(_sum(rows, "billing_power_s")),
        billing_excess_s=_money(_sum(rows, "billing_excess_s")),
        billing_active_s=_money(_sum(rows, "billing_active_s")),
        billing_reactive_s=_money(_sum(rows, "billing_reactive_s")),
        billing_others_s=billing_others,
        billing_total_s=billing_total,
        average_price_cents_kwh=average_price,
    )


def validate_g8_sources(
    *,
    vefame_path: Path,
    period: str,
    catalog_path: Path,
) -> G8SourcesValidationResult:
    if not vefame_path.exists():
        raise FileNotFoundError(f"No existe VEFAME.DBF: {vefame_path}")

    catalog = load_g8_catalog(catalog_path)
    year, month = parse_period(period)

    issues = _validate_structure(vefame_path)
    if any(issue.severity == IssueSeverity.ERROR for issue in issues):
        return G8SourcesValidationResult(
            period=period,
            rows=(),
            totals=_build_totals(()),
            issues=tuple(issues),
        )

    table = DBF(str(vefame_path), load=True, char_decode_errors="ignore")

    rows: list[G8SourceRow] = []
    for row_number, record in enumerate(table, start=1):
        record_year = str(record.get("CANOREG", "")).strip()
        record_month = str(record.get("CMESREG", "")).strip().zfill(2)

        if record_year != year or record_month != month:
            continue

        row = _build_row(
            row_number=row_number,
            record=dict(record),
            catalog=catalog,
            issues=issues,
        )
        if row is not None:
            rows.append(row)

    rows_by_code = {row.client_code: row for row in rows}
    for client in catalog.free_clients:
        if client.ccoclli not in rows_by_code:
            issues.append(
                G8SourceIssue(
                    severity=IssueSeverity.ERROR,
                    row=None,
                    client_code=client.ccoclli,
                    field="CCOCLLI",
                    message="Cliente del catálogo no tiene registro en VEFAME para el periodo.",
                    value=client.name,
                )
            )

    ordered_rows = tuple(
        rows_by_code[client.ccoclli]
        for client in catalog.free_clients
        if client.ccoclli in rows_by_code
    )

    return G8SourcesValidationResult(
        period=period,
        rows=ordered_rows,
        totals=_build_totals(ordered_rows),
        issues=tuple(issues),
    )
