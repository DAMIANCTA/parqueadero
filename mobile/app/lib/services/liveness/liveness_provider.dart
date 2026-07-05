import '../../models/app_models.dart';

enum LivenessEngine { mock, tensorflowLite, mediapipe, mlKit }

abstract class LivenessRuntimeAdapter {
  const LivenessRuntimeAdapter();

  LivenessEngine get engine;
  String get displayName;
  String get integrationNote;
  Future<bool> isAvailable();
}

abstract class LivenessProvider {
  const LivenessProvider();

  LivenessEngine get engine;
  String get displayName;

  Future<LivenessCheckResult> runChallenge({
    required LivenessChallenge challenge,
    required bool cameraReady,
    int frameCount = 5,
  });
}
