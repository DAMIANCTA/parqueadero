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

  Future<AuthorizationResult> submitEntry({
    required String universityId,
    required String campusId,
    required String gateId,
    required String plateText,
    required String faceImageId,
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
            ),
    );
  }
}
