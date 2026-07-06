import 'package:flutter/material.dart';

import '../models/app_models.dart';
import '../state/parking_app_scope.dart';

class HistoryScreen extends StatelessWidget {
  const HistoryScreen({super.key});

  static const routeName = '/history';

  @override
  Widget build(BuildContext context) {
    final history = ParkingAppScope.of(context).history;

    return Scaffold(
      appBar: AppBar(title: const Text('Historial basico')),
      body: history.isEmpty
          ? const Center(child: Text('Todavia no hay operaciones registradas.'))
          : ListView.separated(
              padding: const EdgeInsets.all(16),
              itemCount: history.length,
              separatorBuilder: (_, __) => const SizedBox(height: 12),
              itemBuilder: (context, index) {
                final item = history[index];
                final color = item.result.authorized ? Colors.green : Colors.red;
                return Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    border: Border.all(color: color.withOpacity(0.35)),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        '${item.mode == ModeType.entry ? 'Entrada' : 'Salida'} - ${item.plateText}',
                        style: Theme.of(context).textTheme.titleMedium,
                      ),
                      const SizedBox(height: 6),
                      Text(item.result.message),
                      const SizedBox(height: 6),
                      Text('Estado: ${item.result.status}'),
                      if (item.plateDetection != null)
                        Text(
                          'Deteccion placa: ${item.plateDetection!.plateText.isEmpty ? 'sin lectura' : item.plateDetection!.plateText} '
                          '(${(item.plateDetection!.confidence * 100).toStringAsFixed(0)}%)',
                        ),
                      Text('Hora: ${item.result.timestamp.toLocal()}'),
                    ],
                  ),
                );
              },
            ),
    );
  }
}
