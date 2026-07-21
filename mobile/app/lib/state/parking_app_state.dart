import 'dart:async';

import 'package:flutter/foundation.dart';

import '../config/app_config.dart';
import '../models/app_models.dart';
import '../models/history_entry.dart';
import '../services/local_storage_service.dart';

class ParkingAppState extends ChangeNotifier {
  ParkingAppState(this._storage) {
    _session = _storage.readSession();
    _selection = _storage.readSelection();
    _history.addAll(_storage.readHistory());
  }

  final LocalStorageService _storage;

  OperatorSession? _session;
  AccessPointSelection? _selection;
  final List<HistoryEntry> _history = [];

  OperatorSession? get session => _session;
  AccessPointSelection? get selection => _selection;
  List<HistoryEntry> get history => List.unmodifiable(_history.reversed);

  bool get isLoggedIn => _session != null;
  bool get isSecurityOperator => _session?.isSecurityOperator ?? false;

  void login({required String username, required String displayName}) {
    _session = OperatorSession(
      username: username,
      displayName: displayName,
      loggedAt: DateTime.now(),
    );
    unawaited(_storage.saveSession(_session!));
    notifyListeners();
  }

  /// Persiste la URL base del API validada (llamado desde LoginScreen tras
  /// un checkHealth exitoso), para no pedirla de nuevo en el siguiente
  /// arranque.
  void persistApiBaseUrl(String value) {
    unawaited(_storage.saveApiBaseUrl(value));
  }

  /// Persiste el token JWT obtenido de /auth/login, para no tener que
  /// autenticar de nuevo en el siguiente arranque.
  void persistAuthToken(String value) {
    AppConfig.setAuthToken(value);
    unawaited(_storage.saveAuthToken(value));
  }

  Future<void> logout() async {
    _session = null;
    _selection = null;
    _history.clear();
    await _storage.clearAll();
    AppConfig.setApiBaseUrl(null);
    AppConfig.setMqttHost(null);
    AppConfig.setAuthToken(null);
    notifyListeners();
  }

  void setSelection(AccessPointSelection selection) {
    _selection = selection;
    unawaited(_storage.saveSelection(selection));
    notifyListeners();
  }

  void addHistory(HistoryEntry item) {
    _history.add(item);
    unawaited(_storage.saveHistory(_history));
    notifyListeners();
  }
}
