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

En la pestaña `Configuración`, revisar:

```text
Periodo: YYYY-MM
Carpeta DBF históricos: data/raw
Carpeta plantillas Excel: reports/templates
Carpeta DBF generados: reports/dbf/YYYY-MM
Carpeta TXT generados: reports/txt/YYYY-MM
Catálogos locales: config/local/*.yaml
```

Las rutas anteriores son sugeridas. La interfaz permite cambiarlas libremente.

La carpeta DBF históricos y la carpeta DBF generados pueden ser la misma si el flujo operativo lo requiere.

La herramienta no sube ni versiona DBF reales, plantillas generadas ni TXT generados.

## 3. Preparar DBF

Usar la pestaña `Preparar DBF`.

Esta pestaña concentra dos pasos:

```text
1. Generar plantillas Excel.
2. Exportar DBF mensuales.
```

Ambas acciones se ejecutan por formato:

```text
G1
G2
G7
G8
U2
G11
```

También existen botones para ejecutar todos los formatos, pero se recomienda usarlos solo cuando todos los insumos estén disponibles.

## 4. Generar plantillas

En `Preparar DBF`, usar el grupo `1. Generar plantillas Excel`.

La aplicación genera archivos Excel en la carpeta configurada como:

```text
Carpeta plantillas Excel
```

Las celdas editables aparecen resaltadas. Las celdas protegidas no deben modificarse.

## 5. Completar plantillas

Completar manualmente los campos editables.

Regla básica:

```text
Si un valor no aplica, usar 0. No dejar celdas obligatorias vacías.
```

## 6. Exportar DBF

En `Preparar DBF`, usar el grupo `2. Exportar DBF`.

La aplicación valida las plantillas antes de crear los DBF. Si hay errores en el formato seleccionado, no exporta ese formato.

Los DBF mensuales se generan directamente en la carpeta configurada como:

```text
Carpeta DBF generados
```

## 7. Generar reportes TXT

Después de exportar DBF:

1. Ir a la pestaña `Generar TXT`.
2. Validar fuentes del formato requerido.
3. Generar TXT del formato requerido.

La validación lee los DBF desde:

```text
Carpeta DBF generados
```

Los TXT se generan directamente en:

```text
Carpeta TXT generados
```

Para U2, la fuente principal es `CIUGEN.DBF` y el catálogo local es `config/local/u2_ciiu.yaml`.

## 8. Validaciones mínimas

Antes de usar un TXT como entregable, revisar:

* que la validación no tenga errores
* que el periodo sea correcto
* que los totales sean razonables
* que los catálogos usados sean los correctos
* que el DBF fuente sea el exportado para el periodo

## 9. Advertencia operativa

La herramienta valida estructura, catálogos, periodos y reglas internas. No reemplaza la revisión técnica de los valores de negocio.

Si una plantilla se llena con datos ficticios o mal escalados, el TXT también tendrá totales ficticios o mal escalados.