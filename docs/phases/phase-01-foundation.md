# Fase 01 - Foundation

## Entregables

- Monorepo base.
- Microservicios FastAPI con endpoints mock minimos.
- Documentacion inicial.
- Contratos API base.
- Docker Compose local.
- Variables de entorno de referencia.

## Criterio de exito

La fase se considera exitosa cuando un equipo puede clonar el proyecto, copiar `.env.example` a `.env`, ejecutar `docker compose up --build` y obtener:

- Servicios HTTP respondiendo `/health`.
- Infraestructura local disponible.
- Contratos y arquitectura documentados.

## Fuera de alcance

- Persistencia productiva.
- Seguridad enterprise.
- Modelos de IA reales.
- App Flutter funcional.

## Siguiente fase recomendada

Implementar el dominio base de universidades, campus, puertas, personas, vehiculos y sesiones con PostgreSQL real y migraciones.
