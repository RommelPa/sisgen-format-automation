from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Mapping

from dbfread import DBF

from sisgen_automation.dbf.profile import DbfField, read_dbf_profile
from sisgen_automation.vefame.template import DBF_ENCODING, parse_period
from sisgen_automation.vefame.template_validation import (
    VefameTemplateRecord,
    validate_vefame_template,
)


DBF_EOF_MARKER = b"\x1A"


@dataclass(frozen=True)
class VefameExportResult:
    period: str
    output_path: Path
    original_record_count: int
    appended_record_count: int
    final_record_count: int


def default_vefame_output_path(period: str) -> Path:
    return Path("reports") / "dbf" / period / "VEFAME.DBF"


def _period_exists(source_dbf_path: Path, period: str) -> bool:
    expected_year, expected_month = parse_period(period)

    table = DBF(
        str(source_dbf_path),
        load=True,
        encoding=DBF_ENCODING,
        char_decode_errors="ignore",
    )

    for record in table:
        year = str(record.get("CANOREG", "")).strip()
        month = str(record.get("CMESREG", "")).strip().zfill(2)

        if year == expected_year and month == expected_month:
            return True

    return False


def _format_character(value: object, field: DbfField) -> bytes:
    text = "" if value is None else str(value)

    if len(text) > field.length:
        raise ValueError(
            f"El valor '{text}' excede la longitud del campo {field.name} "
            f"({field.length})."
        )

    return text.ljust(field.length).encode(DBF_ENCODING, errors="replace")


def _format_numeric(value: object, field: DbfField) -> bytes:
    if value is None:
        text = ""
    else:
        decimal_value = Decimal(str(value))

        if field.decimal_count > 0:
            quantizer = Decimal("1").scaleb(-field.decimal_count)
            decimal_value = decimal_value.quantize(quantizer, rounding=ROUND_HALF_UP)
            text = f"{decimal_value:.{field.decimal_count}f}"
        else:
            decimal_value = decimal_value.quantize(Decimal("1"), rounding=ROUND_HALF_UP)
            text = f"{decimal_value:.0f}"

    if len(text) > field.length:
        raise ValueError(
            f"El valor '{text}' excede la longitud del campo {field.name} "
            f"({field.length})."
        )

    return text.rjust(field.length).encode("ascii")


def _serialize_record(
    *,
    record: Mapping[str, object],
    fields: list[DbfField],
    record_length: int,
) -> bytes:
    chunks = [b" "]

    for field in fields:
        value = record.get(field.name)

        if field.field_type == "C":
            chunks.append(_format_character(value, field))
        elif field.field_type == "N":
            chunks.append(_format_numeric(value, field))
        else:
            raise ValueError(f"Tipo de campo DBF no soportado: {field.name} {field.field_type}")

    serialized = b"".join(chunks)

    if len(serialized) != record_length:
        raise ValueError(
            f"Registro serializado con longitud inválida. "
            f"Esperado: {record_length}. Actual: {len(serialized)}."
        )

    return serialized


def _record_to_mapping(record: VefameTemplateRecord) -> dict[str, object]:
    return dict(record.values)


def _write_appended_dbf(
    *,
    source_dbf_path: Path,
    output_path: Path,
    records: list[VefameTemplateRecord],
) -> VefameExportResult:
    profile = read_dbf_profile(source_dbf_path)
    source_bytes = source_dbf_path.read_bytes()

    expected_data_end = profile.header_length + (profile.record_count * profile.record_length)

    if len(source_bytes) < expected_data_end:
        raise ValueError(
            f"El archivo DBF fuente parece truncado: {source_dbf_path}. "
            f"Tamaño esperado mínimo: {expected_data_end}. Tamaño real: {len(source_bytes)}."
        )

    header = bytearray(source_bytes[: profile.header_length])
    existing_records = source_bytes[profile.header_length : expected_data_end]

    source_has_eof = (
        len(source_bytes) > expected_data_end
        and source_bytes[expected_data_end : expected_data_end + 1] == DBF_EOF_MARKER
    )

    serialized_records = [
        _serialize_record(
            record=_record_to_mapping(record),
            fields=profile.fields,
            record_length=profile.record_length,
        )
        for record in records
    ]

    final_record_count = profile.record_count + len(serialized_records)

    # Compatibilidad SISGEN:
    # conservamos la cabecera original y solo actualizamos el contador de registros.
    header[4:8] = final_record_count.to_bytes(4, byteorder="little")

    output_bytes = bytes(header) + existing_records + b"".join(serialized_records)

    if source_has_eof:
        output_bytes += DBF_EOF_MARKER

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(output_bytes)

    return VefameExportResult(
        period="",
        output_path=output_path,
        original_record_count=profile.record_count,
        appended_record_count=len(serialized_records),
        final_record_count=final_record_count,
    )


def export_vefame_dbf(
    *,
    source_dbf_path: Path,
    template_path: Path,
    period: str,
    catalog_path: Path,
    output_path: Path | None = None,
    allow_existing_period: bool = False,
) -> VefameExportResult:
    validation_result = validate_vefame_template(
        template_path=template_path,
        period=period,
        catalog_path=catalog_path,
    )

    if validation_result.has_errors:
        raise ValueError("La plantilla VEFAME tiene errores. Corrige la plantilla antes de exportar el DBF.")

    if not allow_existing_period and _period_exists(source_dbf_path, period):
        raise ValueError(
            f"El periodo {period} ya existe en el DBF histórico. "
            "No se exportó para evitar duplicar información."
        )

    if output_path is None:
        output_path = default_vefame_output_path(period)

    result = _write_appended_dbf(
        source_dbf_path=source_dbf_path,
        output_path=output_path,
        records=list(validation_result.records),
    )

    return VefameExportResult(
        period=period,
        output_path=result.output_path,
        original_record_count=result.original_record_count,
        appended_record_count=result.appended_record_count,
        final_record_count=result.final_record_count,
    )
