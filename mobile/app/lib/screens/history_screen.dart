import 'package:flutter/material.dart';

import '../models/app_models.dart';
import '../state/parking_app_scope.dart';
import '../theme/ucepark_theme.dart';
import '../widgets/ucepark_brand_header.dart';

class HistoryScreen extends StatelessWidget {
  const HistoryScreen({super.key});

  static const routeName = '/history';

  @override
  Widget build(BuildContext context) {
    final history = ParkingAppScope.of(context).history;

    return Scaffold(
      appBar: AppBar(title: const Text('Historial básico')),
      body: history.isEmpty
          ? const Center(child: Text('Todavía no hay operaciones registradas.'))
          : ListView.separated(
              padding: const EdgeInsets.all(16),
              itemCount: history.length,
              separatorBuilder: (_, __) => const SizedBox(height: 12),
              itemBuilder: (context, index) {
                final item = history[index];
                final color = item.result.authorized
                    ? UceParkColors.success
                    : UceParkColors.danger;
                return Card(
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        if (index == 0) ...[
                          const UceParkBrandHeader(
                            compact: true,
                            subtitle: 'Trazabilidad operativa reciente',
                          ),
                          const SizedBox(height: 16),
                        ],
                        Text(
                          '${item.mode == ModeType.entry ? 'Entrada' : 'Salida'} - ${item.plateText}',
                          style: Theme.of(context).textTheme.titleMedium,
                        ),
                        const SizedBox(height: 6),
                        Container(
                          padding: const EdgeInsets.symmetric(
                              horizontal: 10, vertical: 6),
                          decoration: BoxDecoration(
                            color: color.withValues(alpha: 0.1),
                            borderRadius: BorderRadius.circular(999),
                          ),
                          child: Text(
                            item.result.authorized ? 'Autorizado' : 'Denegado',
                            style: Theme.of(context)
                                .textTheme
                                .labelMedium
                                ?.copyWith(color: color),
                          ),
                        ),
                        const SizedBox(height: 8),
                        Text(item.result.message),
                        const SizedBox(height: 6),
                        Text('Estado: ${item.result.status}'),
                        if (item.plateDetection != null)
                          Text(
                            'Detección placa: ${((item.plateDetection!.plateText ?? '').isEmpty) ? 'sin lectura' : (item.plateDetection!.plateText ?? 'sin lectura')} '
                            '(${(item.plateDetection!.confidence * 100).toStringAsFixed(0)}%)',
                          ),
                        Text('Hora: ${item.result.timestamp.toLocal()}'),
                      ],
                    ),
                  ),
                );
              },
            ),
    );
  }
}
