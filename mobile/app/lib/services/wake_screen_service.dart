import 'package:flutter/services.dart';

/// Puente al codigo nativo de Android (ver MainActivity.kt) que prende la
/// pantalla ya mismo, incluso si estaba apagada por inactividad. Se usa
/// apenas llega un evento de presencia MQTT en la garita fisica, para que
/// el guardia/conductor vea la captura sin tener que tocar el telefono.
/// En otras plataformas (iOS/desktop/web) es un no-op silencioso: no hay
/// implementacion nativa registrada para este canal.
class WakeScreenService {
  static const _channel = MethodChannel('ucepark/wake_screen');

  static Future<void> wakeScreenNow() async {
    try {
      await _channel.invokeMethod('wakeScreen');
    } catch (_) {
      // Sin implementacion nativa en esta plataforma: se ignora.
    }
  }
}
