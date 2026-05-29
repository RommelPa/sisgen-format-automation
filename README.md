# SISGEN Format Automation

Automatización de formatos mensuales SISGEN para archivos DBF históricos, generación de plantillas Excel, exportación de DBF mensuales y generación de reportes TXT.

El proyecto reemplaza trabajo manual realizado en herramientas antiguas o emuladores. Mantiene un flujo reproducible, auditable y fácil de usar para operación mensual.

## Estado actual

Versión actual: `v1.7.0`

Funcionalidades principales:

* generación de plantillas Excel mensuales
* validación de plantillas antes de exportar
* exportación de DBF mensuales
* validación de fuentes SISGEN
* generación de reportes TXT
* interfaz gráfica desktop
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
1. Configurar periodo, carpeta DBF base, carpeta de salida y catálogos.
2. Generar plantillas Excel.
3. Completar campos editables.
4. Validar plantillas.
5. Exportar DBF mensuales.
6. Cambiar carpeta DBF base a reports/dbf/YYYY-MM.
7. Validar fuentes.
8. Generar TXT SISGEN.
```

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