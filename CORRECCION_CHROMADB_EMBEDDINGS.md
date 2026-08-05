# Corrección de compatibilidad ChromaDB

Se corrigió el error:

`LocalHashEmbeddingFunction object has no attribute embed_query`

## Cambios aplicados

- Se agregaron los métodos `embed_query` y `embed_documents` a la función local de embeddings.
- Se mantienen compatibilidad con el protocolo anterior mediante `__call__`.
- La aplicación ahora envía embeddings explícitos a ChromaDB al indexar y consultar.
- Se agregó una búsqueda local de respaldo sobre el manual técnico si ChromaDB presenta un error de compatibilidad.
- El Copilot ya no se interrumpe si el motor vectorial no puede ejecutar una consulta.

## Validaciones

- Compilación de `rag_service.py`.
- Prueba de embeddings para texto individual y listas.
- Consulta del endpoint `/api/health`.
- Consulta completa de `/api/copilot/chat` con fuentes técnicas.
