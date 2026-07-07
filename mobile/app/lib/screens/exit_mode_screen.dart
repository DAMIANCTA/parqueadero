import 'dart:convert';
import 'dart:typed_data';

import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';

import '../models/app_models.dart';
import '../services/api_client.dart';
import '../state/parking_app_scope.dart';
import 'result_screen.dart';

class ExitModeScreen extends StatefulWidget {
  const ExitModeScreen({super.key});

  static const routeName = '/exit-mode';

  @override
  State<ExitModeScreen> createState() => _ExitModeScreenState();
}

class _ExitModeScreenState extends State<ExitModeScreen> {
  static const String _pendingPlatePlaceholder = 'TMP000';

  final ApiClient _apiClient = ApiClient();
  final ImagePicker _picker = ImagePicker();
  final TextEditingController _plateController = TextEditingController();
  final TextEditingController _manualPlateController = TextEditingController();
  final TextEditingController _overrideReasonController = TextEditingController();

  bool _faceValid = true;
  bool _livenessValid = true;
  double _faceConfidence = 0.95;
  bool _submitting = false;
  bool _uploadingFaceEvidence = false;
  bool _processingPlateEvidence = false;
  PaymentByPlateResult? _paymentResult;
  LocalEvidenceDraft? _faceEvidence;
  LocalEvidenceDraft? _plateEvidence;
  EvidenceUploadResult? _uploadedFaceEvidence;
  EvidenceUploadResult? _uploadedPlateEvidence;
  PlateDetectionResult? _plateDetection;

  bool get _supportsCameraCapture =>
      !kIsWeb &&
      (defaultTargetPlatform == TargetPlatform.android ||
          defaultTargetPlatform == TargetPlatform.iOS);

  bool get _isSecurityOperator => ParkingAppScope.of(context).isSecurityOperator;

  bool get _usingManualOverride {
    if (!_isSecurityOperator) {
      return false;
    }
    final manual = _normalizedManualPlate;
    return manual.isNotEmpty && manual != (_plateDetection?.plateText ?? '');
  }

  String get _normalizedManualPlate =>
      _manualPlateController.text.trim().toUpperCase().replaceAll(' ', '').replaceAll('-', '');

  bool get _hasValidDetectedPlate => _plateDetection?.autoAccepted ?? false;

  bool get _hasManualOverrideReady =>
      _usingManualOverride &&
      _normalizedManualPlate.length >= 6 &&
      _overrideReasonController.text.trim().isNotEmpty;

  bool get _canSubmitWithPlate => _hasValidDetectedPlate || _hasManualOverrideReady;

  String get _effectivePlateText {
    if (_usingManualOverride) {
      return _normalizedManualPlate;
    }
    return _plateDetection?.plateText ?? '';
  }

  double get _effectivePlateConfidence => _usingManualOverride ? 1.0 : (_plateDetection?.confidence ?? 0.0);

  @override
  void dispose() {
    _plateController.dispose();
    _manualPlateController.dispose();
    _overrideReasonController.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    final selection = ParkingAppScope.of(context).selection;
    if (selection == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Completa la seleccion de universidad, campus y puerta.')),
      );
      return;
    }
    if (!_canSubmitWithPlate) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Debes detectar una placa valida antes de validar la salida.')),
      );
      return;
    }

    setState(() => _submitting = true);
    try {
      final effectivePlate = _effectivePlateText;
      final faceEvidence = await _ensureFaceEvidenceUploaded(
        imageType: EvidenceImageType.faceExit,
        plate: effectivePlate,
      );
      final plateEvidence = _uploadedPlateEvidence;
      if (plateEvidence == null) {
        throw Exception('No hay evidencia de placa cargada.');
      }

      final session = ParkingAppScope.of(context).session;
      final result = await _apiClient.submitExit(
        universityId: selection.universityId,
        campusId: selection.campusId,
        gateId: selection.gateId,
        plateText: effectivePlate,
        faceImageId: faceEvidence.imageId,
        plateImageId: plateEvidence.imageId,
        faceMockId: _buildFaceImageId(effectivePlate),
        operatorUsername: session?.username,
        plateDetectedText: _plateDetection?.plateText,
        plateDetectionConfidence: _plateDetection?.confidence,
        plateOverrideReason: _usingManualOverride ? _overrideReasonController.text.trim() : null,
        livenessScore: _livenessValid ? 0.95 : 0.30,
        confidencePlate: _effectivePlateConfidence,
        confidenceFace: _faceValid ? _faceConfidence : 0.35,
      );
      if (!mounted) return;
      ParkingAppScope.of(context).addHistory(
        HistoryItem(
          mode: ModeType.exit,
          plateText: effectivePlate,
          result: result,
          plateDetection: _plateDetection,
        ),
      );
      Navigator.of(context).pushNamed(ResultScreen.routeName, arguments: result);
    } catch (error) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(error.toString().replaceFirst('Exception: ', ''))),
      );
    } finally {
      if (mounted) {
        setState(() => _submitting = false);
      }
    }
  }

  Future<void> _markPaid() async {
    final plate = _effectivePlateText;
    if (plate.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Primero detecta la placa para marcar pago.')),
      );
      return;
    }

    try {
      final result = await _apiClient.payByPlate(plate);
      if (!mounted) return;
      setState(() => _paymentResult = result);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(result.message)),
      );
    } catch (error) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(error.toString().replaceFirst('Exception: ', ''))),
      );
    }
  }

  Future<void> _pickEvidence({required bool isFace, required ImageSource source}) async {
    try {
      final file = await _picker.pickImage(source: source, imageQuality: 85);
      if (file == null) {
        return;
      }
      final bytes = await file.readAsBytes();
      final draft = LocalEvidenceDraft(
        label: source == ImageSource.camera ? 'Capturada' : 'Seleccionada',
        fileName: file.name,
        bytes: bytes,
        contentType: 'image/jpeg',
        isMock: false,
      );
      _setEvidenceDraft(isFace: isFace, draft: draft);
      if (!isFace) {
        await _uploadAndDetectPlate();
      }
    } catch (_) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('No se pudo obtener la imagen.')),
      );
    }
  }

  Future<void> _useMockEvidence({required bool isFace}) async {
    final draft = _buildDefaultMockEvidence(isFace: isFace);
    _setEvidenceDraft(isFace: isFace, draft: draft);
    if (!isFace) {
      await _uploadAndDetectPlate();
    }
  }

  void _setEvidenceDraft({required bool isFace, required LocalEvidenceDraft draft}) {
    setState(() {
      if (isFace) {
        _faceEvidence = draft;
        _uploadedFaceEvidence = null;
      } else {
        _plateEvidence = draft;
        _uploadedPlateEvidence = null;
        _plateDetection = null;
        _plateController.clear();
        _manualPlateController.clear();
        _overrideReasonController.clear();
      }
    });
  }

  Future<EvidenceUploadResult> _ensureFaceEvidenceUploaded({
    required EvidenceImageType imageType,
    required String plate,
  }) async {
    final existing = _uploadedFaceEvidence;
    if (existing != null && existing.plate == plate) {
      return existing;
    }

    final draft = _faceEvidence ?? _buildDefaultMockEvidence(isFace: true);
    setState(() => _uploadingFaceEvidence = true);
    try {
      final result = await _apiClient.uploadEvidence(
        imageType: imageType,
        plate: plate,
        evidence: draft,
      );
      if (mounted) {
        setState(() {
          _faceEvidence = draft;
          _uploadedFaceEvidence = result;
        });
      }
      return result;
    } finally {
      if (mounted) {
        setState(() => _uploadingFaceEvidence = false);
      }
    }
  }

  Future<void> _uploadAndDetectPlate() async {
    final selection = ParkingAppScope.of(context).selection;
    if (selection == null) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Selecciona universidad, campus y puerta antes de capturar la placa.')),
      );
      return;
    }

    final draft = _plateEvidence ?? _buildDefaultMockEvidence(isFace: false);
    setState(() => _processingPlateEvidence = true);
    try {
      final upload = await _apiClient.uploadEvidence(
        imageType: EvidenceImageType.plateExit,
        plate: _pendingPlatePlaceholder,
        evidence: draft,
      );
      final detection = await _apiClient.detectPlate(
        imageId: upload.imageId,
        universityId: selection.universityId,
        campusId: selection.campusId,
        gateId: selection.gateId,
      );
      if (!mounted) return;
      setState(() {
        _uploadedPlateEvidence = upload;
        _plateDetection = detection;
        _plateController.text = detection.plateText ?? '';
      });
      if (!detection.autoAccepted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('La deteccion de placa no tiene confianza suficiente.')),
        );
      }
    } catch (error) {
      if (!mounted) return;
      setState(() {
        _uploadedPlateEvidence = null;
        _plateDetection = null;
        _plateController.clear();
      });
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(error.toString().replaceFirst('Exception: ', ''))),
      );
    } finally {
      if (mounted) {
        setState(() => _processingPlateEvidence = false);
      }
    }
  }

  LocalEvidenceDraft _buildDefaultMockEvidence({required bool isFace}) {
    final mockPlate = isFace ? (_effectivePlateText.isEmpty ? 'VIS1234' : _effectivePlateText) : 'VIS1234';
    final slot = isFace ? 'face-exit' : 'plate-exit';
    return LocalEvidenceDraft(
      label: isFace ? 'Mock automatico rostro' : 'Mock automatico placa',
      fileName: '$slot-$mockPlate.txt',
      bytes: Uint8List.fromList(utf8.encode('mock:$slot:$mockPlate')),
      contentType: 'text/plain',
      isMock: true,
    );
  }

  String _buildFaceImageId(String plate) {
    if (!_faceValid) {
      return 'face-exit-invalid';
    }
    switch (plate) {
      case 'ABC1234':
        return 'face-student-001';
      case 'XYZ9876':
        return 'face-teacher-001';
      case 'EMP2026':
        return 'face-employee-001';
      case 'EXP2026':
        return 'face-expired-001';
      default:
        return 'face-exit-$plate';
    }
  }

  Widget _buildFaceEvidenceCard() {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        border: Border.all(color: Colors.black12),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('Evidencia de rostro', style: Theme.of(context).textTheme.titleSmall),
          const SizedBox(height: 8),
          Text(_faceEvidence == null ? 'Sin evidencia seleccionada.' : '${_faceEvidence!.label} - ${_faceEvidence!.fileName}'),
          if (_uploadedFaceEvidence != null) ...[
            const SizedBox(height: 4),
            Text('Bucket: ${_uploadedFaceEvidence!.bucket}'),
            Text('Image ID: ${_uploadedFaceEvidence!.imageId}'),
          ],
          const SizedBox(height: 12),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              OutlinedButton.icon(
                onPressed: () => _pickEvidence(isFace: true, source: ImageSource.gallery),
                icon: const Icon(Icons.photo_library_outlined),
                label: const Text('Seleccionar'),
              ),
              if (_supportsCameraCapture)
                OutlinedButton.icon(
                  onPressed: () => _pickEvidence(isFace: true, source: ImageSource.camera),
                  icon: const Icon(Icons.photo_camera_outlined),
                  label: const Text('Capturar'),
                ),
              OutlinedButton.icon(
                onPressed: () => _useMockEvidence(isFace: true),
                icon: const Icon(Icons.auto_fix_high_outlined),
                label: const Text('Usar mock'),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildPlateDetectionCard() {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        border: Border.all(color: Colors.black12),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('Captura y deteccion de placa', style: Theme.of(context).textTheme.titleSmall),
          const SizedBox(height: 8),
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: Colors.teal.withOpacity(0.05),
              borderRadius: BorderRadius.circular(8),
              border: Border.all(color: Colors.teal.withOpacity(0.35)),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Coloque la placa dentro del recuadro',
                  style: Theme.of(context).textTheme.titleSmall,
                ),
                const SizedBox(height: 8),
                AspectRatio(
                  aspectRatio: 16 / 9,
                  child: Container(
                    decoration: BoxDecoration(
                      color: Colors.black.withOpacity(0.04),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Center(
                      child: Container(
                        width: 220,
                        height: 88,
                        decoration: BoxDecoration(
                          border: Border.all(color: Colors.teal, width: 3),
                          borderRadius: BorderRadius.circular(8),
                        ),
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 12),
          Text(_plateEvidence == null ? 'Sin evidencia seleccionada.' : '${_plateEvidence!.label} - ${_plateEvidence!.fileName}'),
          if (_uploadedPlateEvidence != null) ...[
            const SizedBox(height: 4),
            Text('Image ID: ${_uploadedPlateEvidence!.imageId}'),
          ],
          const SizedBox(height: 12),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              OutlinedButton.icon(
                onPressed: _processingPlateEvidence ? null : () => _pickEvidence(isFace: false, source: ImageSource.gallery),
                icon: const Icon(Icons.photo_library_outlined),
                label: const Text('Seleccionar placa'),
              ),
              if (_supportsCameraCapture)
                FilledButton.icon(
                  onPressed: _processingPlateEvidence ? null : () => _pickEvidence(isFace: false, source: ImageSource.camera),
                  icon: const Icon(Icons.photo_camera_outlined),
                  label: const Text('Capturar placa'),
                ),
              OutlinedButton.icon(
                onPressed: _processingPlateEvidence ? null : () => _useMockEvidence(isFace: false),
                icon: const Icon(Icons.auto_fix_high_outlined),
                label: const Text('Usar mock'),
              ),
              if (_plateEvidence != null)
                OutlinedButton.icon(
                  onPressed: _processingPlateEvidence ? null : _uploadAndDetectPlate,
                  icon: const Icon(Icons.refresh),
                  label: const Text('Reintentar captura'),
                ),
            ],
          ),
          const SizedBox(height: 16),
          if (_processingPlateEvidence)
            const Row(
              children: [
                SizedBox(height: 18, width: 18, child: CircularProgressIndicator(strokeWidth: 2)),
                SizedBox(width: 12),
                Text('Detectando placa...'),
              ],
            )
          else if (_plateDetection != null) ...[
            TextField(
              controller: _plateController,
              readOnly: true,
              decoration: const InputDecoration(
                labelText: 'Placa detectada',
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 12),
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: _plateDetection!.autoAccepted ? Colors.green.withOpacity(0.08) : Colors.orange.withOpacity(0.08),
                border: Border.all(color: _plateDetection!.autoAccepted ? Colors.green : Colors.orange),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Estado: ${_plateDetection!.status}'),
                  Text('Placa detectada: ${_plateDetection!.plateText ?? 'Sin lectura valida'}'),
                  Text('Confianza: ${(_plateDetection!.confidence * 100).toStringAsFixed(0)}%'),
                  Text('Proveedor detector: ${_plateDetection!.detectorProvider}'),
                  Text('Proveedor OCR: ${_plateDetection!.ocrProvider}'),
                  if (_plateDetection!.warnings.isNotEmpty) ...[
                    const SizedBox(height: 8),
                    Text('Advertencias:', style: Theme.of(context).textTheme.titleSmall),
                    const SizedBox(height: 4),
                    ..._plateDetection!.warnings.map((warning) => Text('- $warning')),
                  ],
                  if (_plateDetection!.candidates.isNotEmpty) ...[
                    const SizedBox(height: 8),
                    Text('Candidatos:', style: Theme.of(context).textTheme.titleSmall),
                    const SizedBox(height: 4),
                    ..._plateDetection!.candidates.map(
                      (candidate) => Text(
                        '${candidate.text} - ${(candidate.confidence * 100).toStringAsFixed(0)}%',
                      ),
                    ),
                  ],
                ],
              ),
            ),
          ] else
            const Text('Captura la placa para iniciar la deteccion automatica.'),
          if (_isSecurityOperator) ...[
            const SizedBox(height: 16),
            TextField(
              controller: _manualPlateController,
              textCapitalization: TextCapitalization.characters,
              decoration: const InputDecoration(
                labelText: 'Correccion manual de placa (solo seguridad)',
                border: OutlineInputBorder(),
              ),
              onChanged: (_) => setState(() => _plateController.text = _usingManualOverride ? _normalizedManualPlate : (_plateDetection?.plateText ?? '')),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _overrideReasonController,
              decoration: const InputDecoration(
                labelText: 'Motivo de correccion',
                border: OutlineInputBorder(),
              ),
              maxLines: 2,
              onChanged: (_) => setState(() {}),
            ),
          ],
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Modo salida')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          _buildPlateDetectionCard(),
          const SizedBox(height: 12),
          OutlinedButton.icon(
            onPressed: _canSubmitWithPlate ? _markPaid : null,
            icon: const Icon(Icons.payments),
            label: const Text('Marcar pago demo'),
          ),
          const SizedBox(height: 16),
          _buildFaceEvidenceCard(),
          const SizedBox(height: 12),
          SwitchListTile(
            value: _faceValid,
            title: const Text('Simulador de rostro valido'),
            subtitle: Text(_faceValid ? 'El rostro coincidira.' : 'El rostro sera rechazado.'),
            onChanged: (value) => setState(() => _faceValid = value),
          ),
          const SizedBox(height: 12),
          SwitchListTile(
            value: _livenessValid,
            title: const Text('Simulador de liveness valido'),
            subtitle: Text(_livenessValid ? 'El liveness pasara.' : 'El liveness sera bloqueado.'),
            onChanged: (value) => setState(() => _livenessValid = value),
          ),
          if (_paymentResult != null) ...[
            const SizedBox(height: 12),
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: _paymentResult!.success ? Colors.green.withOpacity(0.10) : Colors.orange.withOpacity(0.10),
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: _paymentResult!.success ? Colors.green : Colors.orange),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(_paymentResult!.message),
                  if (_paymentResult!.session != null)
                    Text('Estado de pago: ${_paymentResult!.session!['payment_status'] ?? '-'}'),
                ],
              ),
            ),
          ],
          const SizedBox(height: 20),
          Text('Confianza rostro: ${_faceConfidence.toStringAsFixed(2)}'),
          Slider(value: _faceConfidence, onChanged: (value) => setState(() => _faceConfidence = value)),
          const SizedBox(height: 24),
          FilledButton(
            onPressed: (_submitting || !_canSubmitWithPlate || _processingPlateEvidence) ? null : _submit,
            child: _submitting
                ? const SizedBox(height: 20, width: 20, child: CircularProgressIndicator(strokeWidth: 2))
                : const Text('Validar salida'),
          ),
        ],
      ),
    );
  }
}
