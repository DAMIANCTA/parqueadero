import 'dart:typed_data';

import 'package:flutter/material.dart';

import '../models/app_models.dart';
import '../models/history_entry.dart';
import '../services/api_client.dart';
import '../state/parking_app_scope.dart';
import '../theme/ucepark_theme.dart';
import '../widgets/uce_widgets.dart';

/// Cache en memoria de las fotos de evidencia ya descargadas, para no
/// volver a pedirlas cada vez que se reconstruye la lista (ej. al aplicar
/// un filtro). Vive mientras dure el proceso, se pierde al reiniciar la app
/// (igual que el resto de este cache no-persistente, no hace falta mas).
final Map<String, Future<Uint8List>> _evidenceImageCache = {};

class HistoryScreen extends StatefulWidget {
  const HistoryScreen({super.key});

  static const routeName = '/history';

  @override
  State<HistoryScreen> createState() => _HistoryScreenState();
}

class _HistoryScreenState extends State<HistoryScreen> {
  int _filter = 0; // 0 todos, 1 ingresos, 2 salidas, 3 denegados
  static const _filters = ['Todos', 'Ingresos', 'Salidas', 'Denegados'];

  List<HistoryEntry> _visible(List<HistoryEntry> history) {
    return switch (_filter) {
      1 =>
        history.where((e) => e.mode == ModeType.entry && e.authorized).toList(),
      2 =>
        history.where((e) => e.mode == ModeType.exit && e.authorized).toList(),
      3 => history.where((e) => !e.authorized).toList(),
      _ => history,
    };
  }

  @override
  Widget build(BuildContext context) {
    final history = ParkingAppScope.of(context).history;
    final visible = _visible(history);

    return Scaffold(
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.fromLTRB(18, 10, 18, 14),
          children: [
            const UceTopBar(),
            const SizedBox(height: 12),
            Text(
              'Historial',
              style: Theme.of(context).textTheme.headlineSmall,
            ),
            const Text(
              'Trazabilidad operativa reciente',
              style: TextStyle(fontSize: 13.5, color: UceParkColors.muted),
            ),
            const SizedBox(height: 12),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: List.generate(_filters.length, (i) {
                final active = i == _filter;
                return ChoiceChip(
                  label: Text(_filters[i]),
                  selected: active,
                  onSelected: (_) => setState(() => _filter = i),
                  showCheckmark: false,
                );
              }),
            ),
            const SizedBox(height: 14),
            if (visible.isEmpty)
              const Padding(
                padding: EdgeInsets.symmetric(vertical: 32),
                child: Text(
                  'Todavía no hay operaciones registradas.',
                  textAlign: TextAlign.center,
                  style: TextStyle(color: UceParkColors.muted),
                ),
              )
            else
              for (final entry in visible) ...[
                _HistoryCard(
                  entry: entry,
                  onTap: () => _showDetailSheet(context, entry),
                ),
                const SizedBox(height: 9),
              ],
          ],
        ),
      ),
    );
  }

  void _showDetailSheet(BuildContext context, HistoryEntry entry) {
    showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (_) => _HistoryDetailSheet(entry: entry),
    );
  }
}

class _HistoryCard extends StatelessWidget {
  const _HistoryCard({required this.entry, required this.onTap});

  final HistoryEntry entry;
  final VoidCallback onTap;

  Color get _accent => !entry.authorized
      ? UceParkColors.amber
      : (entry.mode == ModeType.entry
          ? UceParkColors.success
          : UceParkColors.blue);

  IconData get _accessIcon {
    if (!entry.authorized) return Icons.block;
    return entry.mode == ModeType.entry
        ? Icons.add_circle_outline
        : Icons.remove_circle_outline;
  }

  String get _accessLabel {
    if (!entry.authorized) return 'Denegado';
    return entry.mode == ModeType.entry ? 'Entrada' : 'Salida';
  }

  @override
  Widget build(BuildContext context) {
    final time =
        TimeOfDay.fromDateTime(entry.timestamp.toLocal()).format(context);

    return ClipRRect(
      borderRadius: BorderRadius.circular(14),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: onTap,
          child: UceCard(
            padding: const EdgeInsets.fromLTRB(10, 10, 12, 10),
            child: Row(
              children: [
                Container(
                  width: 4,
                  height: 48,
                  decoration: BoxDecoration(
                    color: _accent,
                    borderRadius: BorderRadius.circular(2),
                  ),
                ),
                const SizedBox(width: 10),
                _EvidenceThumbnail(size: 44, imageId: entry.faceImageId),
                const SizedBox(width: 11),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        entry.plateText,
                        style: const TextStyle(
                          fontSize: 13,
                          fontWeight: FontWeight.w800,
                          color: UceParkColors.navy,
                        ),
                      ),
                      Text(
                        entry.message,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: const TextStyle(
                            fontSize: 11.5, color: Color(0xFF51617C)),
                      ),
                      const SizedBox(height: 2),
                      Row(
                        children: [
                          Icon(_accessIcon, size: 13, color: _accent),
                          const SizedBox(width: 4),
                          Text(
                            'Acceso: $_accessLabel',
                            style: TextStyle(
                              fontSize: 11,
                              fontWeight: FontWeight.w800,
                              color: _accent,
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
                Column(
                  crossAxisAlignment: CrossAxisAlignment.end,
                  children: [
                    Text(
                      time,
                      style: const TextStyle(
                        fontSize: 11,
                        fontWeight: FontWeight.w700,
                        color: Color(0xFF8493A8),
                      ),
                    ),
                    const SizedBox(height: 4),
                    const Icon(Icons.chevron_right,
                        size: 18, color: Color(0xFFB6C0CF)),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

/// Miniatura de la evidencia del registro. Si el registro tiene un
/// `faceImageId` (la mayoria de los nuevos, ver garita_face_capture_screen.dart
/// / entry_mode_screen.dart / exit_mode_screen.dart) y hay sesion iniciada
/// con una cuenta real (ver LoginScreen -> ApiClient.login), se pide la foto
/// real via `/evidence/image/{id}` (requiere el permiso `evidence.read`
/// autenticado en api-gateway). Mientras carga, si no hay imageId, o si la
/// cuenta activa no tiene ese permiso, se muestra un avatar generico.
class _EvidenceThumbnail extends StatefulWidget {
  const _EvidenceThumbnail({required this.size, this.imageId});

  final double size;
  final String? imageId;

  @override
  State<_EvidenceThumbnail> createState() => _EvidenceThumbnailState();
}

class _EvidenceThumbnailState extends State<_EvidenceThumbnail> {
  final _apiClient = ApiClient();
  Future<Uint8List>? _future;

  @override
  void initState() {
    super.initState();
    _prepareFuture();
  }

  @override
  void didUpdateWidget(covariant _EvidenceThumbnail oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.imageId != widget.imageId) {
      _prepareFuture();
    }
  }

  void _prepareFuture() {
    final imageId = widget.imageId;
    if (imageId == null) {
      _future = null;
      return;
    }
    _future = _evidenceImageCache.putIfAbsent(
      imageId,
      () => _apiClient.fetchEvidenceImage(imageId),
    );
  }

  @override
  Widget build(BuildContext context) {
    final future = _future;
    if (future == null) {
      return _placeholder();
    }
    return FutureBuilder<Uint8List>(
      future: future,
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.done &&
            snapshot.hasData) {
          return ClipRRect(
            borderRadius: BorderRadius.circular(_borderRadius),
            child: Image.memory(
              snapshot.data!,
              width: widget.size,
              height: widget.size,
              fit: BoxFit.cover,
            ),
          );
        }
        return _placeholder();
      },
    );
  }

  double get _borderRadius => widget.size >= 100 ? 20 : 12;

  Widget _placeholder() {
    return Container(
      width: widget.size,
      height: widget.size,
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(_borderRadius),
        gradient: const RadialGradient(
          center: Alignment(0, -0.35),
          radius: 1,
          colors: [
            Color(0xFFC9A68A),
            Color(0xFFA8836A),
            Color(0xFF2B3550),
          ],
          stops: [0.0, 0.45, 0.62],
        ),
      ),
      child: Icon(
        Icons.person,
        color: Colors.white70,
        size: widget.size * 0.4,
      ),
    );
  }
}

class _HistoryDetailSheet extends StatelessWidget {
  const _HistoryDetailSheet({required this.entry});

  final HistoryEntry entry;

  @override
  Widget build(BuildContext context) {
    final dateTime = entry.timestamp.toLocal();
    final accessLabel = !entry.authorized
        ? 'Denegado'
        : (entry.mode == ModeType.entry ? 'Entrada' : 'Salida');
    final accessColor = !entry.authorized
        ? UceParkColors.amberDark
        : (entry.mode == ModeType.entry
            ? UceParkColors.successDark
            : UceParkColors.blue);

    return SafeArea(
      child: Padding(
        padding: const EdgeInsets.fromLTRB(18, 8, 18, 18),
        child: Container(
          padding: const EdgeInsets.fromLTRB(18, 18, 18, 18),
          decoration: const BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Center(
                child: Container(
                  width: 40,
                  height: 4,
                  margin: const EdgeInsets.only(bottom: 16),
                  decoration: BoxDecoration(
                    color: UceParkColors.line,
                    borderRadius: BorderRadius.circular(2),
                  ),
                ),
              ),
              Center(
                child: _EvidenceThumbnail(
                  size: 180,
                  imageId: entry.faceImageId,
                ),
              ),
              const SizedBox(height: 14),
              Center(
                child: Text(
                  entry.plateText,
                  style: const TextStyle(
                    fontSize: 20,
                    fontWeight: FontWeight.w800,
                    color: UceParkColors.navy,
                  ),
                ),
              ),
              const SizedBox(height: 4),
              Center(
                child: StatusBadge(
                  label: accessLabel,
                  bg: accessColor.withValues(alpha: 0.12),
                  fg: accessColor,
                ),
              ),
              const SizedBox(height: 18),
              _DetailRow(
                  icon: Icons.chat_bubble_outline,
                  label: 'Mensaje',
                  value: entry.message),
              const Divider(height: 24, color: UceParkColors.line),
              _DetailRow(
                  icon: Icons.info_outline,
                  label: 'Estado backend',
                  value: entry.status),
              if (entry.plateDetectionText != null) ...[
                const Divider(height: 24, color: UceParkColors.line),
                _DetailRow(
                  icon: Icons.camera_alt_outlined,
                  label: 'Detección de placa',
                  value: entry.plateDetectionText!.isEmpty
                      ? 'Sin lectura'
                      : '${entry.plateDetectionText} '
                          '(${((entry.plateDetectionConfidence ?? 0) * 100).toStringAsFixed(0)}%)',
                ),
              ],
              const Divider(height: 24, color: UceParkColors.line),
              _DetailRow(
                icon: Icons.schedule,
                label: 'Fecha y hora',
                value:
                    '${dateTime.day.toString().padLeft(2, '0')}/${dateTime.month.toString().padLeft(2, '0')}/${dateTime.year} · '
                    '${TimeOfDay.fromDateTime(dateTime).format(context)}',
              ),
              const SizedBox(height: 20),
              FilledButton(
                onPressed: () => Navigator.of(context).pop(),
                child: const Text('Cerrar'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _DetailRow extends StatelessWidget {
  const _DetailRow({
    required this.icon,
    required this.label,
    required this.value,
  });

  final IconData icon;
  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Icon(icon, size: 18, color: UceParkColors.navy2),
        const SizedBox(width: 12),
        SizedBox(
          width: 120,
          child: Text(
            label,
            style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600),
          ),
        ),
        Expanded(
          child: Text(
            value,
            style: const TextStyle(fontSize: 13.5, color: UceParkColors.ink),
          ),
        ),
      ],
    );
  }
}
