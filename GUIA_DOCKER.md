# Ejecución con Docker

## Construir y ejecutar

```bash
docker compose up --build
```

Abrir en navegador:

```text
http://127.0.0.1:8000
```

## Detener

```bash
docker compose down
```

## Archivos agregados en la raíz del proyecto

- `Dockerfile`
- `docker-compose.yml`

El servicio expone el puerto `8000` y monta las carpetas `data` y `knowledge_base` dentro del contenedor.
