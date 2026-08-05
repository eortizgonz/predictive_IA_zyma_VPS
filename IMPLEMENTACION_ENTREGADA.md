# Implementación entregada

## Módulos incorporados

1. **Predictive Copilot backend** (`services/copilot_service.py`)
   - Interpretación controlada de preguntas.
   - Respuestas diferenciadas para Operaciones, Finanzas y Tecnología.
   - Impacto operacional y financiero.
   - Simulación de aplazamiento.
   - Explicación aproximada de factores.

2. **ChromaDB / recuperación documental** (`services/rag_service.py`)
   - Persistencia local en `data/chroma`.
   - Indexación de manuales.
   - Búsqueda semántica y filtros.
   - Embeddings locales sin descargar modelos.
   - Respaldo funcional local si ChromaDB aún no está instalado.

3. **Persistencia** (`services/database_service.py`)
   - Conversaciones.
   - Mensajes.
   - Órdenes de trabajo en borrador.
   - Eventos de auditoría.

4. **Nuevas APIs**
   - `POST /api/copilot/chat`
   - `POST /api/work-orders/preview`
   - `GET /api/knowledge/search`
   - `GET /api/health`

5. **Frontend conversacional**
   - Respuestas estructuradas.
   - Tarjetas operacionales y financieras.
   - Factores de predicción.
   - Fuentes documentales.
   - Botones para explicar, comparar y preparar orden.

6. **Despliegue**
   - `Dockerfile`.
   - `docker-compose.yml`.
   - `start.bat`.
   - `start.sh`.
   - `.env.example`.

## Validaciones realizadas

- Compilación de archivos Python.
- Validación sintáctica de JavaScript.
- Prueba de salud de la API.
- Consulta de máquinas.
- Pregunta financiera al Copilot.
- Creación de borrador de orden.
- Consulta de conocimiento técnico.

## Alcance actual

Es una versión demostrativa funcional. Los datos de máquinas, producción y costos siguen siendo simulados. Para producción se requiere integración con fuentes reales, autenticación, permisos, PostgreSQL/TimescaleDB y validación formal del modelo.

## Actualización: botón Diagnóstico IA

El botón **Diagnóstico IA** ahora combina de forma explícita dos fuentes:

1. El bloque exacto del manual técnico correspondiente a la máquina y al rango de riesgo actual.
2. La información del modelo predictivo: algoritmo, probabilidad, clasificación, variables utilizadas, umbrales e importancia global de variables.

La interfaz separa ambas fuentes para evitar confundir una recomendación documental con el resultado calculado por el modelo. La extracción del manual es determinista por `machine_id` y rango de riesgo; la búsqueda semántica se utiliza únicamente como respaldo.
