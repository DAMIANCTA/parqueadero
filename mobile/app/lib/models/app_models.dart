enum ModeType { entry, exit }

enum PersonType { visitor, student, teacher, employee }

enum LivenessChallenge { lookLeft, lookRight, blink }

extension PersonTypeValue on PersonType {
  String get value => switch (this) {
        PersonType.visitor => 'visitor',
        PersonType.student => 'student',
        PersonType.teacher => 'teacher',
        PersonType.employee => 'employee',
      };

  String get label => switch (this) {
        PersonType.visitor => 'Visitante',
        PersonType.student => 'Estudiante',
        PersonType.teacher => 'Docente',
        PersonType.employee => 'Trabajador',
      };
}

extension LivenessChallengeValue on LivenessChallenge {
  String get code => switch (this) {
        LivenessChallenge.lookLeft => 'look_left',
        LivenessChallenge.lookRight => 'look_right',
        LivenessChallenge.blink => 'blink',
      };

  String get label => switch (this) {
        LivenessChallenge.lookLeft => 'Mirar a la izquierda',
        LivenessChallenge.lookRight => 'Mirar a la derecha',
        LivenessChallenge.blink => 'Parpadear',
      };

  String get instruction => switch (this) {
        LivenessChallenge.lookLeft => 'Gira ligeramente el rostro hacia la izquierda.',
        LivenessChallenge.lookRight => 'Gira ligeramente el rostro hacia la derecha.',
        LivenessChallenge.blink => 'Mira la camara y parpadea una vez.',
      };
}

class OperatorSession {
  const OperatorSession({
    required this.username,
    required this.displayName,
    required this.loggedAt,
  });

  final String username;
  final String displayName;
  final DateTime loggedAt;
}

class AccessPointSelection {
  const AccessPointSelection({
    required this.universityId,
    required this.universityName,
    required this.campusId,
    required this.campusName,
    required this.gateId,
    required this.gateName,
  });

  final String universityId;
  final String universityName;
  final String campusId;
  final String campusName;
  final String gateId;
  final String gateName;
}

class ResultSessionSummary {
  const ResultSessionSummary({
    required this.sessionId,
    required this.sessionStatus,
    required this.paymentStatus,
    required this.plateText,
    this.personType,
  });

  final String sessionId;
  final String sessionStatus;
  final String paymentStatus;
  final String plateText;
  final String? personType;
}

class AuthorizationResult {
  const AuthorizationResult({
    required this.authorized,
    required this.status,
    required this.message,
    required this.accessEventId,
    required this.auditLogId,
    required this.timestamp,
    this.gatePublished,
    this.gateId,
    this.incidentId,
    this.session,
  });

  final bool authorized;
  final String status;
  final String message;
  final String accessEventId;
  final String auditLogId;
  final DateTime timestamp;
  final bool? gatePublished;
  final String? gateId;
  final String? incidentId;
  final ResultSessionSummary? session;
}

class LivenessFrame {
  const LivenessFrame({
    required this.frameId,
    required this.capturedAt,
    required this.qualityScore,
  });

  final String frameId;
  final DateTime capturedAt;
  final double qualityScore;
}

class LivenessCheckResult {
  const LivenessCheckResult({
    required this.faceImageId,
    required this.livenessScore,
    required this.challenge,
    required this.challengePassed,
    required this.providerName,
    required this.frames,
    required this.capturedAt,
    this.failureReason,
  });

  static const double minimumAcceptedScore = 0.75;

  final String faceImageId;
  final double livenessScore;
  final LivenessChallenge challenge;
  final bool challengePassed;
  final String providerName;
  final List<LivenessFrame> frames;
  final DateTime capturedAt;
  final String? failureReason;

  bool get accepted => challengePassed && livenessScore >= minimumAcceptedScore;
}

class HistoryItem {
  const HistoryItem({
    required this.mode,
    required this.plateText,
    required this.result,
  });

  final ModeType mode;
  final String plateText;
  final AuthorizationResult result;
}
