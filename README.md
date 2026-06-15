# SISGEN Format Automation

Automatización de formatos mensuales SISGEN para archivos DBF históricos, generación de plantillas Excel, exportación de DBF mensuales y generación de reportes TXT.

El proyecto reemplaza trabajo manual realizado en herramientas antiguas o emuladores. Mantiene un flujo reproducible, auditable y fácil de usar para operación mensual.

## Estado actual

Versión actual: `v1.8.0`

Funcionalidades principales:

* generación de plantillas Excel mensuales por formato
* validación de plantillas antes de exportar
* exportación de DBF mensuales por formato
* validación de fuentes SISGEN
* generación de reportes TXT por formato
* interfaz gráfica desktop simplificada
* rutas operativas configurables
* CLI modularizado por formato
* empaquetado Windows reproducible con Nuitka

## Formatos soportados

| Formato | Fuentes principales | Estado |
|---|---|---|
| G1 | CENHID, CENTER, DACOCE, COMCEN | Soportado |
| G2 | VEPOEN | Soportado |
| G7 | COMENE, VENENE, COMNET, TRAENE, VALENE | Soportado |
| G8 | VEFAME | Soportado |
| U2 | CIUGEN | Soportado |
| G11 | CACEHI, CACETE | Soportado |

## Flujo mensual resumido

```text
1. Configurar periodo, rutas operativas y catálogos.
2. Generar plantillas Excel por formato.
3. Completar campos editables.
4. Exportar DBF por formato.
5. Validar fuentes por formato.
6. Generar TXT SISGEN por formato.
```

## Rutas operativas sugeridas

```text
Carpeta DBF históricos: data/raw
Carpeta plantillas Excel: reports/templates
Carpeta DBF generados: reports/dbf/YYYY-MM
Carpeta TXT generados: reports/txt/YYYY-MM
```

Estas rutas son sugeridas. La interfaz permite cambiarlas libremente.

La carpeta DBF históricos y la carpeta DBF generados pueden ser la misma si el flujo operativo lo requiere.

## Uso rápido

Crear entorno e instalar:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[desktop]"
```

Abrir interfaz desktop:

```powershell
sisgen desktop
```

Validación técnica antes de cerrar cambios:

```powershell
ruff check .
python -m compileall src\sisgen_automation
git status
```

## Documentación

* [Guía de usuario](docs/USER_GUIDE.md)
* [Desarrollo](docs/DEVELOPMENT.md)
* [Empaquetado Windows](docs/PACKAGING_WINDOWS.md)
* [Historial de versiones](docs/RELEASE_NOTES.md)
* [Formato G1](docs/formats/G1.md)
* [Formato G2](docs/formats/G2.md)
* [Formato G7](docs/formats/G7.md)
* [Formato G8](docs/formats/G8.md)
* [Formato U2](docs/formats/U2.md)
* [Formato G11](docs/formats/G11.md)

## Catalogo G1 SQLite local

El proyecto permite usar una base SQLite local para administrar las unidades G1 usadas por CENHID y CENTER.

La base SQLite se genera desde los YAML locales con:

```powershell
sisgen catalog migrate-g1-yaml --config-dir config/local --db data/catalogs/sisgen_catalogs.db
```

La base queda en `data/catalogs/sisgen_catalogs.db`. Esta carpeta no debe subirse a Git.

### Listar unidades G1

```powershell
sisgen catalog list-g1-units --db data/catalogs/sisgen_catalogs.db
```

Filtrar por CENHID:

```powershell
sisgen catalog list-g1-units --db data/catalogs/sisgen_catalogs.db --source-format CENHID
```

Filtrar por CENTER:

```powershell
sisgen catalog list-g1-units --db data/catalogs/sisgen_catalogs.db --source-format CENTER
```

Listar solo unidades activas:

```powershell
sisgen catalog list-g1-units --db data/catalogs/sisgen_catalogs.db --active-only
```

Listar solo unidades visibles en plantilla:

```powershell
sisgen catalog list-g1-units --db data/catalogs/sisgen_catalogs.db --visible-only
```

### Administrar unidades G1

Desactivar una unidad sin eliminarla:

```powershell
sisgen catalog deactivate-g1-unit --db data/catalogs/sisgen_catalogs.db --id 1
```

Activar una unidad:

```powershell
sisgen catalog activate-g1-unit --db data/catalogs/sisgen_catalogs.db --id 1
```

Ocultar una unidad de la plantilla:

```powershell
sisgen catalog hide-g1-unit --db data/catalogs/sisgen_catalogs.db --id 1
```

Mostrar una unidad en la plantilla:

```powershell
sisgen catalog show-g1-unit --db data/catalogs/sisgen_catalogs.db --id 1
```

### Generar plantillas desde SQLite

CENHID:

```powershell
sisgen create-cenhid-template --period 2025-12 --catalog-db data/catalogs/sisgen_catalogs.db --output reports/templates/CENHID_2025_12_sqlite_template.xlsx
```

CENTER:

```powershell
sisgen create-center-template --period 2025-12 --catalog-db data/catalogs/sisgen_catalogs.db --output reports/templates/CENTER_2025_12_sqlite_template.xlsx
```

Tambien se mantiene compatibilidad con YAML usando `--catalog`.

No se debe usar `--catalog` y `--catalog-db` al mismo tiempo.

## Archivos locales no versionados

No se suben al repositorio:

* archivos DBF reales
* catálogos locales
* reportes generados
* plantillas Excel generadas
* builds y ejecutables
* entorno virtual
* cachés de Python

Ejemplos:

```text
data/raw/*.DBF
config/local/*.yaml
reports/
.venv/
__pycache__/
build/
dist/
dist-nuitka/
```

## Licencia

Pendiente de definir.