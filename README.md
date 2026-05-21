# SISGEN Format Automation

Automatización de formatos mensuales SISGEN para archivos DBF históricos y generación del Formato G1.

Este proyecto busca reemplazar trabajo manual realizado en herramientas antiguas o emuladores, manteniendo un flujo reproducible, auditable y fácil de usar para usuarios internos.

## Estado actual

Versión inicial en desarrollo.

Funcionalidades implementadas:

- Perfilado técnico de archivos DBF.
- Validación histórica de `CENHID.DBF`, `CENTER.DBF` y `DACOCE.DBF`.
- Generación de plantillas Excel mensuales para:
  - `CENHID`
  - `CENTER`
  - `DACOCE`
- Validación de plantillas Excel antes de exportar.
- Exportación de nuevos DBF mensuales agregando el periodo validado.
- Validación integrada de fuentes para el Formato G1.
- Generación del Formato G1 en TXT.
- Interfaz gráfica desktop inicial para validar fuentes y generar G1.

## Formatos soportados

### CENHID

Datos mensuales de generación hidroeléctrica por grupo.

Flujo soportado:

```text
crear plantilla → validar plantilla → exportar DBF
```

### CENTER

Datos mensuales de generación termoeléctrica por grupo.

Incluye consumo de lubricantes (`NCONLUB`).

Flujo soportado:

```text
crear plantilla → validar plantilla → exportar DBF
```

### DACOCE

Datos mensuales por central:

- consumo propio
- producción neta
- máxima demanda

Flujo soportado:

```text
crear plantilla → validar plantilla → exportar DBF
```

### Formato G1

Generación de reporte TXT a partir de:

- `CENHID.DBF`
- `CENTER.DBF`
- `DACOCE.DBF`

El consumo de combustible térmico todavía está pendiente de integración porque falta identificar el DBF fuente correspondiente.

## Instalación

Crear y activar entorno virtual:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Instalar el proyecto:

```powershell
pip install -e .
```

Para usar la interfaz gráfica desktop:

```powershell
pip install -e ".[desktop]"
```

## Uso por consola

### Perfil de un DBF

```powershell
sisgen profile-dbf data\raw\CENHID.DBF
```

### Crear plantilla CENHID

```powershell
sisgen create-cenhid-template --period 2026-01 --catalog config\local\cenhid_units.yaml
```

### Validar plantilla CENHID

```powershell
sisgen validate-cenhid-template templates\CENHID_2026_01_template.xlsx --period 2026-01 --catalog config\local\cenhid_units.yaml
```

### Exportar CENHID DBF

```powershell
sisgen export-cenhid-dbf data\raw\CENHID.DBF templates\CENHID_2026_01_template.xlsx --period 2026-01 --catalog config\local\cenhid_units.yaml
```

### Validar fuentes G1

```powershell
sisgen validate-g1-sources `
  --cenhid data\raw\CENHID.DBF `
  --center data\raw\CENTER.DBF `
  --dacoce data\raw\DACOCE.DBF `
  --period 2025-12 `
  --cenhid-catalog config\local\cenhid_units.yaml `
  --center-catalog config\local\center_units.yaml
```

### Generar Formato G1 TXT

```powershell
sisgen create-g1-txt `
  --cenhid data\raw\CENHID.DBF `
  --center data\raw\CENTER.DBF `
  --dacoce data\raw\DACOCE.DBF `
  --period 2025-12 `
  --cenhid-catalog config\local\cenhid_units.yaml `
  --center-catalog config\local\center_units.yaml `
  --output reports\G1_2025_12_generated.txt
```

## Interfaz gráfica

Abrir la interfaz desktop:

```powershell
sisgen desktop
```

La interfaz inicial permite:

- seleccionar periodo
- seleccionar carpeta de DBF históricos
- seleccionar carpeta de salida
- seleccionar catálogos locales
- validar fuentes G1
- generar TXT G1

## Archivos locales no versionados

Por seguridad y limpieza, no se suben al repositorio:

- archivos DBF reales
- catálogos locales
- reportes generados
- plantillas Excel generadas
- carpetas de salida
- entorno virtual
- cachés de Python

Ejemplos:

```text
data/raw/*.DBF
data/output/
reports/
templates/*.xlsx
config/local/*.yaml
.venv/
__pycache__/
```

## Estructura principal

```text
src/sisgen_automation/
  cenhid/   lógica de CENHID
  center/   lógica de CENTER
  dacoce/   lógica de DACOCE
  g1/       validación y generación del Formato G1
  dbf/      utilidades DBF
  cli/      comandos de consola
  ui/       interfaz desktop
```

## Limitaciones conocidas

- El consumo de combustible térmico del Formato G1 todavía no está integrado.
- La interfaz desktop inicial solo cubre validación y generación G1.
- La creación de plantillas y exportación DBF aún se realiza principalmente por consola.
- El empaquetado como ejecutable Windows todavía está pendiente.
- El proyecto está en fase MVP y no debe considerarse versión final productiva.

## Próximos pasos

- Convertir la interfaz desktop en flujo completo por pestañas.
- Agregar generación de plantillas desde la interfaz.
- Agregar validación y exportación DBF desde la interfaz.
- Identificar el DBF fuente de combustible térmico.
- Empaquetar como ejecutable Windows.
- Documentar operación mensual paso a paso.

## Licencia

Pendiente de definir.
