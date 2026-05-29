# Desarrollo

Guía técnica ménima para trabajar en el proyecto.

## Entorno

Crear y activar entorno virtual:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Instalar el proyecto en modo editable:

```powershell
pip install -e ".[desktop,packaging]"
```

## Validación técnica

Antes de cerrar cualquier cambio:

```powershell
ruff check .
python -m compileall src\sisgen_automation
git status
```

## Flujo Git recomendado

```powershell
git status
git add <archivos>
git commit -m "Mensaje claro"
git push origin main
```

Antes de etiquetar una versión:

```powershell
ruff check .
python -m compileall src\sisgen_automation
git status
git log --oneline --decorate -5
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
  g2/        validación y generación del Formato G2
  g7/        validación y generación del Formato G7
  g8/        validación y generación del Formato G8
  g11/       validación y generación del Formato G11
  traene/    lógica de TRAENE
  valene/    lógica de VALENE
  vefame/    lógica de VEFAME
  venene/    lógica de VENENE
  dbf/       utilidades DBF
  cli/       comandos de consola modularizados
  ui/        interfaz desktop
```

## Reglas de diseño

* La lógica de negocio vive fuera de la interfaz gráfica.
* El CLI y el desktop deben reutilizar la misma lógica core.
* Las plantillas se validan antes de exportar DBF.
* Los DBF exportados se validan antes de generar TXT.
* Los datos reales y catálogos locales no se versionan.

## Archivos generados

No subir al repositorio:

```text
data/raw/*.DBF
config/local/*.yaml
reports/
dist/
dist-nuitka/
build/
.venv/
__pycache__/
```
