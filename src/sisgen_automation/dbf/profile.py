from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path


@dataclass(frozen=True)
class DbfField:
    name: str
    field_type: str
    length: int
    decimal_count: int


@dataclass(frozen=True)
class DbfProfile:
    path: Path
    version_byte: int
    version_label: str
    last_update: date | None
    record_count: int
    active_record_count: int
    deleted_record_count: int
    header_length: int
    record_length: int
    file_size_bytes: int
    expected_min_size_bytes: int
    eof_marker_present: bool
    fields: list[DbfField]
    warnings: list[str]


def _decode_dbf_date(raw_header: bytes) -> date | None:
    year = 1900 + raw_header[1]
    month = raw_header[2]
    day = raw_header[3]

    try:
        return date(year, month, day)
    except ValueError:
        return None


def _version_label(version_byte: int) -> str:
    labels = {
        0x02: "FoxBASE",
        0x03: "FoxBASE+/dBASE III PLUS sin memo",
        0x30: "Visual FoxPro",
        0x31: "Visual FoxPro con autoincremento",
        0x43: "dBASE IV SQL",
        0x63: "dBASE IV SQL con memo",
        0x83: "dBASE III PLUS con memo",
        0x8B: "dBASE IV con memo",
        0xCB: "dBASE IV SQL table con memo",
        0xF5: "FoxPro con memo",
        0xFB: "FoxBASE",
    }

    return labels.get(version_byte, f"Versión DBF no identificada: 0x{version_byte:02X}")


def read_dbf_profile(path: Path) -> DbfProfile:
    if not path.exists():
        raise FileNotFoundError(f"No existe el archivo: {path}")

    if path.suffix.lower() != ".dbf":
        raise ValueError(f"El archivo no tiene extensión DBF: {path}")

    file_size = path.stat().st_size
    warnings: list[str] = []

    with path.open("rb") as dbf_file:
        header = dbf_file.read(32)

        if len(header) < 32:
            raise ValueError("El archivo DBF no tiene una cabecera válida de 32 bytes.")

        version_byte = header[0]
        last_update = _decode_dbf_date(header)
        record_count = int.from_bytes(header[4:8], byteorder="little")
        header_length = int.from_bytes(header[8:10], byteorder="little")
        record_length = int.from_bytes(header[10:12], byteorder="little")

        fields: list[DbfField] = []
        position = 32

        while position < header_length:
            dbf_file.seek(position)
            first_byte = dbf_file.read(1)

            if first_byte == b"\r":
                break

            descriptor = first_byte + dbf_file.read(31)

            if len(descriptor) != 32:
                raise ValueError("Descriptor de campo incompleto en la cabecera DBF.")

            raw_name = descriptor[0:11].split(b"\x00", maxsplit=1)[0]
            name = raw_name.decode("ascii", errors="replace").strip()

            if not name:
                break

            field_type = chr(descriptor[11])
            length = descriptor[16]
            decimal_count = descriptor[17]

            fields.append(
                DbfField(
                    name=name,
                    field_type=field_type,
                    length=length,
                    decimal_count=decimal_count,
                )
            )

            position += 32

        deleted_records = 0
        dbf_file.seek(header_length)

        for _ in range(record_count):
            deletion_marker = dbf_file.read(1)

            if deletion_marker == b"*":
                deleted_records += 1

            dbf_file.seek(record_length - 1, 1)

        expected_min_size = header_length + (record_count * record_length)

        eof_marker_present = False
        if file_size > expected_min_size:
            dbf_file.seek(expected_min_size)
            eof_marker_present = dbf_file.read(1) == b"\x1A"

    field_length_sum = 1 + sum(field.length for field in fields)

    if field_length_sum != record_length:
        warnings.append(
            "La suma de longitudes de campos no coincide con la longitud del registro. "
            f"Esperado por campos: {field_length_sum}. Cabecera DBF: {record_length}."
        )

    if file_size < expected_min_size:
        warnings.append(
            "El tamaño del archivo es menor al mínimo esperado según la cabecera DBF."
        )

    field_names = [field.name for field in fields]
    duplicated_fields = sorted({name for name in field_names if field_names.count(name) > 1})

    if duplicated_fields:
        warnings.append(f"Campos duplicados detectados: {', '.join(duplicated_fields)}")

    if not fields:
        warnings.append("No se detectaron campos en el archivo DBF.")

    return DbfProfile(
        path=path,
        version_byte=version_byte,
        version_label=_version_label(version_byte),
        last_update=last_update,
        record_count=record_count,
        active_record_count=record_count - deleted_records,
        deleted_record_count=deleted_records,
        header_length=header_length,
        record_length=record_length,
        file_size_bytes=file_size,
        expected_min_size_bytes=expected_min_size,
        eof_marker_present=eof_marker_present,
        fields=fields,
        warnings=warnings,
    )


def profile_to_markdown(profile: DbfProfile) -> str:
    lines: list[str] = []

    lines.append(f"# Perfil DBF: `{profile.path.name}`")
    lines.append("")
    lines.append("## Metadatos")
    lines.append("")
    lines.append("| Propiedad | Valor |")
    lines.append("|---|---:|")
    lines.append(f"| Ruta | `{profile.path}` |")
    lines.append(f"| Versión DBF | `{profile.version_byte}` - {profile.version_label} |")
    lines.append(f"| Fecha de última actualización DBF | {profile.last_update or 'No identificada'} |")
    lines.append(f"| Registros declarados | {profile.record_count} |")
    lines.append(f"| Registros activos | {profile.active_record_count} |")
    lines.append(f"| Registros eliminados | {profile.deleted_record_count} |")
    lines.append(f"| Longitud de cabecera | {profile.header_length} bytes |")
    lines.append(f"| Longitud por registro | {profile.record_length} bytes |")
    lines.append(f"| Tamaño del archivo | {profile.file_size_bytes} bytes |")
    lines.append(f"| Tamaño mínimo esperado | {profile.expected_min_size_bytes} bytes |")
    lines.append(f"| Marcador EOF presente | {'Sí' if profile.eof_marker_present else 'No'} |")
    lines.append("")
    lines.append("## Campos")
    lines.append("")
    lines.append("| Orden | Campo | Tipo | Longitud | Decimales |")
    lines.append("|---:|---|---|---:|---:|")

    for index, field in enumerate(profile.fields, start=1):
        lines.append(
            f"| {index} | `{field.name}` | `{field.field_type}` | "
            f"{field.length} | {field.decimal_count} |"
        )

    lines.append("")
    lines.append("## Advertencias")
    lines.append("")

    if profile.warnings:
        for warning in profile.warnings:
            lines.append(f"- {warning}")
    else:
        lines.append("- No se detectaron advertencias estructurales.")

    lines.append("")

    return "\n".join(lines)


def write_profile_markdown(profile: DbfProfile, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(profile_to_markdown(profile), encoding="utf-8")