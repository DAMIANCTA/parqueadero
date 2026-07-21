import 'dart:math';

import '../../models/app_models.dart';
import 'liveness_provider.dart';

class MockLivenessProvider extends LivenessProvider {
  MockLivenessProvider({Random? random}) : _random = random ?? Random();

  final Random _random;

  @override
  LivenessEngine get engine => LivenessEngine.mock;

  @override
  String get displayName => 'MockLivenessProvider';

  @override
  Future<LivenessCheckResult> runChallenge({
    required LivenessChallenge challenge,
    required bool cameraReady,
    int frameCount = 5,
  }) async {
    await Future<void>.delayed(const Duration(milliseconds: 1200));

    final successProbability = cameraReady ? 0.82 : 0.68;
    final challengePassed = _random.nextDouble() <= successProbability;
    final livenessScore = challengePassed
        ? 0.78 + (_random.nextDouble() * 0.20)
        : 0.34 + (_random.nextDouble() * 0.30);
    final capturedAt = DateTime.now();
    final frames = List<LivenessFrame>.generate(
      frameCount,
      (index) => LivenessFrame(
        frameId: 'frame-${capturedAt.millisecondsSinceEpoch}-$index',
        capturedAt: capturedAt.add(Duration(milliseconds: index * 180)),
        qualityScore: 0.72 + (_random.nextDouble() * 0.26),
      ),
    );

    return LivenessCheckResult(
      faceImageId: 'face-${capturedAt.millisecondsSinceEpoch}',
      livenessScore: livenessScore.clamp(0.0, 1.0).toDouble(),
      challenge: challenge,
      challengePassed: challengePassed,
      providerName: displayName,
      frames: frames,
      capturedAt: capturedAt,
      failureReason: challengePassed ? null : _buildFailureReason(challenge),
    );
  }

  String _buildFailureReason(LivenessChallenge challenge) {
    return switch (challenge) {
      LivenessChallenge.lookLeft =>
        'No se detecto el giro esperado hacia la izquierda.',
      LivenessChallenge.lookRight =>
        'No se detecto el giro esperado hacia la derecha.',
      LivenessChallenge.blink =>
        'No se detecto un parpadeo valido durante la captura.',
    };
  }
}
