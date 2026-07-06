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
}
