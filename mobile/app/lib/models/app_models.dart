import 'dart:typed_data';

enum ModeType { entry, exit }

enum PersonType { visitor, student, teacher, employee }

enum LivenessChallenge { lookLeft, lookRight, blink }

enum EvidenceImageType { faceEntry, faceExit, plateEntry, plateExit }

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

extension EvidenceImageTypeValue on EvidenceImageType {
  String get value => switch (this) {
        EvidenceImageType.faceEntry => 'face_entry',
        EvidenceImageType.faceExit => 'face_exit',
        EvidenceImageType.plateEntry => 'plate_entry',
        EvidenceImageType.plateExit => 'plate_exit',
      };

  String get label => switch (this) {
        EvidenceImageType.faceEntry => 'Rostro entrada',
        EvidenceImageType.faceExit => 'Rostro salida',
        EvidenceImageType.plateEntry => 'Placa entrada',
        EvidenceImageType.plateExit => 'Placa salida',
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

  bool get isSecurityOperator => username.toLowerCase().contains('security');
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

class DemoGateResult {
  const DemoGateResult({
    required this.status,
    required this.message,
    required this.demoEventId,
    required this.topic,
    required this.statusTopic,
    required this.command,
    required this.published,
    required this.payload,
  });

  final String status;
  final String message;
  final String demoEventId;
  final String topic;
  final String statusTopic;
  final String command;
  final bool published;
  final Map<String, dynamic> payload;
}

class PaymentByPlateResult {
  const PaymentByPlateResult({
    required this.success,
    required this.message,
    required this.auditLogId,
    this.session,
  });

  final bool success;
  final String message;
  final String auditLogId;
  final Map<String, dynamic>? session;
}

class LocalEvidenceDraft {
  const LocalEvidenceDraft({
    required this.label,
    required this.fileName,
    required this.bytes,
    required this.contentType,
    required this.isMock,
  });

  final String label;
  final String fileName;
  final Uint8List bytes;
  final String contentType;
  final bool isMock;
}

class EvidenceUploadResult {
  const EvidenceUploadResult({
    required this.imageId,
    required this.bucket,
    required this.objectName,
    required this.imageType,
    required this.plate,
    required this.createdAt,
    this.sessionId,
  });

  final String imageId;
  final String bucket;
  final String objectName;
  final String imageType;
  final String plate;
  final DateTime createdAt;
  final String? sessionId;
}

class PlateCandidateResult {
  const PlateCandidateResult({
    required this.text,
    required this.confidence,
  });

  final String text;
  final double confidence;
}

class PlateDetectionResult {
  const PlateDetectionResult({
    required this.imageId,
    required this.plateText,
    required this.confidence,
    required this.boundingBox,
    required this.candidates,
    required this.status,
    required this.mode,
    required this.validFormat,
    required this.source,
    required this.detectorProvider,
    required this.ocrProvider,
    required this.warnings,
    required this.detectedAt,
  });

  static const double minimumAutoAcceptance = 0.75;

  final String imageId;
  final String? plateText;
  final double confidence;
  final Map<String, dynamic>? boundingBox;
  final List<PlateCandidateResult> candidates;
  final String status;
  final String mode;
  final bool validFormat;
  final String source;
  final String detectorProvider;
  final String ocrProvider;
  final List<String> warnings;
  final DateTime detectedAt;

  bool get detected => status == 'DETECTED' && (plateText?.isNotEmpty ?? false);
  bool get autoAccepted => detected && confidence >= minimumAutoAcceptance;
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
    this.plateDetection,
  });

  final ModeType mode;
  final String plateText;
  final AuthorizationResult result;
  final PlateDetectionResult? plateDetection;
}
