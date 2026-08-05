# Correccion del solapamiento de graficos

## Causa
Los contenedores HTML de Plotly no tenian una altura explicita. Plotly calculaba un lienzo automatico mayor que la tarjeta visual y el SVG se extendia sobre la seccion Predictive Copilot.

## Correcciones aplicadas
- Altura fija y responsive para temperatura y vibracion.
- Altura fija y responsive para riesgo de falla.
- `overflow: hidden` en cada panel y contenedor Plotly.
- Aislamiento de capas con `isolation` y `z-index`.
- Layout de Plotly con altura explicita.
- Redimensionamiento controlado al cambiar el ancho de pantalla.
- Nueva version de cache para CSS y JavaScript.

## Resultado esperado
Cada grafico queda dentro de su tarjeta. La seccion Predictive Copilot empieza despues de finalizar completamente la grilla de analitica y no puede ser atravesada por el SVG o canvas de Plotly.
