import 'app_models.dart';

/// Version liviana y serializable de un resultado de entrada/salida para el
/// historial local. A diferencia de `HistoryItem` (que guarda el
/// `AuthorizationResult` completo, pesado de serializar), solo conserva los
/// campos que `history_screen.dart` realmente muestra.
class HistoryEntry {
  const HistoryEntry({
    required this.mode,
    required this.plateText,
    required this.authorized,
    required this.message,
    required this.status,
    required this.timestamp,
    this.plateDetectionText,
    this.plateDetectionConfidence,
    this.faceImageId,
  });

  final ModeType mode;
  final String plateText;
  final bool authorized;
  final String message;
  final String status;
  final DateTime timestamp;
  final String? plateDetectionText;
  final double? plateDetectionConfidence;

  /// image_id de la foto de rostro ya subida a parking-service (via
  /// /evidence/upload), si el flujo que genero este registro llego a subir
  /// una. Se usa para pedir la miniatura real en el historial.
  final String? faceImageId;

  factory HistoryEntry.fromResult({
    required ModeType mode,
    required String plateText,
    required AuthorizationResult result,
    PlateDetectionResult? plateDetection,
    String? faceImageId,
  }) {
    return HistoryEntry(
      mode: mode,
      plateText: plateText,
      authorized: result.authorized,
      message: result.message,
      status: result.status,
      timestamp: result.timestamp,
      plateDetectionText: plateDetection?.plateText,
      plateDetectionConfidence: plateDetection?.confidence,
      faceImageId: faceImageId,
    );
  }

  Map<String, dynamic> toJson() => {
        'mode': mode.name,
        'plateText': plateText,
        'authorized': authorized,
        'message': message,
        'status': status,
        'timestamp': timestamp.toIso8601String(),
        'plateDetectionText': plateDetectionText,
        'plateDetectionConfidence': plateDetectionConfidence,
        'faceImageId': faceImageId,
      };

  static HistoryEntry? fromJson(Map<String, dynamic> json) {
    try {
      return HistoryEntry(
        mode: ModeType.values.byName(json['mode'] as String),
        plateText: json['plateText'] as String,
        authorized: json['authorized'] as bool,
        message: json['message'] as String,
        status: json['status'] as String,
        timestamp: DateTime.parse(json['timestamp'] as String),
        plateDetectionText: json['plateDetectionText'] as String?,
        plateDetectionConfidence:
            (json['plateDetectionConfidence'] as num?)?.toDouble(),
        faceImageId: json['faceImageId'] as String?,
      );
    } catch (_) {
      return null;
    }
  }
}
