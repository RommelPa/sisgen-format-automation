from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Literal

from dbfread import DBF  # type: ignore[import-untyped]

from sisgen_automation.g2.catalog import load_g2_catalog


IssueSeverity = Literal["ERROR", "WARNING"]


@dataclass(frozen=True)
class G2SourceIssue:
    severity: IssueSeverity
    source: str
    field: str | None
    message: str
    value: str | None = None


@dataclass(frozen=True)
class G2SaleRow:
    year: str
    month: str
    company_code: str
    distributor_code: str
    distributor_name: str
    csieldi: str
    ccosues: str
    delivery_bar_name: str
    client_type: str
    voltage_kv: Decimal
    ppb: Decimal
    pebp: Decimal
    pebf: Decimal
    energy_hp_mwh: Decimal
    energy_hfp_mwh: Decimal
    energy_total_mwh: Decimal
    contracted_power_hp_kw: Decimal
    contracted_power_hfp_kw: Decimal
    max_demand_hp_kw: Decimal
    max_demand_hfp_kw: Decimal
    billing_power_pen: Decimal
    billing_energy_pen: Decimal

    @property
    def billing_total_pen(self) -> Decimal:
        return self.billing_power_pen + self.billing_energy_pen


@dataclass(frozen=True)
class G2SourcesValidationResult:
    vepoen_path: Path
    catalog_path: Path
    period: str
    rows: list[G2SaleRow]
    issues: list[G2SourceIssue]
    distributor_order: list[str]

    @property
    def errors(self) -> list[G2SourceIssue]:
        return [item for item in self.issues if item.severity == "ERROR"]

    @property
    def warnings(self) -> list[G2SourceIssue]:
        return [item for item in self.issues if item.severity == "WARNING"]

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
    issues: list[G2SourceIssue],
    field: str,
    context: str,
) -> Decimal:
    parsed = _to_decimal(value)

    if parsed is None:
        issues.append(
            G2SourceIssue(
                severity="ERROR",
                source="VEPOEN",
                field=field,
                message="Valor numérico obligatorio vacío o inválido.",
                value=context,
            )
        )
        return Decimal("0")

    return parsed

def _decimal_or_zero(value: object) -> Decimal:
    parsed = _to_decimal(value)

    if parsed is None:
        return Decimal("0")

    return parsed

def validate_g2_sources(
    *,
    vepoen_path: Path,
    catalog_path: Path,
    period: str,
) -> G2SourcesValidationResult:
    expected_year, expected_month = parse_period(period)
    catalog = load_g2_catalog(catalog_path)

    if not vepoen_path.exists():
        raise ValueError(f"No existe VEPOEN.DBF: {vepoen_path}")

    table = DBF(str(vepoen_path), load=True, char_decode_errors="ignore")

    issues: list[G2SourceIssue] = []
    rows: list[G2SaleRow] = []

    for record in table:
        year = _clean_text(record.get("CANOREG"))
        month = _clean_text(record.get("CMESREG")).zfill(2)

        if year != expected_year or month != expected_month:
            continue

        company_code = _clean_text(record.get("CCODEMP"))
        distributor_code = _clean_text(record.get("CCODDIS"))
        csieldi = _clean_text(record.get("CSIELDI"))
        ccosues = _clean_text(record.get("CCOSUES"))
        delivery_bar_name = _clean_text(record.get("CNOMBAR"))
        client_type = _clean_text(record.get("CCLRELI"))

        context = f"{year}-{month} / {distributor_code} / {delivery_bar_name}"

        if company_code != catalog.company.ccodeemp:
            issues.append(
                G2SourceIssue(
                    severity="WARNING",
                    source="VEPOEN",
                    field="CCODEMP",
                    message="Código de empresa distinto al configurado en catálogo G2.",
                    value=f"{context}; CCODEMP={company_code}",
                )
            )

        distributor = catalog.distributors.get(distributor_code)
        if distributor is None:
            issues.append(
                G2SourceIssue(
                    severity="ERROR",
                    source="VEPOEN",
                    field="CCODDIS",
                    message="Distribuidora no existe en catálogo G2.",
                    value=context,
                )
            )
            distributor_name = distributor_code
        else:
            distributor_name = distributor.display_name

        if not delivery_bar_name:
            issues.append(
                G2SourceIssue(
                    severity="ERROR",
                    source="VEPOEN",
                    field="CNOMBAR",
                    message="Nombre de barra vacío.",
                    value=context,
                )
            )

        rows.append(
            G2SaleRow(
                year=year,
                month=month,
                company_code=company_code,
                distributor_code=distributor_code,
                distributor_name=distributor_name,
                csieldi=csieldi,
                ccosues=ccosues,
                delivery_bar_name=delivery_bar_name,
                client_type=client_type,
                voltage_kv=_require_decimal(record.get("NTENBAR"), issues, "NTENBAR", context),
                ppb=_require_decimal(record.get("NPRPOBA"), issues, "NPRPOBA", context),
                pebp=_require_decimal(record.get("NPRENHO"), issues, "NPRENHO", context),
                pebf=_require_decimal(record.get("NPRENFU"), issues, "NPRENFU", context),
                energy_hp_mwh=_require_decimal(record.get("NENVEHO"), issues, "NENVEHO", context),
                energy_hfp_mwh=_require_decimal(record.get("NENVEFU"), issues, "NENVEFU", context),
                energy_total_mwh=_require_decimal(record.get("NENVETO"), issues, "NENVETO", context),
                contracted_power_hp_kw=_require_decimal(record.get("NPOCOHO"), issues, "NPOCOHO", context),
                contracted_power_hfp_kw=_require_decimal(record.get("NPOCOFU"), issues, "NPOCOFU", context),
                max_demand_hp_kw=_decimal_or_zero(record.get("NMADEHO")),
                max_demand_hfp_kw=_decimal_or_zero(record.get("NMADEFU")),
                billing_power_pen=_require_decimal(record.get("NFACPOT"), issues, "NFACPOT", context),
                billing_energy_pen=_require_decimal(record.get("NFACENE"), issues, "NFACENE", context),
            )
        )

    if not rows:
        issues.append(
            G2SourceIssue(
                severity="ERROR",
                source="VEPOEN",
                field=None,
                message="No se encontraron registros VEPOEN para el periodo.",
                value=period,
            )
        )

    if csieldi:
        issues.append(
            G2SourceIssue(
                severity="WARNING",
                source="VEPOEN",
                field="CSIELDI",
                message="CSIELDI tiene valor, pero para esta versión se esperaba vacío.",
                value=f"{context}; CSIELDI={csieldi}",
            )
        )

    if ccosues:
        issues.append(
            G2SourceIssue(
                severity="WARNING",
                source="VEPOEN",
                field="CCOSUES",
                message="CCOSUES tiene valor, pero para esta versión se esperaba vacío.",
                value=f"{context}; CCOSUES={ccosues}",
            )
        )

    return G2SourcesValidationResult(
        vepoen_path=vepoen_path,
        catalog_path=catalog_path,
        period=period,
        rows=rows,
        issues=issues,
        distributor_order=list(catalog.distributors.keys()),
    )