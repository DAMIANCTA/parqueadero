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
  final ApiClient _apiClient = ApiClient();
  final ImagePicker _picker = ImagePicker();
  final TextEditingController _plateController = TextEditingController();
  bool _faceValid = true;
  bool _livenessValid = true;
  double _plateConfidence = 0.95;
  double _faceConfidence = 0.95;
  bool _submitting = false;
  PaymentByPlateResult? _paymentResult;
  LocalEvidenceDraft? _faceEvidence;
  LocalEvidenceDraft? _plateEvidence;
  EvidenceUploadResult? _uploadedFaceEvidence;
  EvidenceUploadResult? _uploadedPlateEvidence;

  bool get _supportsCameraCapture =>
      !kIsWeb &&
      (defaultTargetPlatform == TargetPlatform.android ||
          defaultTargetPlatform == TargetPlatform.iOS);

  @override
  void dispose() {
    _plateController.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    final selection = ParkingAppScope.of(context).selection;
    if (selection == null || _plateController.text.trim().isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Completa la seleccion y la placa.')),
      );
      return;
    }

    setState(() => _submitting = true);
    try {
      final normalizedPlate = _plateController.text.trim().toUpperCase();
      final faceEvidence = await _ensureEvidenceUploaded(
        isFace: true,
        imageType: EvidenceImageType.faceExit,
        plate: normalizedPlate,
      );
      final plateEvidence = await _ensureEvidenceUploaded(
        isFace: false,
        imageType: EvidenceImageType.plateExit,
        plate: normalizedPlate,
      );
      final result = await _apiClient.submitExit(
        universityId: selection.universityId,
        campusId: selection.campusId,
        gateId: selection.gateId,
        plateText: normalizedPlate,
        faceImageId: _buildFaceImageId(normalizedPlate),
        faceEvidenceId: faceEvidence.imageId,
        plateEvidenceId: plateEvidence.imageId,
        livenessScore: _livenessValid ? 0.95 : 0.30,
        confidencePlate: _plateConfidence,
        confidenceFace: _faceValid ? _faceConfidence : 0.35,
      );
      if (!mounted) return;
      ParkingAppScope.of(context).addHistory(
        HistoryItem(mode: ModeType.exit, plateText: normalizedPlate, result: result),
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
    final plate = _plateController.text.trim().toUpperCase();
    if (plate.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Ingresa primero una placa para marcar pago.')),
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
      _setEvidenceDraft(
        isFace: isFace,
        draft: LocalEvidenceDraft(
          label: source == ImageSource.camera ? 'Capturada' : 'Seleccionada',
          fileName: file.name,
          bytes: bytes,
          contentType: 'image/jpeg',
          isMock: false,
        ),
      );
    } catch (_) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('No se pudo obtener la imagen.')),
      );
    }
  }

  void _useMockEvidence({required bool isFace}) {
    final normalizedPlate = _plateController.text.trim().toUpperCase();
    final slot = isFace ? 'face-exit' : 'plate-exit';
    final bytes = Uint8List.fromList(
      utf8.encode(
        'mock:$slot:${normalizedPlate.isEmpty ? 'NO_PLATE' : normalizedPlate}:${DateTime.now().toIso8601String()}',
      ),
    );
    _setEvidenceDraft(
      isFace: isFace,
      draft: LocalEvidenceDraft(
        label: 'Mock generado',
        fileName: '$slot-${normalizedPlate.isEmpty ? 'pending' : normalizedPlate}.txt',
        bytes: bytes,
        contentType: 'text/plain',
        isMock: true,
      ),
    );
  }

  void _setEvidenceDraft({required bool isFace, required LocalEvidenceDraft draft}) {
    setState(() {
      if (isFace) {
        _faceEvidence = draft;
        _uploadedFaceEvidence = null;
      } else {
        _plateEvidence = draft;
        _uploadedPlateEvidence = null;
      }
    });
  }

  Future<EvidenceUploadResult> _ensureEvidenceUploaded({
    required bool isFace,
    required EvidenceImageType imageType,
    required String plate,
  }) async {
    final existing = isFace ? _uploadedFaceEvidence : _uploadedPlateEvidence;
    if (existing != null && existing.plate == plate) {
      return existing;
    }

    final draft = isFace
        ? (_faceEvidence ?? _buildDefaultMockEvidence(isFace: true, plate: plate))
        : (_plateEvidence ?? _buildDefaultMockEvidence(isFace: false, plate: plate));
    final result = await _apiClient.uploadEvidence(
      imageType: imageType,
      plate: plate,
      evidence: draft,
    );
    if (mounted) {
      setState(() {
        if (isFace) {
          _faceEvidence = draft;
          _uploadedFaceEvidence = result;
        } else {
          _plateEvidence = draft;
          _uploadedPlateEvidence = result;
        }
      });
    }
    return result;
  }

  LocalEvidenceDraft _buildDefaultMockEvidence({required bool isFace, required String plate}) {
    final slot = isFace ? 'face-exit' : 'plate-exit';
    return LocalEvidenceDraft(
      label: 'Mock automatico',
      fileName: '$slot-$plate.txt',
      bytes: Uint8List.fromList(utf8.encode('mock:$slot:$plate')),
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

  Widget _buildEvidenceCard({
    required String title,
    required LocalEvidenceDraft? draft,
    required EvidenceUploadResult? uploaded,
    required VoidCallback onUseMock,
    required VoidCallback onPickGallery,
    VoidCallback? onCapture,
  }) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        border: Border.all(color: Colors.black12),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(title, style: Theme.of(context).textTheme.titleSmall),
          const SizedBox(height: 8),
          Text(draft == null ? 'Sin evidencia seleccionada.' : '${draft.label} - ${draft.fileName}'),
          if (uploaded != null) ...[
            const SizedBox(height: 4),
            Text('Bucket: ${uploaded.bucket}'),
            Text('Image ID: ${uploaded.imageId}'),
          ],
          const SizedBox(height: 12),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              OutlinedButton.icon(
                onPressed: onPickGallery,
                icon: const Icon(Icons.photo_library_outlined),
                label: const Text('Seleccionar'),
              ),
              if (onCapture != null)
                OutlinedButton.icon(
                  onPressed: onCapture,
                  icon: const Icon(Icons.photo_camera_outlined),
                  label: const Text('Capturar'),
                ),
              OutlinedButton.icon(
                onPressed: onUseMock,
                icon: const Icon(Icons.auto_fix_high_outlined),
                label: const Text('Usar mock'),
              ),
            ],
          ),
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
          TextField(
            controller: _plateController,
            textCapitalization: TextCapitalization.characters,
            decoration: const InputDecoration(
              labelText: 'Placa',
              helperText: 'Ejemplo visitante: VIS1001 | Registradas: ABC1234, XYZ9876, EMP2026, EXP2026',
              border: OutlineInputBorder(),
            ),
          ),
          const SizedBox(height: 12),
          OutlinedButton.icon(
            onPressed: _markPaid,
            icon: const Icon(Icons.payments),
            label: const Text('Marcar pago demo'),
          ),
          const SizedBox(height: 16),
          _buildEvidenceCard(
            title: 'Evidencia de rostro',
            draft: _faceEvidence,
            uploaded: _uploadedFaceEvidence,
            onUseMock: () => _useMockEvidence(isFace: true),
            onPickGallery: () => _pickEvidence(isFace: true, source: ImageSource.gallery),
            onCapture: _supportsCameraCapture ? () => _pickEvidence(isFace: true, source: ImageSource.camera) : null,
          ),
          const SizedBox(height: 12),
          _buildEvidenceCard(
            title: 'Evidencia de placa',
            draft: _plateEvidence,
            uploaded: _uploadedPlateEvidence,
            onUseMock: () => _useMockEvidence(isFace: false),
            onPickGallery: () => _pickEvidence(isFace: false, source: ImageSource.gallery),
            onCapture: _supportsCameraCapture ? () => _pickEvidence(isFace: false, source: ImageSource.camera) : null,
          ),
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
          Text('Confianza placa: ${_plateConfidence.toStringAsFixed(2)}'),
          Slider(value: _plateConfidence, onChanged: (value) => setState(() => _plateConfidence = value)),
          Text('Confianza rostro: ${_faceConfidence.toStringAsFixed(2)}'),
          Slider(value: _faceConfidence, onChanged: (value) => setState(() => _faceConfidence = value)),
          const SizedBox(height: 24),
          FilledButton(
            onPressed: _submitting ? null : _submit,
            child: _submitting
                ? const SizedBox(height: 20, width: 20, child: CircularProgressIndicator(strokeWidth: 2))
                : const Text('Validar salida'),
          ),
        ],
      ),
    );
  }
}
