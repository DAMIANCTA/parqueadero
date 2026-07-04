# Diagrama de Contexto

```mermaid
flowchart LR
    Mobile["App movil Flutter"] --> Gateway["API Gateway"]
    Gateway --> Auth["Auth Service"]
    Gateway --> Identity["Identity Service"]
    Gateway --> Sessions["Parking Session Service"]
    Gateway --> Payments["Payment Service"]
    Gateway --> Face["Facial Recognition Service (mock)"]
    Gateway --> Plate["Plate Recognition Service (mock)"]
    Gateway --> Liveness["Liveness Service (mock)"]
    Gateway --> Media["Media Service"]
    Gateway --> IoT["IoT Service"]

    Identity --> CoreDB["PostgreSQL Core"]
    Sessions --> CoreDB
    Payments --> CoreDB

    Face --> BioDB["PostgreSQL Biometrics + pgvector"]
    Face --> MinIO["MinIO"]
    Plate --> MinIO
    Media --> MinIO

    IoT --> MQTT["Mosquitto MQTT"]
    MQTT --> NodeRED["Node-RED"]
    NodeRED --> Barrier["ESP32 / Barrera (futuro)"]
```

## Nota

En esta fase el gateway existe como servicio base con catalogo y salud. La orquestacion real entre servicios se implementara despues, cuando empecemos los flujos de entrada y salida end-to-end.
