import 'package:flutter/material.dart';

import '../state/parking_app_scope.dart';
import 'demo_iot_screen.dart';
import 'entry_mode_screen.dart';
import 'exit_mode_screen.dart';
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
        title: const Text('Operacion de puerta'),
        actions: [
          IconButton(
            onPressed: () {
              appState.logout();
              Navigator.of(context).pushNamedAndRemoveUntil(LoginScreen.routeName, (route) => false);
            },
            icon: const Icon(Icons.logout),
          ),
        ],
      ),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            if (selection != null)
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: Theme.of(context).colorScheme.surfaceContainerHighest,
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Text(
                  '${selection.universityName}\n${selection.campusName} - ${selection.gateName}',
                  style: Theme.of(context).textTheme.titleMedium,
                ),
              ),
            const SizedBox(height: 24),
            FilledButton.icon(
              onPressed: () => Navigator.of(context).pushNamed(EntryModeScreen.routeName),
              icon: const Icon(Icons.login),
              label: const Text('Modo entrada'),
            ),
            const SizedBox(height: 12),
            FilledButton.icon(
              onPressed: () => Navigator.of(context).pushNamed(ExitModeScreen.routeName),
              icon: const Icon(Icons.logout),
              label: const Text('Modo salida'),
            ),
            const SizedBox(height: 12),
            OutlinedButton.icon(
              onPressed: () => Navigator.of(context).pushNamed(HistoryScreen.routeName),
              icon: const Icon(Icons.history),
              label: const Text('Historial basico'),
            ),
            const SizedBox(height: 12),
            OutlinedButton.icon(
              onPressed: () => Navigator.of(context).pushNamed(DemoIotScreen.routeName),
              icon: const Icon(Icons.hub),
              label: const Text('Demo IoT'),
            ),
            const SizedBox(height: 12),
            TextButton(
              onPressed: () => Navigator.of(context).pushNamed(SetupScreen.routeName),
              child: const Text('Cambiar universidad, campus o puerta'),
            ),
          ],
        ),
      ),
    );
  }
}
