import 'package:flutter/material.dart';

import '../models/app_models.dart';
import '../services/api_client.dart';
import '../state/parking_app_scope.dart';
import 'capture_face_screen.dart';
import 'capture_plate_screen.dart';
import 'result_screen.dart';

class EntryModeScreen extends StatefulWidget {
  const EntryModeScreen({super.key});

  static const routeName = '/entry-mode';

  @override
  State<EntryModeScreen> createState() => _EntryModeScreenState();
}

class _EntryModeScreenState extends State<EntryModeScreen> {
  final ApiClient _apiClient = ApiClient();
  final TextEditingController _plateController = TextEditingController();
  PersonType _personType = PersonType.visitor;
  double _livenessScore = 0.90;
  double _plateConfidence = 0.95;
  double _faceConfidence = 0.96;
  String? _faceImageId;
  bool _submitting = false;

  @override
  void dispose() {
    _plateController.dispose();
    super.dispose();
  }

  Future<void> _captureFace() async {
    final result = await Navigator.of(context).push<String>(
      MaterialPageRoute(builder: (_) => const CaptureFaceScreen()),
    );
    if (result == null || !mounted) return;
    setState(() => _faceImageId = result);
  }

  Future<void> _capturePlate() async {
    final result = await Navigator.of(context).push<String>(
      MaterialPageRoute(builder: (_) => const CapturePlateScreen()),
    );
    if (result == null || !mounted) return;
    setState(() => _plateController.text = result);
  }

  Future<void> _submit() async {
    final selection = ParkingAppScope.of(context).selection;
    if (selection == null || _faceImageId == null || _plateController.text.trim().isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Completa la seleccion, rostro y placa.')),
      );
      return;
    }

    setState(() => _submitting = true);
    try {
      final result = await _apiClient.submitEntry(
        universityId: selection.universityId,
        campusId: selection.campusId,
        gateId: selection.gateId,
        plateText: _plateController.text.trim(),
        faceImageId: _faceImageId!,
        livenessScore: _livenessScore,
        personType: _personType,
        confidencePlate: _plateConfidence,
        confidenceFace: _faceConfidence,
      );
      if (!mounted) return;
      ParkingAppScope.of(context).addHistory(
        HistoryItem(mode: ModeType.entry, plateText: _plateController.text.trim().toUpperCase(), result: result),
      );
      Navigator.of(context).pushNamed(ResultScreen.routeName, arguments: result);
    } catch (_) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('No se pudo enviar la solicitud de entrada.')),
      );
    } finally {
      if (mounted) {
        setState(() => _submitting = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Modo entrada')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          DropdownButtonFormField<PersonType>(
            value: _personType,
            decoration: const InputDecoration(labelText: 'Tipo de persona', border: OutlineInputBorder()),
            items: PersonType.values
                .map((type) => DropdownMenuItem(value: type, child: Text(type.label)))
                .toList(),
            onChanged: (value) => setState(() => _personType = value ?? PersonType.visitor),
          ),
          const SizedBox(height: 16),
          TextField(
            controller: _plateController,
            textCapitalization: TextCapitalization.characters,
            decoration: const InputDecoration(labelText: 'Placa', border: OutlineInputBorder()),
          ),
          const SizedBox(height: 12),
          OutlinedButton.icon(
            onPressed: _capturePlate,
            icon: const Icon(Icons.directions_car),
            label: const Text('Captura de placa'),
          ),
          const SizedBox(height: 12),
          OutlinedButton.icon(
            onPressed: _captureFace,
            icon: const Icon(Icons.face),
            label: Text(_faceImageId == null ? 'Captura de rostro' : 'Rostro listo'),
          ),
          const SizedBox(height: 20),
          Text('Liveness: ${_livenessScore.toStringAsFixed(2)}'),
          Slider(value: _livenessScore, onChanged: (value) => setState(() => _livenessScore = value)),
          Text('Confianza placa: ${_plateConfidence.toStringAsFixed(2)}'),
          Slider(value: _plateConfidence, onChanged: (value) => setState(() => _plateConfidence = value)),
          Text('Confianza rostro: ${_faceConfidence.toStringAsFixed(2)}'),
          Slider(value: _faceConfidence, onChanged: (value) => setState(() => _faceConfidence = value)),
          const SizedBox(height: 24),
          FilledButton(
            onPressed: _submitting ? null : _submit,
            child: _submitting
                ? const SizedBox(height: 20, width: 20, child: CircularProgressIndicator(strokeWidth: 2))
                : const Text('Enviar entrada'),
          ),
        ],
      ),
    );
  }
}
