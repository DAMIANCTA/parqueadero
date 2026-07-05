import 'dart:math';

import '../../models/app_models.dart';
import 'liveness_provider.dart';
import 'liveness_runtime_adapters.dart';
import 'mock_liveness_provider.dart';

class LivenessService {
  LivenessService({
    LivenessProvider? provider,
    Random? random,
  })  : _provider = provider ?? MockLivenessProvider(),
        _random = random ?? Random();

  final LivenessProvider _provider;
  final Random _random;

  static const int defaultFrameCount = 5;

  static const List<LivenessRuntimeAdapter> plannedRuntimes = [
    TensorFlowLiteRuntimeAdapter(),
    MediaPipeRuntimeAdapter(),
    MlKitRuntimeAdapter(),
  ];

  String get activeProviderName => _provider.displayName;

  LivenessChallenge nextChallenge() {
    final challenges = LivenessChallenge.values;
    return challenges[_random.nextInt(challenges.length)];
  }

  Future<LivenessCheckResult> performCheck({
    required LivenessChallenge challenge,
    required bool cameraReady,
    int frameCount = defaultFrameCount,
  }) {
    return _provider.runChallenge(
      challenge: challenge,
      cameraReady: cameraReady,
      frameCount: frameCount,
    );
  }
}
