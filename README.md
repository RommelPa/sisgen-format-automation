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