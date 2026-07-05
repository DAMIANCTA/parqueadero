import 'package:flutter/material.dart';

import '../models/app_models.dart';

class ResultScreen extends StatelessWidget {
  const ResultScreen({super.key});

  static const routeName = '/result';

  @override
  Widget build(BuildContext context) {
    final result = ModalRoute.of(context)!.settings.arguments as AuthorizationResult;

    return Scaffold(
      appBar: AppBar(title: const Text('Resultado')),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Container(
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                color: result.authorized ? Colors.green.shade50 : Colors.red.shade50,
                borderRadius: BorderRadius.circular(8),
              ),
              child: Column(
                children: [
                  Icon(
                    result.authorized ? Icons.verified : Icons.error_outline,
                    size: 48,
                    color: result.authorized ? Colors.green.shade700 : Colors.red.shade700,
                  ),
                  const SizedBox(height: 12),
                  Text(result.status, style: Theme.of(context).textTheme.headlineSmall),
                  const SizedBox(height: 8),
                  Text(result.message, textAlign: TextAlign.center),
                ],
              ),
            ),
            const SizedBox(height: 20),
            if (result.session != null) ...[
              Text('Sesion', style: Theme.of(context).textTheme.titleMedium),
              const SizedBox(height: 8),
              Text('ID: ${result.session!.sessionId}'),
              Text('Estado: ${result.session!.sessionStatus}'),
              Text('Pago: ${result.session!.paymentStatus}'),
              Text('Placa: ${result.session!.plateText}'),
              const SizedBox(height: 16),
            ],
            Text('Access event: ${result.accessEventId}'),
            Text('Audit log: ${result.auditLogId}'),
            if (result.incidentId != null) Text('Incidente: ${result.incidentId}'),
            if (result.gateId != null) Text('Puerta: ${result.gateId}'),
            const Spacer(),
            FilledButton(
              onPressed: () => Navigator.of(context).pop(),
              child: const Text('Volver'),
            ),
          ],
        ),
      ),
    );
  }
}
