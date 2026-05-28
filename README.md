# SISGEN Format Automation

Automatización de formatos mensuales SISGEN para archivos DBF históricos, generación de plantillas Excel, exportación de DBF mensuales y generación de reportes TXT.

El proyecto reemplaza trabajo manual realizado en herramientas antiguas o emuladores. Mantiene un flujo reproducible, auditable y fácil de usar para operación mensual.

## Estado actual

Versión actual: `v1.4.0`

Funcionalidades implementadas:

* Perfilado técnico de archivos DBF.
* Validación histórica de archivos DBF.
* Generación de plantillas Excel mensuales.
* Validación de plantillas antes de exportar.
* Exportación de nuevos DBF mensuales agregando el periodo validado.
* Generación de reportes TXT SISGEN.
* Interfaz gráfica desktop para flujo mensual.
* CLI modularizado por formato.
* Soporte funcional para formatos G1, G2, G7 y G11.

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

* consumo propio
* producción neta
* máxima demanda

Flujo soportado:

```text
crear plantilla → validar plantilla → exportar DBF
```

### COMCEN

Datos mensuales de consumo propio por central.

Flujo soportado:

```text
crear plantilla → validar plantilla → exportar DBF
```

### VEPOEN

Datos mensuales de ventas de potencia y energía.

Este archivo alimenta el Formato G2.

Flujo soportado:

```text
crear plantilla → validar plantilla → exportar DBF → generar TXT G2
```

### CACEHI y CACETE

Datos mensuales para el Formato G11.

* `CACEHI`: información hidroeléctrica.
* `CACETE`: información termoeléctrica.

Flujo soportado:

```text
crear plantillas → validar plantillas → exportar DBF → generar TXT G11
```

### COMENE, VENENE, COMNET, TRAENE y VALENE

Datos mensuales para el Formato G7.

* `COMENE`: compras de energía.
* `VENENE`: ventas de energía.
* `COMNET`: compromisos netos.
* `TRAENE`: transferencias de potencia.
* `VALENE`: valorización de transferencias.

Flujo soportado:

```text
crear plantillas → validar plantillas → exportar DBF → generar TXT G7
```

## Reportes TXT soportados

### Formato G1

Generación de reporte TXT a partir de:

* `CENHID.DBF`
* `CENTER.DBF`
* `DACOCE.DBF`
* `COMCEN.DBF`

### Formato G2

Generación de reporte TXT a partir de:

* `VEPOEN.DBF`

### Formato G7

Generación de reporte TXT a partir de:

* `COMENE.DBF`
* `VENENE.DBF`
* `COMNET.DBF`
* `TRAENE.DBF`
* `VALENE.DBF`

### Formato G11

Generación de reporte TXT a partir de:

* `CACEHI.DBF`
* `CACETE.DBF`

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

### Perfil técnico de un DBF

```powershell
sisgen profile-dbf data\raw\CENHID.DBF
```

### Crear plantilla mensual CENHID

```powershell
sisgen create-cenhid-template `
  --period 2026-01 `
  --catalog config\local\cenhid_units.yaml
```

### Validar plantilla CENHID

```powershell
sisgen validate-cenhid-template `
  reports\templates\CENHID_2026_01_template.xlsx `
  --period 2026-01 `
  --catalog config\local\cenhid_units.yaml
```

### Exportar CENHID DBF

```powershell
sisgen export-cenhid-dbf `
  data\raw\CENHID.DBF `
  reports\templates\CENHID_2026_01_template.xlsx `
  --period 2026-01 `
  --catalog config\local\cenhid_units.yaml
```

### Validar fuentes G1

```powershell
sisgen validate-g1-sources `
  --cenhid reports\dbf\2025-12\CENHID.DBF `
  --center reports\dbf\2025-12\CENTER.DBF `
  --dacoce reports\dbf\2025-12\DACOCE.DBF `
  --comcen reports\dbf\2025-12\COMCEN.DBF `
  --period 2025-12 `
  --cenhid-catalog config\local\cenhid_units.yaml `
  --center-catalog config\local\center_units.yaml `
  --fail-on-errors
```

### Generar Formato G1 TXT

```powershell
sisgen create-g1-txt `
  --cenhid reports\dbf\2025-12\CENHID.DBF `
  --center reports\dbf\2025-12\CENTER.DBF `
  --dacoce reports\dbf\2025-12\DACOCE.DBF `
  --comcen reports\dbf\2025-12\COMCEN.DBF `
  --period 2025-12 `
  --cenhid-catalog config\local\cenhid_units.yaml `
  --center-catalog config\local\center_units.yaml
```

### Validar fuentes G2

```powershell
sisgen validate-g2-sources `
  --vepoen reports\dbf\2025-12\VEPOEN.DBF `
  --period 2025-12 `
  --catalog config\local\g2_distributors.yaml `
  --fail-on-errors
```

### Generar Formato G2 TXT

```powershell
sisgen create-g2-txt `
  --vepoen reports\dbf\2025-12\VEPOEN.DBF `
  --period 2025-12 `
  --catalog config\local\g2_distributors.yaml
```

### Validar fuentes G7

```powershell
sisgen validate-g7-sources `
  --comene reports\dbf\2025-12\COMENE.DBF `
  --venene reports\dbf\2025-12\VENENE.DBF `
  --comnet reports\dbf\2025-12\COMNET.DBF `
  --traene reports\dbf\2025-12\TRAENE.DBF `
  --valene reports\dbf\2025-12\VALENE.DBF `
  --period 2025-12 `
  --catalog config\local\g7_units.yaml `
  --fail-on-errors
```

### Generar Formato G7 TXT

```powershell
sisgen create-g7-txt `
  --comene reports\dbf\2025-12\COMENE.DBF `
  --venene reports\dbf\2025-12\VENENE.DBF `
  --comnet reports\dbf\2025-12\COMNET.DBF `
  --traene reports\dbf\2025-12\TRAENE.DBF `
  --valene reports\dbf\2025-12\VALENE.DBF `
  --period 2025-12 `
  --catalog config\local\g7_units.yaml
```

### Validar fuentes G11

```powershell
sisgen validate-g11-sources `
  --cacehi reports\dbf\2025-12\CACEHI.DBF `
  --cacete reports\dbf\2025-12\CACETE.DBF `
  --period 2025-12 `
  --catalog config\local\g11_units.yaml `
  --fail-on-errors
```

### Generar Formato G11 TXT

```powershell
sisgen create-g11-txt `
  --cacehi reports\dbf\2025-12\CACEHI.DBF `
  --cacete reports\dbf\2025-12\CACETE.DBF `
  --period 2025-12 `
  --catalog config\local\g11_units.yaml
```

## Interfaz gráfica desktop

Abrir la interfaz:

```powershell
sisgen desktop
```

La interfaz permite:

* configurar periodo mensual
* seleccionar carpeta DBF base
* seleccionar carpeta de salida
* seleccionar catálogos locales
* generar plantillas mensuales
* validar plantillas
* exportar DBF mensuales
* validar fuentes G1
* generar TXT G1
* validar fuentes G2
* generar TXT G2
* validar fuentes G7
* generar TXT G7
* validar fuentes G11
* generar TXT G11
* revisar logs del proceso

## Flujo mensual recomendado

1. Abrir la interfaz desktop.

```powershell
sisgen desktop
```

2. Configurar:

```text
Periodo: YYYY-MM
Carpeta DBF base: data/raw
Carpeta salida: reports
Catálogos locales: config/local/*.yaml
```

3. Generar plantillas mensuales.

4. Llenar manualmente los campos editables en Excel.

5. Exportar DBF mensuales.

6. Cambiar la carpeta DBF base a:

```text
reports/dbf/YYYY-MM
```

7. Validar y generar los reportes TXT requeridos.

## Catálogos locales

El proyecto usa catálogos YAML locales para controlar unidades, empresas y entidades válidas.

Ejemplos:

```text
config/local/cenhid_units.yaml
config/local/center_units.yaml
config/local/g2_distributors.yaml
config/local/g7_units.yaml
config/local/g11_units.yaml
```

Estos archivos no se versionan porque pueden contener información operativa interna.

## Archivos locales no versionados

Por seguridad y limpieza, no se suben al repositorio:

* archivos DBF reales
* catálogos locales
* reportes generados
* plantillas Excel generadas
* carpetas de salida
* entorno virtual
* cachés de Python
* builds y ejecutables generados

Ejemplos:

```text
data/raw/*.DBF
reports/
config/local/*.yaml
.venv/
__pycache__/
build/
dist/
```

## Estructura principal

```text
src/sisgen_automation/
  cacehi/    lógica de CACEHI
  cacete/    lógica de CACETE
  cenhid/    lógica de CENHID
  center/    lógica de CENTER
  comcen/    lógica de COMCEN
  comene/    lógica de COMENE
  comnet/    lógica de COMNET
  dacoce/    lógica de DACOCE
  g1/        validación y generación del Formato G1
  g2/        validación, plantillas y generación del Formato G2
  g7/        validación y generación del Formato G7
  g11/       validación y generación del Formato G11
  traene/    lógica de TRAENE
  valene/    lógica de VALENE
  venene/    lógica de VENENE
  dbf/       utilidades DBF
  cli/       comandos de consola modularizados
  ui/        interfaz desktop
```

## Validación técnica

Antes de cerrar cambios, ejecutar:

```powershell
ruff check .
python -m compileall src\sisgen_automation
git status
```

## Historial de versiones

### v1.4.0

* Modularización del CLI.
* Integración completa del Formato G7.
* Generación de plantillas G7.
* Validación de plantillas G7.
* Exportación DBF G7 desde desktop.
* Validación de fuentes G7.
* Generación TXT G7.
* Integración de Reporte G7 en desktop.

### v1.3.0

* Integración desktop del Formato G11.
* Generación de plantillas CACEHI y CACETE.
* Exportación DBF CACEHI y CACETE.
* Validación de fuentes G11.
* Generación TXT G11.

### v1.2.0

* Integración del flujo G2.
* Plantilla y exportación VEPOEN.
* Validación de fuentes G2.
* Generación TXT G2.

## Limitaciones conocidas

* El empaquetado final como ejecutable Windows todavía está pendiente.
* El formato visual final de algunos TXT puede requerir ajuste de presentación.
* Los catálogos locales deben mantenerse manualmente.
* El sistema depende de que las plantillas Excel sean llenadas correctamente antes de exportar DBF.

## Próximos pasos

* Empaquetar como ejecutable Windows.
* Mejorar el diseño visual de la interfaz desktop.
* Documentar operación mensual paso a paso para usuarios finales.
* Agregar pruebas automatizadas para workflows críticos.
* Revisar formato final de TXT con usuarios especialistas.
* Evaluar integración de nuevos formatos SISGEN.

## Licencia

Pendiente de definir.