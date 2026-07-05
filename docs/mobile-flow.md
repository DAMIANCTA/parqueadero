# Flujo Mobile de Entrada y Salida

## Objetivo

Definir la operacion esperada desde la app movil usada en puertas de acceso para registrar ingreso y salida de vehiculos.

## Flujo de entrada para visitantes

1. El operador selecciona la universidad, campus y puerta.
2. La app captura la placa del vehiculo.
3. La app captura el rostro del conductor.
4. La app envia imagenes y metadatos al backend.
5. `plate_recognition_service` devuelve una placa mock.
6. `liveness_service` devuelve validacion mock.
7. `parking_session_service` crea una sesion temporal de parqueo.
8. `media_service` registra referencias de imagen.
9. `iot_service` publica la orden de apertura si la validacion es correcta.

## Flujo de salida para visitantes

1. La app captura nuevamente placa y rostro.
2. El backend ubica la sesion abierta del visitante.
3. Se compara la placa de salida con la placa registrada al entrar.
4. Se compara el rostro de salida con la referencia generada al entrar.
5. `payment_service` valida que la sesion este pagada.
6. Si todo coincide, el backend autoriza salida.
7. `iot_service` publica la orden de apertura.

## Flujo de caja para visitantes

1. La secretaria busca la sesion por placa o por QR.
2. `payment_service` calcula el monto usando hora de entrada y tarifa vigente.
3. La secretaria registra el pago con metodo de pago y usuario cajero.
4. El sistema cambia `payment_status` a `PAID`.
5. Se registra auditoria para trazabilidad del cobro.

## Flujo de entrada y salida para estudiantes, docentes y trabajadores

1. La app captura placa y rostro.
2. `identity_service` valida que la placa exista.
3. El backend valida que el rostro corresponda a una persona autorizada para esa placa.
4. Se revisa vigencia del permiso.
5. Se registra el evento de entrada o salida.
6. Si la validacion es correcta, se abre la barrera.

## Consideraciones de UX mobile

- Operacion en pocos pasos.
- Respuesta visual inmediata: autorizado, rechazado o pendiente.
- Soporte para capturas repetidas cuando la imagen tenga mala calidad.
- Preparado para futuras colas offline y reintentos.
- Trazabilidad de quien opero la puerta y en que dispositivo.
