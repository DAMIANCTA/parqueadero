import 'dart:convert';

import 'package:shared_preferences/shared_preferences.dart';

import '../models/app_models.dart';
import '../models/history_entry.dart';

/// Wrapper tipado sobre `SharedPreferences`, para no exponer el storage
/// crudo al resto de la app. Guarda la configuracion de servidor/MQTT, la
/// sesion del operador, la seleccion de universidad/campus/puerta, y un
/// historial acotado de operaciones - todo lo que antes vivia solo en
/// memoria y se perdia en cada reinicio de la app.
class LocalStorageService {
  LocalStorageService(this._prefs);

  final SharedPreferences _prefs;

  static const _kApiBaseUrl = 'ucepark.apiBaseUrl';
  static const _kMqttHost = 'ucepark.mqttHost';
  static const _kAuthToken = 'ucepark.authToken';
  static const _kSession = 'ucepark.session';
  static const _kSelection = 'ucepark.selection';
  static const _kHistory = 'ucepark.history';
  static const _historyLimit = 30;

  static Future<LocalStorageService> create() async {
    return LocalStorageService(await SharedPreferences.getInstance());
  }

  String? readApiBaseUrl() => _prefs.getString(_kApiBaseUrl);

  Future<void> saveApiBaseUrl(String value) =>
      _prefs.setString(_kApiBaseUrl, value);

  String? readMqttHost() => _prefs.getString(_kMqttHost);

  Future<void> saveMqttHost(String value) =>
      _prefs.setString(_kMqttHost, value);

  String? readAuthToken() => _prefs.getString(_kAuthToken);

  Future<void> saveAuthToken(String value) =>
      _prefs.setString(_kAuthToken, value);

  OperatorSession? readSession() {
    final raw = _prefs.getString(_kSession);
    if (raw == null) return null;
    try {
      final json = jsonDecode(raw) as Map<String, dynamic>;
      return OperatorSession(
        username: json['username'] as String,
        displayName: json['displayName'] as String,
        loggedAt: DateTime.parse(json['loggedAt'] as String),
      );
    } catch (_) {
      return null;
    }
  }

  Future<void> saveSession(OperatorSession session) => _prefs.setString(
        _kSession,
        jsonEncode({
          'username': session.username,
          'displayName': session.displayName,
          'loggedAt': session.loggedAt.toIso8601String(),
        }),
      );

  AccessPointSelection? readSelection() {
    final raw = _prefs.getString(_kSelection);
    if (raw == null) return null;
    try {
      final json = jsonDecode(raw) as Map<String, dynamic>;
      return AccessPointSelection(
        universityId: json['universityId'] as String,
        universityName: json['universityName'] as String,
        campusId: json['campusId'] as String,
        campusName: json['campusName'] as String,
        gateId: json['gateId'] as String,
        gateName: json['gateName'] as String,
      );
    } catch (_) {
      return null;
    }
  }

  Future<void> saveSelection(AccessPointSelection selection) =>
      _prefs.setString(
        _kSelection,
        jsonEncode({
          'universityId': selection.universityId,
          'universityName': selection.universityName,
          'campusId': selection.campusId,
          'campusName': selection.campusName,
          'gateId': selection.gateId,
          'gateName': selection.gateName,
        }),
      );

  List<HistoryEntry> readHistory() {
    final raw = _prefs.getStringList(_kHistory);
    if (raw == null) return [];
    return raw
        .map((item) {
          try {
            return HistoryEntry.fromJson(
                jsonDecode(item) as Map<String, dynamic>);
          } catch (_) {
            return null;
          }
        })
        .whereType<HistoryEntry>()
        .toList();
  }

  Future<void> saveHistory(List<HistoryEntry> history) {
    final capped = history.length > _historyLimit
        ? history.sublist(history.length - _historyLimit)
        : history;
    return _prefs.setStringList(
      _kHistory,
      capped.map((item) => jsonEncode(item.toJson())).toList(),
    );
  }

  Future<void> clearAll() async {
    await _prefs.remove(_kApiBaseUrl);
    await _prefs.remove(_kMqttHost);
    await _prefs.remove(_kAuthToken);
    await _prefs.remove(_kSession);
    await _prefs.remove(_kSelection);
    await _prefs.remove(_kHistory);
  }
}
