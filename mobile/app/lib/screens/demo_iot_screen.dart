import 'package:flutter/material.dart';

import '../models/app_models.dart';
import '../services/api_client.dart';

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
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Theme.of(context).colorScheme.surfaceContainerHighest,
                borderRadius: BorderRadius.circular(8),
              ),
              child: const Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Escenario demo', style: TextStyle(fontWeight: FontWeight.w700)),
                  SizedBox(height: 8),
                  Text('Universidad: uce'),
                  Text('Campus: matriz'),
                  Text('Puerta: norte'),
                  Text('Placa: ABC1234'),
                ],
              ),
            ),
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
                style: TextStyle(color: Theme.of(context).colorScheme.error),
              ),
            ],
            if (_result != null) ...[
              const SizedBox(height: 20),
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: _result!.published ? Colors.green.shade50 : Colors.red.shade50,
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(_result!.status, style: Theme.of(context).textTheme.titleMedium),
                    const SizedBox(height: 8),
                    Text(_result!.message),
                    const SizedBox(height: 12),
                    Text('Evento: ${_result!.demoEventId}'),
                    Text('Topico cmd: ${_result!.topic}'),
                    Text('Topico status: ${_result!.statusTopic}'),
                    Text('Publicado: ${_result!.published ? 'si' : 'no'}'),
                  ],
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
