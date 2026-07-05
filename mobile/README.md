# Mobile

Contiene la aplicacion Flutter del sistema para operadores en puertas de acceso.

## Estructura actual

- `app/`: codigo fuente Flutter de la Fase 8.

## Alcance actual

- Login con verificacion de conectividad por `GET /health`.
- Seleccion de universidad, campus y puerta.
- Flujos de entrada y salida usando:
  - `POST /parking/entry`
  - `POST /parking/exit`
- Captura de rostro y placa con camara cuando este disponible.
- Alternativa manual o simulada para placa y rostro.
- Historial basico en memoria.

## Seguridad

- No guarda tokens ni datos sensibles en texto plano.
- La sesion del operador queda en memoria.
