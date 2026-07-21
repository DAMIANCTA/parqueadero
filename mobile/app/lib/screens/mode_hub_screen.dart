import 'package:flutter/material.dart';

import '../state/parking_app_scope.dart';
import '../theme/ucepark_theme.dart';
import '../widgets/uce_widgets.dart';
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
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.fromLTRB(18, 10, 18, 14),
          children: [
            UceTopBar(
              trailing: IconButton(
                onPressed: () async {
                  await appState.logout();
                  if (!context.mounted) return;
                  Navigator.of(context).pushNamedAndRemoveUntil(
                      LoginScreen.routeName, (route) => false);
                },
                icon: const Icon(Icons.logout, color: UceParkColors.navy),
              ),
            ),
            const SizedBox(height: 14),
            Text(
              'Operación de puerta',
              style: Theme.of(context).textTheme.headlineSmall,
            ),
            const Text(
              'Centro operativo móvil del parqueadero universitario',
              style: TextStyle(fontSize: 13.5, color: UceParkColors.muted),
            ),
            const SizedBox(height: 16),
            if (selection != null)
              UceCard(
                child: Text(
                  '${selection.universityName}\n${selection.campusName} - ${selection.gateName}',
                  style: Theme.of(context).textTheme.titleMedium,
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
              onPressed: () =>
                  Navigator.of(context).pushNamed(GaritaFisicaScreen.routeName),
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
      ),
    );
  }
}
