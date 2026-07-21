import 'package:flutter/material.dart';

import '../state/parking_app_scope.dart';
import '../widgets/ucepark_brand_header.dart';
import 'demo_iot_screen.dart';
import 'entry_mode_screen.dart';
import 'exit_mode_screen.dart';
import 'garita_face_capture_screen.dart';
import 'history_screen.dart';
import 'login_screen.dart';
import 'setup_screen.dart';

class ModeHubScreen extends StatelessWidget {
  const ModeHubScreen({super.key});

  static const routeName = '/hub';

  @override
  Widget build(BuildContext context) {
    final appState = ParkingAppScope.of(context);
    final selection = appState.selection;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Operación de puerta'),
        actions: [
          IconButton(
            onPressed: () {
              appState.logout();
              Navigator.of(context).pushNamedAndRemoveUntil(
                  LoginScreen.routeName, (route) => false);
            },
            icon: const Icon(Icons.logout),
          ),
        ],
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          const UceParkBrandHeader(
            compact: true,
            subtitle: 'Centro operativo móvil del parqueadero universitario',
          ),
          const SizedBox(height: 16),
          if (selection != null)
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Text(
                  '${selection.universityName}\n${selection.campusName} - ${selection.gateName}',
                  style: Theme.of(context).textTheme.titleMedium,
                ),
              ),
            ),
          const SizedBox(height: 24),
          FilledButton.icon(
            onPressed: () =>
                Navigator.of(context).pushNamed(EntryModeScreen.routeName),
            icon: const Icon(Icons.login),
            label: const Text('Modo entrada'),
          ),
          const SizedBox(height: 12),
          FilledButton.icon(
            onPressed: () =>
                Navigator.of(context).pushNamed(ExitModeScreen.routeName),
            icon: const Icon(Icons.logout),
            label: const Text('Modo salida'),
          ),
          const SizedBox(height: 12),
          OutlinedButton.icon(
            onPressed: () =>
                Navigator.of(context).pushNamed(HistoryScreen.routeName),
            icon: const Icon(Icons.history),
            label: const Text('Historial básico'),
          ),
          const SizedBox(height: 12),
          OutlinedButton.icon(
            onPressed: () =>
                Navigator.of(context).pushNamed(DemoIotScreen.routeName),
            icon: const Icon(Icons.hub),
            label: const Text('Demo IoT'),
          ),
          const SizedBox(height: 12),
          OutlinedButton.icon(
            onPressed: () => Navigator.of(context)
                .pushNamed(GaritaFisicaScreen.routeName),
            icon: const Icon(Icons.sensor_door),
            label: const Text('Garita fisica (MQTT)'),
          ),
          const SizedBox(height: 12),
          TextButton(
            onPressed: () =>
                Navigator.of(context).pushNamed(SetupScreen.routeName),
            child: const Text('Cambiar universidad, campus o puerta'),
          ),
        ],
      ),
    );
  }
}
