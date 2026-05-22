from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import struct


@dataclass(frozen=True)
class DbfLayout:
    format_name: str
    header_length: int
    record_length: int


EXPECTED_SISGEN_LAYOUTS = {
    "CENHID": DbfLayout(
        format_name="CENHID",
        header_length=545,
        record_length=212,
    ),
    "CENTER": DbfLayout(
        format_name="CENTER",
        header_length=577,
        record_length=231,
    ),
    "DACOCE": DbfLayout(
        format_name="DACOCE",
        header_length=289,
        record_length=77,
    ),
}


@dataclass(frozen=True)
class ActualDbfLayout:
    path: Path
    version: int
    record_count: int
    header_length: int
    record_length: int


def read_actual_dbf_layout(path: Path) -> ActualDbfLayout:
    data = path.read_bytes()

    if len(data) < 32:
        raise ValueError(f"El archivo DBF es demasiado pequeño: {path}")

    return ActualDbfLayout(
        path=path,
        version=data[0],
        record_count=struct.unpack("<I", data[4:8])[0],
        header_length=struct.unpack("<H", data[8:10])[0],
        record_length=struct.unpack("<H", data[10:12])[0],
    )


def assert_sisgen_expected_layout(path: Path, format_name: str) -> None:
    normalized_format = format_name.upper()
    expected = EXPECTED_SISGEN_LAYOUTS[normalized_format]
    actual = read_actual_dbf_layout(path)

    if actual.version != 3:
        raise ValueError(
            f"{path.name} no tiene versión DBF esperada. "
            f"Esperado: 3. Actual: {actual.version}."
        )

    if (
        actual.header_length != expected.header_length
        or actual.record_length != expected.record_length
    ):
        raise ValueError(
            f"{path.name} no tiene la estructura esperada para SISGEN.\n"
            f"Formato: {normalized_format}\n"
            f"Header esperado: {expected.header_length}; actual: {actual.header_length}\n"
            f"Record length esperado: {expected.record_length}; actual: {actual.record_length}\n\n"
            "No uses DBF guardados desde Excel ni DBF de otra versión de SISGEN. "
            "Usa una copia limpia de los DBF que el emulador reconoce correctamente."
        )