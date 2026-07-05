# Flujo Mobile de Entrada y Salida

## Objetivo

Definir la operacion esperada desde la app movil usada en puertas de acceso para registrar ingreso y salida de vehiculos.

## Flujo de entrada para visitantes

1. El operador selecciona la universidad, campus y puerta.
2. La app captura la placa del vehiculo.
3. La app activa la camara frontal para captura facial.
4. La app genera un reto aleatorio de liveness: mirar a la izquierda, mirar a la derecha o parpadear.
5. La capa mock de liveness captura varios frames simulados, calcula `liveness_score` y bloquea el flujo si el score es bajo.
6. Si el reto es aprobado, la app envia `face_image_id`, `liveness_score` e imagenes/metadatos al backend.
7. `plate_recognition_service` devuelve una placa mock.
8. `parking_session_service` crea una sesion temporal de parqueo.
9. `media_service` registra referencias de imagen.
10. `iot_service` publica la orden de apertura si la validacion es correcta.

## Flujo de salida para visitantes

1. La app captura nuevamente placa y rostro.
2. Antes de enviar la solicitud, ejecuta el reto de liveness en camara frontal.
3. Si el score no supera el umbral minimo, la app exige nueva captura y no envia la salida.
4. El backend ubica la sesion abierta del visitante.
5. Se compara la placa de salida con la placa registrada al entrar.
6. Se compara el rostro de salida con la referencia generada al entrar.
7. `payment_service` valida que la sesion este pagada.
8. Si todo coincide, el backend autoriza salida.
9. `iot_service` publica la orden de apertura.

## Flujo de caja para visitantes

1. La secretaria busca la sesion por placa o por QR.
2. `payment_service` calcula el monto usando hora de entrada y tarifa vigente.
3. La secretaria registra el pago con metodo de pago y usuario cajero.
4. El sistema cambia `payment_status` a `PAID`.
5. Se registra auditoria para trazabilidad del cobro.

## Flujo de entrada y salida para estudiantes, docentes y trabajadores

1. La app captura placa y rostro.
2. La app ejecuta liveness antes de permitir el envio de la operacion.
3. `identity_service` valida que la placa exista.
4. El backend valida que el rostro corresponda a una persona autorizada para esa placa.
5. Se revisa vigencia del permiso.
6. Se registra el evento de entrada o salida.
7. Si la validacion es correcta, se abre la barrera.

## Modulo de liveness en app movil

1. La pantalla de rostro intenta usar la camara frontal del dispositivo.
2. Se selecciona un reto aleatorio por cada intento.
3. La capa actual usa `MockLivenessProvider` para simular la captura de varios frames y producir `liveness_score`.
4. Si el resultado es menor a `0.75`, la app bloquea el envio hacia `POST /parking/entry` o `POST /parking/exit`.
5. Si el resultado es valido, se conserva `face_image_id` y `liveness_score` para adjuntarlos al backend.
6. La interfaz de liveness ya separa proveedor, runtime y resultado para integrar despues TensorFlow Lite, MediaPipe o ML Kit sin cambiar pantallas ni contratos de API.

## Integracion futura de modelo real

- TensorFlow Lite: para anti-spoofing offline y clasificacion en dispositivo.
- MediaPipe: para landmarks, orientacion de cabeza y validacion del reto.
- ML Kit: para deteccion facial rapida y señales complementarias de presencia real.
- La app ya deja un contrato `LivenessProvider` y adaptadores de runtime preparados para reemplazar el mock por un motor real.

## Consideraciones de UX mobile

- Operacion en pocos pasos.
- Respuesta visual inmediata: autorizado, rechazado o pendiente.
- Soporte para capturas repetidas cuando la imagen tenga mala calidad.
- Preparado para futuras colas offline y reintentos.
- Trazabilidad de quien opero la puerta y en que dispositivo.
