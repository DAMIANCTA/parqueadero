import 'dart:convert';

import 'package:http/http.dart' as http;

import '../config/app_config.dart';
import '../models/app_models.dart';

class ApiClient {
  ApiClient({http.Client? client}) : _client = client ?? http.Client();

  final http.Client _client;

  Future<bool> checkHealth() async {
    final response = await _client.get(Uri.parse('${AppConfig.apiBaseUrl}/health'));
    return response.statusCode == 200;
  }

  Future<FaceServiceConfig> getFaceConfig() async {
    final response = await _client.get(Uri.parse('${AppConfig.apiBaseUrl}/faces/config'));
    final body = jsonDecode(response.body) as Map<String, dynamic>;
    if (response.statusCode >= 400) {
      throw Exception(body['detail'] ?? 'No se pudo consultar la configuracion facial.');
    }
    return FaceServiceConfig(
      faceServiceMode: body['face_service_mode'] as String? ?? 'mock',
      faceRealProvider: body['face_real_provider'] as String? ?? 'mock',
      similarityThreshold: (body['similarity_threshold'] as num? ?? 0.82).toDouble(),
      livenessThreshold: (body['liveness_threshold'] as num? ?? 0.75).toDouble(),
      embeddingDimensions: body['embedding_dimensions'] as int? ?? 0,
      opencvAvailable: body['opencv_available'] as bool? ?? false,
      insightfaceAvailable: body['insightface_available'] as bool? ?? false,
      faceRecognitionAvailable: body['face_recognition_available'] as bool? ?? false,
      providerAvailable: body['provider_available'] as bool? ?? false,
      modelLoaded: body['model_loaded'] as bool? ?? false,
      activeProvider: body['active_provider'] as String? ?? 'unknown',
      environment: body['environment'] as String?,
      modelError: body['model_error'] as String?,
    );
  }

  Future<DemoGateResult> openDemoGate() async {
    final response = await _client.post(
      Uri.parse('${AppConfig.apiBaseUrl}/demo/open-gate'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'university_id': 'uce',
        'campus_id': 'matriz',
        'gate_id': 'norte',
        'plate': 'ABC1234',
      }),
    );

    final body = jsonDecode(response.body) as Map<String, dynamic>;
    if (response.statusCode >= 400) {
      throw Exception(body['detail'] ?? 'No se pudo abrir la barrera demo.');
    }

    return DemoGateResult(
      status: body['status'] as String? ?? 'UNKNOWN',
      message: body['message'] as String? ?? 'Sin mensaje',
      demoEventId: body['demo_event_id'] as String? ?? 'n/a',
      topic: body['topic'] as String? ?? 'n/a',
      statusTopic: body['status_topic'] as String? ?? 'n/a',
      command: body['command'] as String? ?? 'open',
      published: body['published'] as bool? ?? false,
      payload: Map<String, dynamic>.from(body['payload'] as Map? ?? const {}),
    );
  }

  Future<PaymentByPlateResult> payByPlate(String plateText) async {
    final response = await _client.post(
      Uri.parse('${AppConfig.apiBaseUrl}/payments/pay-by-plate'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'plate_text': plateText,
        'cashier_user_id': 'cashier-demo',
        'payment_method': 'cash',
      }),
    );

    final body = jsonDecode(response.body) as Map<String, dynamic>;
    if (response.statusCode >= 400) {
      throw Exception(body['detail'] ?? 'No se pudo registrar el pago.');
    }

    return PaymentByPlateResult(
      success: body['success'] as bool? ?? false,
      message: body['message'] as String? ?? 'Sin mensaje',
      auditLogId: body['audit_log_id'] as String? ?? 'n/a',
      session: body['session'] is Map<String, dynamic> ? Map<String, dynamic>.from(body['session'] as Map<String, dynamic>) : null,
    );
  }

  Future<PaymentLookupResult> checkPaymentByPlate(String plateText) async {
    final response = await _client.get(
      Uri.parse('${AppConfig.apiBaseUrl}/payments/by-plate/${Uri.encodeComponent(plateText)}'),
    );

    final body = jsonDecode(response.body) as Map<String, dynamic>;
    if (response.statusCode >= 400) {
      throw Exception(body['detail'] ?? 'No se pudo consultar el pago.');
    }

    return PaymentLookupResult(
      found: body['found'] as bool? ?? false,
      message: body['message'] as String? ?? 'Sin mensaje',
      sessionId: body['session_id'] as String? ?? 'n/a',
      plateText: body['plate_text'] as String? ?? plateText,
      entryTime: DateTime.tryParse(body['entry_time'] as String? ?? '') ?? DateTime.now(),
      exitTime: DateTime.tryParse(body['exit_time'] as String? ?? ''),
      sessionStatus: body['session_status'] as String? ?? 'UNKNOWN',
      durationMinutes: body['duration_minutes'] as int? ?? 0,
      amount: (body['amount'] as num? ?? 0).toDouble(),
      currency: body['currency'] as String? ?? 'USD',
      paymentStatus: body['payment_status'] as String? ?? 'PENDING',
      paidAt: DateTime.tryParse(body['paid_at'] as String? ?? ''),
      paidAmount: (body['paid_amount'] as num?)?.toDouble(),
      paymentMethod: body['payment_method'] as String?,
      paymentValidUntil: DateTime.tryParse(body['payment_valid_until'] as String? ?? ''),
      receiptNumber: body['receipt_number'] as String?,
      accessType: body['access_type'] as String?,
      personId: body['person_id'] as String?,
      personName: body['person_name'] as String?,
      roleType: body['role_type'] as String?,
      permitStatus: body['permit_status'] as String?,
    );
  }

  Future<EvidenceUploadResult> uploadEvidence({
    required EvidenceImageType imageType,
    required String plate,
    String? sessionId,
    required LocalEvidenceDraft evidence,
  }) async {
    final request = http.MultipartRequest(
      'POST',
      Uri.parse('${AppConfig.apiBaseUrl}/evidence/upload'),
    )
      ..fields['image_type'] = imageType.value
      ..fields['plate'] = plate
      ..files.add(
        http.MultipartFile.fromBytes(
          'file',
          evidence.bytes,
          filename: evidence.fileName,
        ),
      );

    if (sessionId != null && sessionId.isNotEmpty) {
      request.fields['session_id'] = sessionId;
    }

    final streamedResponse = await request.send();
    final response = await http.Response.fromStream(streamedResponse);
    final body = jsonDecode(response.body) as Map<String, dynamic>;
    if (response.statusCode >= 400) {
      throw Exception(body['detail'] ?? 'No se pudo cargar la evidencia.');
    }

    return EvidenceUploadResult(
      imageId: body['image_id'] as String? ?? 'n/a',
      bucket: body['bucket'] as String? ?? '-',
      objectName: body['object_name'] as String? ?? '-',
      imageType: body['image_type'] as String? ?? imageType.value,
      plate: body['plate'] as String? ?? plate,
      createdAt: DateTime.tryParse(body['created_at'] as String? ?? '') ?? DateTime.now(),
      sessionId: body['session_id'] as String?,
    );
  }

  Future<PlateDetectionResult> detectPlate({
    required String imageId,
    required String universityId,
    required String campusId,
    required String gateId,
  }) async {
    final response = await _client.post(
      Uri.parse('${AppConfig.apiBaseUrl}/plates/detect'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'image_id': imageId,
        'university_id': universityId,
        'campus_id': campusId,
        'gate_id': gateId,
      }),
    );

    final body = jsonDecode(response.body) as Map<String, dynamic>;
    if (response.statusCode >= 400) {
      throw Exception(body['detail'] ?? 'No se pudo detectar la placa.');
    }

    final rawCandidates = (body['candidates'] as List? ?? const []);
    final rawWarnings = (body['warnings'] as List? ?? const []);
    return PlateDetectionResult(
      imageId: body['image_id'] as String? ?? imageId,
      plateText: body['plate_text'] as String?,
      confidence: (body['confidence'] as num? ?? 0).toDouble(),
      boundingBox: body['bounding_box'] is Map ? Map<String, dynamic>.from(body['bounding_box'] as Map) : null,
      candidates: rawCandidates
          .whereType<Map>()
          .map(
            (item) => PlateCandidateResult(
              text: item['text'] as String? ?? '',
              confidence: (item['confidence'] as num? ?? 0).toDouble(),
            ),
          )
          .toList(),
      status: body['status'] as String? ?? 'NOT_DETECTED',
      mode: body['mode'] as String? ?? 'mock',
      validFormat: body['valid_format'] as bool? ?? false,
      source: body['source'] as String? ?? 'minio',
      detectorProvider: body['detector_provider'] as String? ?? 'unknown',
      ocrProvider: body['ocr_provider'] as String? ?? 'unknown',
      warnings: rawWarnings.map((item) => item.toString()).toList(),
      detectedAt: DateTime.now(),
    );
  }

  Future<PlateBatchDetectionResult> detectPlateBatch({
    required List<String> imageIds,
    required String universityId,
    required String campusId,
    required String gateId,
  }) async {
    final response = await _client.post(
      Uri.parse('${AppConfig.apiBaseUrl}/plates/detect-batch'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'image_ids': imageIds,
        'university_id': universityId,
        'campus_id': campusId,
        'gate_id': gateId,
      }),
    );

    final body = jsonDecode(response.body) as Map<String, dynamic>;
    if (response.statusCode >= 400) {
      throw Exception(body['detail'] ?? 'No se pudo detectar la placa por lote.');
    }

    final rawResults = body['results'] as List? ?? const [];
    final rawWarnings = body['warnings'] as List? ?? const [];
    return PlateBatchDetectionResult(
      status: body['status'] as String? ?? 'NOT_DETECTED',
      plateText: body['plate_text'] as String?,
      confidence: (body['confidence'] as num? ?? 0).toDouble(),
      results: rawResults
          .whereType<Map>()
          .map(
            (item) => PlateBatchResultItem(
              imageId: item['image_id'] as String? ?? 'n/a',
              plateText: item['plate_text'] as String?,
              confidence: (item['confidence'] as num? ?? 0).toDouble(),
              status: item['status'] as String? ?? 'NOT_DETECTED',
            ),
          )
          .toList(),
      warnings: rawWarnings.map((item) => item.toString()).toList(),
      detectedAt: DateTime.now(),
    );
  }

  Future<AuthorizationResult> submitEntry({
    required String universityId,
    required String campusId,
    required String gateId,
    required String plateText,
    required String faceImageId,
    String? plateImageId,
    String? faceMockId,
    String? operatorUsername,
    String? plateDetectedText,
    double? plateDetectionConfidence,
    String? plateOverrideReason,
    required double livenessScore,
    required PersonType personType,
    required double confidencePlate,
    required double confidenceFace,
  }) async {
    final response = await _client.post(
      Uri.parse('${AppConfig.apiBaseUrl}/parking/entry'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'university_id': universityId,
        'campus_id': campusId,
        'gate_id': gateId,
        'plate_text': plateText,
        'face_image_id': faceImageId,
        'plate_image_id': plateImageId,
        'face_mock_id': faceMockId,
        'operator_username': operatorUsername,
        'plate_detected_text': plateDetectedText,
        'plate_detection_confidence': plateDetectionConfidence,
        'plate_override_reason': plateOverrideReason,
        'liveness_score': livenessScore,
        'person_type': personType.value,
        'confidence_plate': confidencePlate,
        'confidence_face': confidenceFace,
      }),
    );
    return _parseAuthorization(response);
  }

  Future<AuthorizationResult> submitExit({
    required String universityId,
    required String campusId,
    required String gateId,
    required String plateText,
    required String faceImageId,
    String? plateImageId,
    String? faceMockId,
    String? operatorUsername,
    String? plateDetectedText,
    double? plateDetectionConfidence,
    String? plateOverrideReason,
    required double livenessScore,
    required double confidencePlate,
    required double confidenceFace,
  }) async {
    final response = await _client.post(
      Uri.parse('${AppConfig.apiBaseUrl}/parking/exit'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'university_id': universityId,
        'campus_id': campusId,
        'gate_id': gateId,
        'plate_text': plateText,
        'face_image_id': faceImageId,
        'plate_image_id': plateImageId,
        'face_mock_id': faceMockId,
        'operator_username': operatorUsername,
        'plate_detected_text': plateDetectedText,
        'plate_detection_confidence': plateDetectionConfidence,
        'plate_override_reason': plateOverrideReason,
        'liveness_score': livenessScore,
        'confidence_plate': confidencePlate,
        'confidence_face': confidenceFace,
      }),
    );
    return _parseAuthorization(response);
  }

  AuthorizationResult _parseAuthorization(http.Response response) {
    final body = jsonDecode(response.body) as Map<String, dynamic>;
    final sessionData = body['session'] as Map<String, dynamic>?;
    final gateCommand = body['gate_command'] as Map<String, dynamic>?;
    final faceValidationData = body['face_validation'] is Map<String, dynamic>
        ? body['face_validation'] as Map<String, dynamic>
        : null;
    final parsedSimilarity = (faceValidationData?['similarity'] as num?)?.toDouble();
    final parsedDistance = (faceValidationData?['distance'] as num?)?.toDouble();
    final parsedThreshold = (faceValidationData?['threshold'] as num?)?.toDouble();
    final parsedFaceMatch =
        faceValidationData?['match'] as bool? ?? faceValidationData?['face_match'] as bool?;

    return AuthorizationResult(
      authorized: body['authorized'] as bool? ?? false,
      status: body['status'] as String? ?? 'UNKNOWN',
      message: body['message'] as String? ?? 'Sin mensaje',
      accessEventId: body['access_event_id'] as String? ?? 'n/a',
      auditLogId: body['audit_log_id'] as String? ?? 'n/a',
      timestamp: DateTime.now(),
      gatePublished: gateCommand?['published'] as bool?,
      gateId: gateCommand?['gate_id'] as String?,
      incidentId: body['incident_id'] as String?,
      session: sessionData == null
          ? null
          : ResultSessionSummary(
              sessionId: sessionData['session_id'] as String,
              sessionStatus: sessionData['session_status'] as String,
              paymentStatus: sessionData['payment_status'] as String,
              plateText: sessionData['plate_text'] as String,
              personType: sessionData['person_type'] as String?,
              accessType: sessionData['access_type'] as String? ?? body['access_type'] as String?,
              personId: sessionData['person_id'] as String? ?? body['person_id'] as String?,
              personName: sessionData['person_name'] as String? ?? body['person_name'] as String?,
              roleType: sessionData['role_type'] as String? ?? body['role_type'] as String?,
              permitStatus: sessionData['permit_status'] as String? ??
                  body['permit_status'] as String? ??
                  body['member_permit_status'] as String?,
            ),
      faceValidation: faceValidationData != null
          ? FaceValidationUiResult(
              detected: faceValidationData['detected'] as bool? ?? false,
              match: parsedFaceMatch,
              similarity: parsedSimilarity,
              distance: parsedDistance,
              threshold: parsedThreshold,
              imageId: faceValidationData['image_id'] as String?,
              templateId: faceValidationData['template_id'] as String?,
              provider: faceValidationData['provider'] as String? ?? 'unknown',
              mode: faceValidationData['mode'] as String? ?? 'unknown',
              modelName: faceValidationData['model_name'] as String?,
              qualityScore: (faceValidationData['quality_score'] as num?)?.toDouble(),
              embeddingSize: faceValidationData['embedding_size'] as int? ?? 0,
              boundingBox: faceValidationData['bounding_box'] is Map
                  ? Map<String, dynamic>.from(faceValidationData['bounding_box'] as Map)
                  : null,
              warnings: (faceValidationData['warnings'] as List? ?? const []).map((item) => item.toString()).toList(),
            )
          : null,
      faceMatch: parsedFaceMatch,
      similarity: parsedSimilarity,
      distance: parsedDistance,
      threshold: parsedThreshold,
    );
  }
}
