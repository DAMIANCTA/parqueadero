import 'package:flutter/material.dart';

import 'app.dart';
import 'config/app_config.dart';
import 'services/local_storage_service.dart';
import 'state/parking_app_state.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  final storage = await LocalStorageService.create();

  final restoredApiBaseUrl = storage.readApiBaseUrl();
  if (restoredApiBaseUrl != null) {
    AppConfig.setApiBaseUrl(restoredApiBaseUrl);
  }
  final restoredMqttHost = storage.readMqttHost();
  if (restoredMqttHost != null) {
    AppConfig.setMqttHost(restoredMqttHost);
  }
  final restoredAuthToken = storage.readAuthToken();
  if (restoredAuthToken != null) {
    AppConfig.setAuthToken(restoredAuthToken);
  }

  runApp(SmartParkingApp(appState: ParkingAppState(storage)));
}
