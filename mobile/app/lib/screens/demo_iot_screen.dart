import 'package:flutter/material.dart';

import '../models/app_models.dart';
import '../services/api_client.dart';
import '../theme/ucepark_theme.dart';
import '../widgets/ucepark_brand_header.dart';

class DemoIotScreen extends StatefulWidget {
  const DemoIotScreen({super.key});

  static const routeName = '/demo-iot';

  @override
  State<DemoIotScreen> createState() => _DemoIotScreenState();
}

class _DemoIotScreenState extends State<DemoIotScreen> {
  final _apiClient = ApiClient();
  bool _loading = false;
  String? _error;
  DemoGateResult? _result;

  Future<void> _openDemoGate() async {
    setState(() {
      _loading = true;
      _error = null;
    });

    try {
      final result = await _apiClient.openDemoGate();
      if (!mounted) return;
      setState(() {
        _result = result;
        _loading = false;
      });
    } catch (error) {
      if (!mounted) return;
      setState(() {
        _error = error.toString().replaceFirst('Exception: ', '');
        _loading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Demo IoT')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          const UceParkBrandHeader(
            compact: true,
            subtitle: 'Control institucional de barrera y mensajería MQTT',
          ),
          const SizedBox(height: 16),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  Text('Escenario demo',
                      style: Theme.of(context).textTheme.titleMedium),
                  const SizedBox(height: 8),
                  const Text('Universidad: uce'),
                  const Text('Campus: matriz'),
                  const Text('Puerta: norte'),
                  const Text('Placa: ABC1234'),
                  const SizedBox(height: 20),
                  FilledButton.icon(
                    onPressed: _loading ? null : _openDemoGate,
                    icon: const Icon(Icons.sensors),
                    label: _loading
                        ? const SizedBox(
                            height: 18,
                            width: 18,
                            child: CircularProgressIndicator(strokeWidth: 2),
                          )
                        : const Text('Abrir barrera demo'),
                  ),
                  if (_error != null) ...[
                    const SizedBox(height: 16),
                    Text(
                      _error!,
                      style:
                          TextStyle(color: Theme.of(context).colorScheme.error),
                    ),
                  ],
                  if (_result != null) ...[
                    const SizedBox(height: 20),
                    Container(
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(
                        color: _result!.published
                            ? UceParkColors.success.withValues(alpha: 0.08)
                            : UceParkColors.danger.withValues(alpha: 0.08),
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(
                          color: _result!.published
                              ? UceParkColors.success
                              : UceParkColors.danger,
                        ),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(_result!.status,
                              style: Theme.of(context).textTheme.titleMedium),
                          const SizedBox(height: 8),
                          Text(_result!.message),
                          const SizedBox(height: 12),
                          Text('Evento: ${_result!.demoEventId}'),
                          Text('Tópico cmd: ${_result!.topic}'),
                          Text('Tópico status: ${_result!.statusTopic}'),
                          Text(
                              'Publicado: ${_result!.published ? 'sí' : 'no'}'),
                        ],
                      ),
                    ),
                  ],
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
