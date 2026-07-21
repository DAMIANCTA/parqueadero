import 'package:flutter/material.dart';

import '../models/app_models.dart';
import '../widgets/uce_widgets.dart';

class ResultScreen extends StatelessWidget {
  const ResultScreen({super.key});

  static const routeName = '/result';

  @override
  Widget build(BuildContext context) {
    final result =
        ModalRoute.of(context)!.settings.arguments as AuthorizationResult;
    final session = result.session;
    final isMember = session?.isMember ?? false;
    final face = result.faceValidation;

    return Scaffold(
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.fromLTRB(18, 10, 18, 14),
          children: [
            const UceTopBar(showBack: true),
            const SizedBox(height: 14),
            UceHero(
              authorized: result.authorized,
              title: result.authorized ? 'Acceso Permitido' : 'Acceso Denegado',
              description:
                  _headlineDescription(result: result, isMember: isMember),
              detailChip: _localizedMessage(result.message),
            ),
            const SizedBox(height: 10),
            UceCard(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Estado backend',
                      style: Theme.of(context).textTheme.titleSmall),
                  const SizedBox(height: 4),
                  Text(result.status),
                ],
              ),
            ),
            const SizedBox(height: 16),
            if (session != null) ...[
              _SectionCard(
                title: 'Sesión',
                children: [
                  _infoRow('ID', session.sessionId),
                  _infoRow('Placa', session.plateText),
                  _infoRow('Estado', session.sessionStatus),
                  _infoRow('Acceso',
                      session.accessType ?? (isMember ? 'MEMBER' : 'VISITOR')),
                  _infoRow('Pago', session.paymentStatus),
                  if (isMember) ...[
                    _infoRow('Nombre', session.personName ?? '-'),
                    _infoRow('Rol', session.roleLabel),
                    _infoRow('Permiso', _permitLabel(session.permitStatus)),
                  ],
                ],
              ),
              const SizedBox(height: 16),
            ],
            if (face != null) ...[
              _SectionCard(
                title: 'Validación facial',
                children: [
                  _infoRow('Rostro detectado', face.detected ? 'Sí' : 'No'),
                  _infoRow('Face', face.matchLabel),
                  if (face.similarity != null)
                    _infoRow('Similarity',
                        '${(face.similarity! * 100).toStringAsFixed(1)}%'),
                  if (face.distance != null)
                    _infoRow('Distance', face.distance!.toStringAsFixed(4)),
                  if (face.threshold != null)
                    _infoRow('Threshold', face.thresholdValueLabel),
                  _infoRow('Proveedor', face.provider),
                  if ((face.modelName ?? '').isNotEmpty)
                    _infoRow('Modelo', face.modelName!),
                  if (face.qualityScore != null)
                    _infoRow('Calidad',
                        '${(face.qualityScore! * 100).toStringAsFixed(1)}%'),
                  if (face.embeddingSize > 0)
                    _infoRow('Embedding', '${face.embeddingSize} dimensiones'),
                  if (face.boundingBox != null)
                    _infoRow('Bounding box', face.boundingBox.toString()),
                  if (face.warnings.isNotEmpty)
                    _infoRow('Advertencias', face.warnings.join(', ')),
                ],
              ),
              const SizedBox(height: 16),
            ],
            _SectionCard(
              title: 'Trazabilidad',
              children: [
                _infoRow('Access event', result.accessEventId),
                _infoRow('Audit log', result.auditLogId),
                if (result.incidentId != null)
                  _infoRow('Incidente', result.incidentId!),
                if (result.gateId != null) _infoRow('Puerta', result.gateId!),
              ],
            ),
            const SizedBox(height: 24),
            FilledButton(
              onPressed: () => Navigator.of(context).pop(),
              child: const Text('Volver'),
            ),
          ],
        ),
      ),
    );
  }

  static String _headlineDescription({
    required AuthorizationResult result,
    required bool isMember,
  }) {
    if (isMember) {
      return result.authorized
          ? 'Vehicle member access authorized'
          : 'Vehicle member access rejected';
    }
    return result.authorized
        ? 'Vehicle entry/exit authorized'
        : 'Vehicle entry/exit rejected';
  }

  static String _localizedMessage(String message) {
    final normalized = message.trim().toLowerCase();
    if (normalized.contains('face verification failed')) {
      return 'Face verification failed. El rostro no coincide con el registro esperado.';
    }
    if (normalized == 'monthly permit expired' ||
        normalized == 'permission is not valid') {
      return 'Permiso mensual vencido.';
    }
    return message;
  }

  static String _permitLabel(String? permitStatus) {
    switch ((permitStatus ?? '').toUpperCase()) {
      case 'VALID':
        return 'Vigente';
      case 'EXPIRED':
        return 'Vencido';
      case '':
        return '-';
      default:
        return permitStatus!;
    }
  }

  static Widget _infoRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 120,
            child: Text(
              '$label:',
              style: const TextStyle(fontWeight: FontWeight.w600),
            ),
          ),
          Expanded(child: Text(value)),
        ],
      ),
    );
  }
}

class _SectionCard extends StatelessWidget {
  const _SectionCard({
    required this.title,
    required this.children,
  });

  final String title;
  final List<Widget> children;

  @override
  Widget build(BuildContext context) {
    return UceCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(title, style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: 12),
          ...children,
        ],
      ),
    );
  }
}
