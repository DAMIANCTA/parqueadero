# UCEPark Brand Guidelines

## Identidad

UCEPark es la identidad visual del sistema institucional de parqueaderos inteligentes de la Universidad Central del Ecuador. La interfaz debe comunicar control, confianza, trazabilidad y formalidad académica.

## Logo

- Logo principal: `UCEPark`
- Uso en Flutter: `mobile/app/assets/images/ucepark_logo.png`
- Uso en portal web: `web/admin-portal/assets/ucepark_logo.png`
- Recomendación:
  - usarlo en login, encabezados institucionales y vistas principales
  - respetar proporciones originales
  - no rotar ni alterar colores del logo

## Paleta oficial

```text
--navy: #15294D
--maroon: #7A1F2E
--paper: #F5F1E8
--ink: #22252B
--success: #2F7D4F
--danger: #B23B30
--biometric: #5B4B8A
--border-soft: #D8DAE0
```

## Tipografías

- Títulos:
  - `Century Schoolbook`
  - fallback: `Georgia`, serif
- Texto general:
  - `Calibri`
  - fallback: `Arial`, sans-serif

## Uso de color

- Azul marino:
  - encabezados
  - botones principales
  - navegación principal
  - títulos institucionales
- Granate:
  - acciones secundarias
  - alertas operativas suaves
  - guía visual de captura de placa
- Crema:
  - fondo general de la aplicación
- Verde:
  - autorizado
  - pago registrado
  - permiso vigente
- Rojo:
  - denegado
  - error
  - permiso vencido
- Morado biométrico:
  - validación facial
  - identidad biométrica
  - guía visual de captura de rostro

## Estados visuales

- `AUTHORIZED`, `PAID`, `VALID`:
  - fondo suave verde
  - texto y borde verde
- `REJECTED`, `DENIED`, `EXPIRED`:
  - fondo suave rojo
  - texto y borde rojo
- `PENDING`:
  - fondo suave granate
  - texto granate
- `MEMBER`, `FACE`, `BIOMETRIC`:
  - fondo suave morado
  - texto morado

## Componentes

### Botones

- Primario:
  - fondo `#15294D`
  - texto blanco
- Secundario:
  - fondo `#7A1F2E`
  - texto blanco
- Alterno outlined:
  - borde granate o azul marino según contexto

### Cards

- fondo blanco
- borde `#D8DAE0`
- radio de borde suave
- sombra ligera

### Inputs

- fondo claro
- borde suave
- foco azul marino
- texto principal en `#22252B`

### Badges

- verde para `PAID`, `VALID`, `AUTHORIZED`
- rojo para `REJECTED`, `EXPIRED`
- granate para `PENDING`
- morado para biometría o estados MEMBER

## Aplicación Flutter

- tema global:
  - `mobile/app/lib/theme/ucepark_theme.dart`
- encabezado visual reutilizable:
  - `mobile/app/lib/widgets/ucepark_brand_header.dart`
- vistas principales con branding:
  - login
  - setup
  - hub operativo
  - entrada
  - salida
  - historial
  - resultado
  - demo IoT

## Portal web

- ruta principal:
  - `web/admin-portal/`
- branding aplicado a:
  - login
  - sidebar
  - topbar
  - dashboard
  - caja/pagos
  - tablas
  - badges
  - formularios

## Cámaras

- Captura de placa:
  - guía rectangular granate
  - botón principal azul marino
- Captura de rostro:
  - guía ovalada morada
  - botón principal azul marino

## Consistencia

- No mostrar mocks ni controles de simulación en compilaciones productivas.
- Mantener una experiencia sobria e institucional.
- Evitar paletas turquesa o dashboards con estética genérica SaaS si no pertenecen a la identidad UCEPark.
