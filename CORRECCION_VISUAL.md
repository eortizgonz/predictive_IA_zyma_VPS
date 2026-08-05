# Corrección visual validada

Esta versión corrige el problema en el que la aplicación aparecía como HTML sin formato.

## Correcciones

- Hoja de estilos renombrada y versionada para evitar caché antigua.
- Rutas estáticas absolutas basadas en la carpeta del proyecto.
- Ruta de plantillas absoluta.
- Scripts de inicio posicionan automáticamente la terminal en la carpeta correcta.
- Se conservaron el dashboard, activos, gráficos, Diagnóstico IA, manuales, modelo predictivo, Copilot, ChromaDB, impacto financiero y órdenes de trabajo.

## Iniciar en Windows

1. Extraer todo el ZIP.
2. Ejecutar `start.bat`.
3. Abrir `http://127.0.0.1:8000`.
4. Si había una versión anterior abierta, presionar `Ctrl + F5` una vez.

No abrir directamente `templates/dashboard.html`, porque la aplicación necesita FastAPI para servir estilos, JavaScript y datos.
