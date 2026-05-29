# Empaquetado Windows

El proyecto usa Nuitka para generar una carpeta ejecutable standalone en Windows.

## Instalar dependencias

```powershell
pip install -e ".[desktop,packaging]"
```

## Construir ejecutable

```powershell
.\scripts\build_windows_nuitka.ps1
```

El ejecutable se genera en:

```text
dist-nuitka/run_desktop.dist/SISGEN-Format-Automation.exe
```

## Crear ZIP de distribuci?n

```powershell
Compress-Archive `
  -Path dist-nuitka\run_desktop.dist\* `
  -DestinationPath ..\SISGEN-Format-Automation-v1.6.0-windows.zip `
  -Force
```

## Regla importante

No copiar solo el `.exe`.

La carpeta completa `run_desktop.dist` es el entregable, porque contiene dependencias, DLL y plugins Qt.

## Distribuci?n interna

Para uso operativo interno, el ZIP puede incluir carpetas como:

```text
SISGEN-Format-Automation/
  SISGEN-Format-Automation.exe
  _internal/
  data/
    raw/
  config/
    local/
  reports/
```

Los archivos reales de `data/raw` y `config/local` no se versionan en GitHub. Solo deben incluirse en paquetes internos autorizados o copiarse manualmente en la instalación local.

## Catálogos requeridos

```text
config/local/cenhid_units.yaml
config/local/center_units.yaml
config/local/g2_distributors.yaml
config/local/g7_units.yaml
config/local/g8_clients.yaml
config/local/g11_units.yaml
```

## Validación del ejecutable

Después de construir:

1. Abrir `SISGEN-Format-Automation.exe`.
2. Verificar que la interfaz cargue.
3. Probar generación de plantillas.
4. Probar validación.
5. Probar exportación DBF.
6. Probar generación TXT.

## Nota sobre antivirus corporativo

Si una herramienta de seguridad bloquea un ejecutable generado, no se debe forzar una excepción sin autorización.

Alternativas:

* usar build con Nuitka
* distribuir carpeta completa
* revisar firma de código
* coordinar validación con TI
