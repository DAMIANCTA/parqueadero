import 'package:flutter/material.dart';

import '../models/app_models.dart';
import '../widgets/ucepark_brand_header.dart';
import '../state/parking_app_scope.dart';
import 'mode_hub_screen.dart';

class SetupScreen extends StatefulWidget {
  const SetupScreen({super.key});

  static const routeName = '/setup';

  @override
  State<SetupScreen> createState() => _SetupScreenState();
}

class _SetupScreenState extends State<SetupScreen> {
  String _universityId = '11111111-1111-1111-1111-111111111111';
  String _campusId = '22222222-2222-2222-2222-222222222222';
  String _gateId = '33333333-3333-3333-3333-333333333331';

  final universities = const {
    '11111111-1111-1111-1111-111111111111': 'Universidad Demo Smart Parking',
  };

  final campuses = const {
    '22222222-2222-2222-2222-222222222222': 'Campus Central',
  };

  final gates = const {
    '33333333-3333-3333-3333-333333333331': 'Puerta Norte',
    '33333333-3333-3333-3333-333333333332': 'Puerta Sur',
  };

  void _continue() {
    final selection = AccessPointSelection(
      universityId: _universityId,
      universityName: universities[_universityId]!,
      campusId: _campusId,
      campusName: campuses[_campusId]!,
      gateId: _gateId,
      gateName: gates[_gateId]!,
    );
    ParkingAppScope.of(context).setSelection(selection);
    Navigator.of(context).pushReplacementNamed(ModeHubScreen.routeName);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Selección de acceso')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          const UceParkBrandHeader(
            compact: true,
            subtitle: 'Configuración inicial de universidad, campus y puerta',
          ),
          const SizedBox(height: 16),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  Text(
                    'Configura el punto de operación',
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                  const SizedBox(height: 8),
                  Text(
                    'El dispositivo móvil quedará asociado a esta universidad, campus y garita.',
                    style: Theme.of(context).textTheme.bodyMedium,
                  ),
                  const SizedBox(height: 20),
                  DropdownButtonFormField<String>(
                    initialValue: _universityId,
                    decoration: const InputDecoration(labelText: 'Universidad'),
                    items: universities.entries
                        .map((entry) => DropdownMenuItem(
                            value: entry.key, child: Text(entry.value)))
                        .toList(),
                    onChanged: (value) =>
                        setState(() => _universityId = value!),
                  ),
                  const SizedBox(height: 16),
                  DropdownButtonFormField<String>(
                    initialValue: _campusId,
                    decoration: const InputDecoration(labelText: 'Campus'),
                    items: campuses.entries
                        .map((entry) => DropdownMenuItem(
                            value: entry.key, child: Text(entry.value)))
                        .toList(),
                    onChanged: (value) => setState(() => _campusId = value!),
                  ),
                  const SizedBox(height: 16),
                  DropdownButtonFormField<String>(
                    initialValue: _gateId,
                    decoration: const InputDecoration(labelText: 'Puerta'),
                    items: gates.entries
                        .map((entry) => DropdownMenuItem(
                            value: entry.key, child: Text(entry.value)))
                        .toList(),
                    onChanged: (value) => setState(() => _gateId = value!),
                  ),
                  const SizedBox(height: 24),
                  FilledButton(
                      onPressed: _continue, child: const Text('Continuar')),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
