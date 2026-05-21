# SISGEN Format Automation

Automatización de formatos mensuales SISGEN para generación de archivos DBF y reportes de auditoría.

## Objetivo

Reducir el trabajo manual asociado a la actualización mensual de formatos SISGEN, manteniendo compatibilidad con archivos DBF históricos y generando reportes de revisión.

## Alcance inicial

La primera versión trabaja con el formato:

- `CENHID`: Generación mensual de centrales hidráulicas.

## Principios del proyecto

- No modificar archivos DBF originales directamente.
- Generar siempre una salida nueva.
- Validar estructura antes de exportar.
- No subir datos reales a GitHub.
- Usar datos demo para documentación pública.

## Flujo esperado

1. Leer DBF histórico.
2. Identificar estructura.
3. Crear plantilla mensual.
4. Validar datos nuevos.
5. Generar DBF actualizado.
6. Emitir reportes de auditoría.

## Estado

Proyecto en configuración inicial.