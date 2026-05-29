# Guía de usuario

Esta guía describe el flujo mensual recomendado para operar SISGEN Format Automation desde la interfaz desktop.

## 1. Abrir la aplicación

Desde el entorno de desarrollo:

```powershell
sisgen desktop
```

Desde una distribución Windows empaquetada, abrir:

```text
SISGEN-Format-Automation.exe
```

## 2. Configurar parámetros

En la pestaña de configuración, revisar:

```text
Periodo: YYYY-MM
Carpeta DBF base: data/raw
Carpeta de salida: reports
Catálogos locales: config/local/*.yaml
```

Para reportes generados desde DBF exportados, cambiar la carpeta DBF base a:

```text
reports/dbf/YYYY-MM
```

## 3. Generar plantillas

Usar la pestaña `Plantillas`.

La aplicación genera archivos Excel mensuales en:

```text
reports/templates/
```

Las celdas editables aparecen resaltadas. Las celdas protegidas no deben modificarse.

## 4. Completar plantillas

Completar manualmente los campos editables.

Regla básica:

```text
Si un valor no aplica, usar 0. No dejar celdas obligatorias vacías.
```

## 5. Exportar DBF

Usar la pestaña `Exportar DBF`.

La aplicación valida las plantillas antes de crear los DBF. Si hay errores, no exporta.

Los DBF mensuales se generan en:

```text
reports/dbf/YYYY-MM/
```

## 6. Generar reportes TXT

Después de exportar DBF:

1. Cambiar la carpeta DBF base a `reports/dbf/YYYY-MM`.
2. Ir a la pestaña del formato requerido.
3. Validar fuentes.
4. Generar TXT.

Para U2, la fuente principal es `CIUGEN.DBF` y el catálogo local es `config/local/u2_ciiu.yaml`.

Los TXT se generan en:

```text
reports/g1/
reports/g2/
reports/g7/
reports/g8/
reports/u2/
reports/g11/
```

## 7. Validaciones mínimas

Antes de usar un TXT como entregable, revisar:

* que la validación no tenga errores
* que el periodo sea correcto
* que los totales sean razonables
* que los catálogos usados sean los correctos
* que el DBF fuente sea el exportado para el periodo

## 8. Advertencia operativa

La herramienta valida estructura, catálogos, periodos y reglas internas. No reemplaza la revisión técnica de los valores de negocio.

Si una plantilla se llena con datos ficticios o mal escalados, el TXT también tendrá totales ficticios o mal escalados.