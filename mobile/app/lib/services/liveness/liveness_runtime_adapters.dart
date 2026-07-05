import 'liveness_provider.dart';

class TensorFlowLiteRuntimeAdapter extends LivenessRuntimeAdapter {
  const TensorFlowLiteRuntimeAdapter();

  @override
  LivenessEngine get engine => LivenessEngine.tensorflowLite;

  @override
  String get displayName => 'TensorFlow Lite';

  @override
  String get integrationNote =>
      'Preparado para ejecutar inferencia local con un modelo anti-spoofing y analisis por frames.';

  @override
  Future<bool> isAvailable() async => false;
}

class MediaPipeRuntimeAdapter extends LivenessRuntimeAdapter {
  const MediaPipeRuntimeAdapter();

  @override
  LivenessEngine get engine => LivenessEngine.mediapipe;

  @override
  String get displayName => 'MediaPipe';

  @override
  String get integrationNote =>
      'Preparado para landmarks faciales, orientacion de cabeza y validaciones de reto guiado.';

  @override
  Future<bool> isAvailable() async => false;
}

class MlKitRuntimeAdapter extends LivenessRuntimeAdapter {
  const MlKitRuntimeAdapter();

  @override
  LivenessEngine get engine => LivenessEngine.mlKit;

  @override
  String get displayName => 'ML Kit';

  @override
  String get integrationNote =>
      'Preparado para deteccion facial en dispositivo y enriquecimiento de señales de liveness.';

  @override
  Future<bool> isAvailable() async => false;
}
