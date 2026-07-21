import 'package:flutter/foundation.dart';

class AppConfig {
  static const String _definedApiBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: '',
  );

  static String? _runtimeApiBaseUrl;

  static String get defaultApiBaseUrl {
    if (_definedApiBaseUrl.isNotEmpty) {
      return _definedApiBaseUrl;
    }
    if (kIsWeb) {
      return 'http://localhost:8000';
    }

    switch (defaultTargetPlatform) {
      case TargetPlatform.android:
        return 'http://10.0.2.2:8000';
      case TargetPlatform.windows:
        return 'http://localhost:8000';
      default:
        return 'http://localhost:8000';
    }
  }

  static String get apiBaseUrl => _runtimeApiBaseUrl ?? defaultApiBaseUrl;

  static void setApiBaseUrl(String? value) {
    final normalized = value?.trim() ?? '';
    _runtimeApiBaseUrl = normalized.isEmpty ? null : normalized;
  }

  static String? _runtimeMqttHost;
  static int _runtimeMqttPort = 1883;

  static String get _apiHost => Uri.tryParse(apiBaseUrl)?.host ?? '';

  /// Por defecto reutiliza el host de [apiBaseUrl] (el broker MQTT de la
  /// garita fisica corre junto al backend), asi el operador no tiene que
  /// escribir la IP dos veces salvo que el broker viva en otra maquina.
  static String get mqttHost => _runtimeMqttHost ?? _apiHost;

  static int get mqttPort => _runtimeMqttPort;

  static bool get hasMqttHost => mqttHost.isNotEmpty;

  static void setMqttHost(String? value) {
    final normalized = value?.trim() ?? '';
    _runtimeMqttHost = normalized.isEmpty ? null : normalized;
  }

  static void setMqttPort(int value) {
    _runtimeMqttPort = value;
  }
}
