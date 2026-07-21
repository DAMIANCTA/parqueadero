import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';

import '../config/debug_flags.dart';
import '../models/app_models.dart';
import '../models/history_entry.dart';
import '../services/api_client.dart';
import '../services/image_preparation_service.dart';
import '../state/parking_app_scope.dart';
import '../theme/ucepark_theme.dart';
import '../widgets/uce_widgets.dart';
import 'face_camera_capture_screen.dart';
import 'plate_camera_capture_screen.dart';
import 'result_screen.dart';

class EntryModeScreen extends StatefulWidget {
  const EntryModeScreen({super.key});

  static const routeName = '/entry-mode';

  @override
  State<EntryModeScreen> createState() => _EntryModeScreenState();
}

class _EntryModeScreenState extends State<EntryModeScreen> {
  static const String _pendingPlatePlaceholder = 'TMP000';

  final ApiClient _apiClient = ApiClient();
  final ImagePreparationService _imagePreparationService =
      const ImagePreparationService();
  final ImagePicker _picker = ImagePicker();
  final TextEditingController _plateController = TextEditingController();
  final TextEditingController _manualPlateController = TextEditingController();
  final TextEditingController _overrideReasonController =
      TextEditingController();

  PersonType _personType = PersonType.visitor;
  bool _faceValid = true;
  bool _livenessValid = true;
  double _faceConfidence = 0.95;
  FaceServiceConfig? _faceConfig;
  bool _submitting = false;
  bool _uploadingFaceEvidence = false;
  bool _processingPlateEvidence = false;
  LocalEvidenceDraft? _faceEvidence;
  List<LocalEvidenceDraft> _plateEvidences = const [];
  EvidenceUploadResult? _uploadedFaceEvidence;
  List<EvidenceUploadResult> _uploadedPlateEvidences = const [];
  PlateBatchDetectionResult? _plateBatchDetection;
  PlateDetectionResult? _plateDetection;

  bool get _supportsCameraCapture =>
      !kIsWeb &&
      (defaultTargetPlatform == TargetPlatform.android ||
          defaultTargetPlatform == TargetPlatform.iOS);

  bool get _supportsMultiGallery => !kIsWeb;

  bool get _isSecurityOperator =>
      ParkingAppScope.of(context).isSecurityOperator;
  bool get _useRealFaceFlow => _faceConfig?.usesRealOrHybrid ?? false;
  bool get _hasFaceEvidenceReady =>
      _faceEvidence != null || _uploadedFaceEvidence != null;

  bool get _usingManualOverride {
    if (!_isSecurityOperator) {
      return false;
    }
    final manual = _normalizedManualPlate;
    return manual.isNotEmpty && manual != (_plateDetection?.plateText ?? '');
  }

  String get _normalizedManualPlate => _manualPlateController.text
      .trim()
      .toUpperCase()
      .replaceAll(' ', '')
      .replaceAll('-', '');

  bool get _hasValidDetectedPlate => _plateDetection?.autoAccepted ?? false;

  bool get _hasManualOverrideReady =>
      _usingManualOverride &&
      _normalizedManualPlate.length >= 6 &&
      _overrideReasonController.text.trim().isNotEmpty;

  bool get _canSubmitWithPlate =>
      _hasValidDetectedPlate || _hasManualOverrideReady;

  String get _effectivePlateText {
    if (_usingManualOverride) {
      return _normalizedManualPlate;
    }
    return _plateDetection?.plateText ?? '';
  }

  double get _effectivePlateConfidence =>
      _usingManualOverride ? 1.0 : (_plateDetection?.confidence ?? 0.0);

  EvidenceUploadResult? get _selectedPlateEvidence {
    if (_uploadedPlateEvidences.isEmpty) {
      return null;
    }
    final detectedPlate = _plateDetection?.plateText;
    final batch = _plateBatchDetection;
    if (detectedPlate == null || batch == null) {
      return _uploadedPlateEvidences.first;
    }

    PlateBatchResultItem? bestMatch;
    for (final result in batch.results) {
      if (result.plateText != detectedPlate) {
        continue;
      }
      if (bestMatch == null || result.confidence > bestMatch.confidence) {
        bestMatch = result;
      }
    }

    if (bestMatch == null) {
      return _uploadedPlateEvidences.first;
    }

    for (final upload in _uploadedPlateEvidences) {
      if (upload.imageId == bestMatch.imageId) {
        return upload;
      }
    }
    return _uploadedPlateEvidences.first;
  }

  @override
  void initState() {
    super.initState();
    _loadFaceConfig();
  }

  Future<void> _loadFaceConfig() async {
    try {
      final config = await _apiClient.getFaceConfig();
      if (!mounted) return;
      setState(() => _faceConfig = config);
    } catch (_) {}
  }

  @override
  void dispose() {
    _plateController.dispose();
    _manualPlateController.dispose();
    _overrideReasonController.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    final appScope = ParkingAppScope.of(context);
    final session = appScope.session;
    final selection = appScope.selection;
    if (selection == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
            content:
                Text('Completa la seleccion de universidad, campus y puerta.')),
      );
      return;
    }
    if (!_canSubmitWithPlate) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
            content: Text(
                'Debes detectar una placa valida antes de registrar la entrada.')),
      );
      return;
    }
    if (!_hasFaceEvidenceReady) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
            content: Text(
                'Debes capturar el rostro antes de registrar la entrada.')),
      );
      return;
    }

    setState(() => _submitting = true);
    try {
      final effectivePlate = _effectivePlateText;
      final faceEvidence = await _ensureFaceEvidenceUploaded(
        imageType: EvidenceImageType.faceEntry,
        plate: effectivePlate,
        universityId: selection.universityId,
      );
      final plateEvidence = _selectedPlateEvidence;
      if (plateEvidence == null) {
        throw Exception('No hay evidencia de placa cargada.');
      }

      final result = await _apiClient.submitEntry(
        universityId: selection.universityId,
        campusId: selection.campusId,
        gateId: selection.gateId,
        plateText: effectivePlate,
        faceImageId: faceEvidence.imageId,
        plateImageId: plateEvidence.imageId,
        faceMockId: _useRealFaceFlow ? null : _buildFaceImageId(effectivePlate),
        operatorUsername: session?.username,
        plateDetectedText: _plateDetection?.plateText,
        plateDetectionConfidence: _plateDetection?.confidence,
        plateOverrideReason:
            _usingManualOverride ? _overrideReasonController.text.trim() : null,
        livenessScore:
            showDebugControls ? (_livenessValid ? 0.95 : 0.30) : 0.95,
        personType: _personType,
        confidencePlate: _effectivePlateConfidence,
        confidenceFace: showDebugControls && !_useRealFaceFlow
            ? (_faceValid ? _faceConfidence : 0.35)
            : 0.95,
      );
      if (!mounted) return;
      appScope.addHistory(
        HistoryEntry.fromResult(
          mode: ModeType.entry,
          plateText: effectivePlate,
          result: result,
          plateDetection: _plateDetection,
          faceImageId: faceEvidence.imageId,
        ),
      );
      Navigator.of(context)
          .pushNamed(ResultScreen.routeName, arguments: result);
    } catch (error) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
            content: Text(error.toString().replaceFirst('Exception: ', ''))),
      );
    } finally {
      if (mounted) {
        setState(() => _submitting = false);
      }
    }
  }

  Future<void> _pickEvidence(
      {required bool isFace, required ImageSource source}) async {
    if (!isFace) {
      if (source == ImageSource.camera) {
        await _capturePlateWithEmbeddedCamera();
        return;
      }
      await _collectPlateEvidences(source: source);
      return;
    }

    if (source == ImageSource.camera) {
      await _captureFaceWithEmbeddedCamera();
      return;
    }

    try {
      final file = await _picker.pickImage(source: source, imageQuality: 85);
      if (file == null) {
        return;
      }
      final draft = await _imagePreparationService.buildDraft(
        file: file,
        label: source == ImageSource.camera ? 'Capturada' : 'Seleccionada',
      );
      _setEvidenceDraft(isFace: true, draft: draft);
      await _uploadCapturedFaceEvidence();
    } catch (_) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('No se pudo obtener la imagen.')),
      );
    }
  }

  Future<void> _captureFaceWithEmbeddedCamera() async {
    if (!_canSubmitWithPlate) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
            content: Text(
                'Primero captura una placa valida antes de tomar el rostro.')),
      );
      return;
    }

    try {
      final capturedFile = await Navigator.of(context).push<XFile>(
        MaterialPageRoute<XFile>(
          builder: (_) => const FaceCameraCaptureScreen(),
        ),
      );

      if (capturedFile == null) {
        return;
      }

      final draft = await _imagePreparationService.buildDraft(
        file: capturedFile,
        label: 'Rostro capturado',
      );
      _setEvidenceDraft(isFace: true, draft: draft);
      await _uploadCapturedFaceEvidence();
    } catch (_) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
            content: Text(
                'La captura interna de rostro fallo. Intenta nuevamente.')),
      );
    }
  }

  Future<void> _capturePlateWithEmbeddedCamera() async {
    try {
      final capturedFiles = await Navigator.of(context).push<List<XFile>>(
        MaterialPageRoute<List<XFile>>(
          builder: (_) => const PlateCameraCaptureScreen(),
        ),
      );

      if (capturedFiles == null || capturedFiles.isEmpty) {
        return;
      }

      final drafts = <LocalEvidenceDraft>[];
      for (var index = 0; index < capturedFiles.length && index < 3; index++) {
        final file = capturedFiles[index];
        drafts.add(
          await _imagePreparationService.buildDraft(
            file: file,
            label: 'Capturada ${index + 1}',
          ),
        );
      }

      if (drafts.isEmpty) {
        if (!mounted) return;
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
              content: Text('No se pudieron procesar las capturas de placa.')),
        );
        return;
      }

      _setPlateEvidenceDrafts(drafts);
      await _uploadAndDetectPlateBatch();
    } catch (_) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
            content:
                Text('La captura interna de placa fallo. Intenta nuevamente.')),
      );
    }
  }

  Future<void> _useMockEvidence({required bool isFace}) async {
    if (!isFace) {
      final drafts = List<LocalEvidenceDraft>.generate(
        3,
        (index) =>
            _buildDefaultMockEvidence(isFace: false, suffix: '-${index + 1}'),
      );
      _setPlateEvidenceDrafts(drafts);
      await _uploadAndDetectPlateBatch();
      return;
    }

    final draft = _buildDefaultMockEvidence(isFace: isFace);
    _setEvidenceDraft(isFace: isFace, draft: draft);
  }

  void _setEvidenceDraft(
      {required bool isFace, required LocalEvidenceDraft draft}) {
    setState(() {
      if (isFace) {
        _faceEvidence = draft;
        _uploadedFaceEvidence = null;
      }
    });
  }

  void _setPlateEvidenceDrafts(List<LocalEvidenceDraft> drafts) {
    setState(() {
      _plateEvidences = List<LocalEvidenceDraft>.from(drafts.take(3));
      _uploadedPlateEvidences = const [];
      _plateBatchDetection = null;
      _plateDetection = null;
      _plateController.clear();
      _manualPlateController.clear();
      _overrideReasonController.clear();
    });
  }

  Future<EvidenceUploadResult> _ensureFaceEvidenceUploaded({
    required EvidenceImageType imageType,
    required String plate,
    required String universityId,
  }) async {
    final existing = _uploadedFaceEvidence;
    if (existing != null && existing.plate == plate) {
      return existing;
    }

    final normalizedPlate = plate.trim().toUpperCase();
    final draft = _faceEvidence ??
        (showDebugControls ? _buildDefaultMockEvidence(isFace: true) : null);
    if (draft == null) {
      throw Exception('Captura el rostro antes de continuar.');
    }

    setState(() => _uploadingFaceEvidence = true);
    try {
      final result = await _apiClient.uploadEvidence(
        imageType: imageType,
        plate: normalizedPlate,
        universityId: universityId,
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

  Future<void> _uploadCapturedFaceEvidence() async {
    final draft = _faceEvidence;
    if (draft == null) {
      return;
    }

    final plate = _effectivePlateText;
    if (plate.isEmpty) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
            content: Text(
                'Primero detecta una placa valida antes de subir el rostro.')),
      );
      return;
    }

    final selection = ParkingAppScope.of(context).selection;
    if (selection == null) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
            content: Text(
                'Selecciona universidad, campus y puerta antes de subir el rostro.')),
      );
      return;
    }

    setState(() => _uploadingFaceEvidence = true);
    try {
      final result = await _apiClient.uploadEvidence(
        imageType: EvidenceImageType.faceEntry,
        plate: plate,
        universityId: selection.universityId,
        evidence: draft,
      );
      if (!mounted) return;
      setState(() => _uploadedFaceEvidence = result);
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
            content: Text('Rostro capturado y cargado correctamente.')),
      );
    } catch (error) {
      if (!mounted) return;
      setState(() => _uploadedFaceEvidence = null);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
            content: Text(error.toString().replaceFirst('Exception: ', ''))),
      );
    } finally {
      if (mounted) {
        setState(() => _uploadingFaceEvidence = false);
      }
    }
  }

  Future<void> _collectPlateEvidences({required ImageSource source}) async {
    try {
      final drafts = <LocalEvidenceDraft>[];
      if (source == ImageSource.gallery && _supportsMultiGallery) {
        final files = await _picker.pickMultiImage(imageQuality: 85);
        if (files.isEmpty) {
          return;
        }
        for (final file in files.take(3)) {
          drafts.add(await _imagePreparationService.buildDraft(
              file: file, label: 'Seleccionada'));
        }
      } else {
        for (var index = 0; index < 3; index++) {
          final file =
              await _picker.pickImage(source: source, imageQuality: 85);
          if (file == null) {
            break;
          }
          drafts.add(
            await _imagePreparationService.buildDraft(
              file: file,
              label: source == ImageSource.camera
                  ? 'Capturada ${index + 1}'
                  : 'Seleccionada ${index + 1}',
            ),
          );
        }
      }

      if (drafts.isEmpty) {
        return;
      }

      _setPlateEvidenceDrafts(drafts);
      await _uploadAndDetectPlateBatch();
    } catch (_) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
            content: Text('No se pudieron obtener las capturas de placa.')),
      );
    }
  }

  Future<void> _uploadAndDetectPlateBatch() async {
    final selection = ParkingAppScope.of(context).selection;
    if (selection == null) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
            content: Text(
                'Selecciona universidad, campus y puerta antes de capturar la placa.')),
      );
      return;
    }

    final drafts = _plateEvidences.isNotEmpty
        ? _plateEvidences
        : List<LocalEvidenceDraft>.generate(
            3,
            (index) => _buildDefaultMockEvidence(
                isFace: false, suffix: '-${index + 1}'));
    setState(() => _processingPlateEvidence = true);
    try {
      final uploads = <EvidenceUploadResult>[];
      for (final draft in drafts) {
        final upload = await _apiClient.uploadEvidence(
          imageType: EvidenceImageType.plateEntry,
          plate: _pendingPlatePlaceholder,
          universityId: selection.universityId,
          evidence: draft,
        );
        uploads.add(upload);
      }

      final batchDetection = await _apiClient.detectPlateBatch(
        imageIds: uploads.map((item) => item.imageId).toList(),
        universityId: selection.universityId,
        campusId: selection.campusId,
        gateId: selection.gateId,
      );
      final detection = batchDetection.toPrimaryDetection();
      if (!mounted) return;
      setState(() {
        _plateEvidences = drafts;
        _uploadedPlateEvidences = uploads;
        _plateBatchDetection = batchDetection;
        _plateDetection = detection;
        _plateController.text = detection.plateText ?? '';
      });
      if (batchDetection.inconsistent) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
              content: Text('Resultado inconsistente entre capturas.')),
        );
      } else if (!detection.autoAccepted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
              content:
                  Text('La deteccion de placa no tiene confianza suficiente.')),
        );
      }
    } catch (error) {
      if (!mounted) return;
      setState(() {
        _uploadedPlateEvidences = const [];
        _plateBatchDetection = null;
        _plateDetection = null;
        _plateController.clear();
      });
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
            content: Text(error.toString().replaceFirst('Exception: ', ''))),
      );
    } finally {
      if (mounted) {
        setState(() => _processingPlateEvidence = false);
      }
    }
  }

  LocalEvidenceDraft _buildDefaultMockEvidence(
      {required bool isFace, String suffix = ''}) {
    final mockPlate = isFace
        ? (_effectivePlateText.isEmpty
            ? _recommendedMockPlate()
            : _effectivePlateText)
        : _recommendedMockPlate();
    final slot = isFace ? 'face-entry' : 'plate-entry';
    return LocalEvidenceDraft(
      label: isFace ? 'Mock automatico rostro' : 'Mock automatico placa',
      fileName: '$slot-$mockPlate$suffix.txt',
      bytes: Uint8List.fromList(utf8.encode('mock:$slot:$mockPlate$suffix')),
      contentType: 'text/plain',
      isMock: true,
    );
  }

  String _recommendedMockPlate() {
    return switch (_personType) {
      PersonType.visitor => 'VIS1001',
      PersonType.student => 'ABC1234',
      PersonType.teacher => 'XYZ9876',
      PersonType.employee => 'EMP2026',
    };
  }

  String _buildFaceImageId(String plate) {
    if (!_faceValid) {
      return 'face-entry-invalid';
    }
    return switch (_personType) {
      PersonType.student => 'face-student-001',
      PersonType.teacher => 'face-teacher-001',
      PersonType.employee =>
        plate == 'EXP2026' ? 'face-expired-001' : 'face-employee-001',
      PersonType.visitor => 'face-entry-$plate',
    };
  }

  Widget _buildFaceEvidenceCard() {
    return UceCard(
      padding: const EdgeInsets.all(14),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('Evidencia de rostro',
              style: Theme.of(context).textTheme.titleSmall),
          const SizedBox(height: 8),
          Text(_faceEvidence == null
              ? 'Sin rostro capturado.'
              : 'Rostro capturado.'),
          if (_uploadedFaceEvidence != null) ...[
            const SizedBox(height: 4),
            const Text('Evidencia facial lista para validacion.'),
            if (showDebugControls)
              Text('Image ID: ${_uploadedFaceEvidence!.imageId}'),
          ],
          if (_uploadingFaceEvidence) ...[
            const SizedBox(height: 12),
            const Row(
              children: [
                SizedBox(
                    height: 18,
                    width: 18,
                    child: CircularProgressIndicator(strokeWidth: 2)),
                SizedBox(width: 12),
                Text('Subiendo rostro...'),
              ],
            ),
          ],
          const SizedBox(height: 12),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              if (_supportsCameraCapture)
                FilledButton.icon(
                  onPressed: _uploadingFaceEvidence || _submitting
                      ? null
                      : () => _pickEvidence(
                          isFace: true, source: ImageSource.camera),
                  icon: const Icon(Icons.photo_camera_outlined),
                  label: const Text('Capturar rostro'),
                ),
              if (showDebugControls)
                OutlinedButton.icon(
                  onPressed: _uploadingFaceEvidence || _submitting
                      ? null
                      : () => _pickEvidence(
                          isFace: true, source: ImageSource.gallery),
                  icon: const Icon(Icons.photo_library_outlined),
                  label: const Text('Seleccionar'),
                ),
              if (showDebugControls && !_useRealFaceFlow)
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
    return UceCard(
      padding: const EdgeInsets.all(14),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('Captura y deteccion de placa',
              style: Theme.of(context).textTheme.titleSmall),
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
          Text(
            _plateEvidences.isEmpty
                ? 'Sin evidencias seleccionadas.'
                : '${_plateEvidences.length} capturas listas para procesar.',
          ),
          if (_uploadedPlateEvidences.isNotEmpty) ...[
            const SizedBox(height: 4),
            Text('Imagenes subidas: ${_uploadedPlateEvidences.length}/3'),
          ],
          const SizedBox(height: 12),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              if (_supportsCameraCapture)
                FilledButton.icon(
                  onPressed: _processingPlateEvidence
                      ? null
                      : () => _pickEvidence(
                          isFace: false, source: ImageSource.camera),
                  icon: const Icon(Icons.photo_camera_outlined),
                  label: const Text('Capturar placa'),
                ),
              if (showDebugControls)
                OutlinedButton.icon(
                  onPressed: _processingPlateEvidence
                      ? null
                      : () => _pickEvidence(
                          isFace: false, source: ImageSource.gallery),
                  icon: const Icon(Icons.photo_library_outlined),
                  label: const Text('Seleccionar 3 imagenes'),
                ),
              if (showDebugControls)
                OutlinedButton.icon(
                  onPressed: _processingPlateEvidence
                      ? null
                      : () => _useMockEvidence(isFace: false),
                  icon: const Icon(Icons.auto_fix_high_outlined),
                  label: const Text('Usar mock'),
                ),
              if (_plateEvidences.isNotEmpty)
                OutlinedButton.icon(
                  onPressed: _processingPlateEvidence
                      ? null
                      : () => _pickEvidence(
                            isFace: false,
                            source: _supportsCameraCapture
                                ? ImageSource.camera
                                : ImageSource.gallery,
                          ),
                  icon: const Icon(Icons.refresh),
                  label: const Text('Reintentar captura'),
                ),
            ],
          ),
          const SizedBox(height: 16),
          if (_processingPlateEvidence)
            const Row(
              children: [
                SizedBox(
                    height: 18,
                    width: 18,
                    child: CircularProgressIndicator(strokeWidth: 2)),
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
                color: _plateDetection!.autoAccepted
                    ? Colors.green.withOpacity(0.08)
                    : Colors.orange.withOpacity(0.08),
                border: Border.all(
                    color: _plateDetection!.autoAccepted
                        ? Colors.green
                        : Colors.orange),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Estado: ${_plateDetection!.status}'),
                  Text(
                      'Placa detectada: ${_plateDetection!.plateText ?? 'Sin lectura valida'}'),
                  Text(
                      'Confianza: ${(_plateDetection!.confidence * 100).toStringAsFixed(0)}%'),
                  Text(
                      'Proveedor detector: ${_plateDetection!.detectorProvider}'),
                  Text('Proveedor OCR: ${_plateDetection!.ocrProvider}'),
                  if (_plateBatchDetection != null) ...[
                    const SizedBox(height: 8),
                    Text('Resultados por captura:',
                        style: Theme.of(context).textTheme.titleSmall),
                    const SizedBox(height: 4),
                    ..._plateBatchDetection!.results.map(
                      (result) => Text(
                        '${result.imageId}: ${result.plateText ?? 'sin lectura'} - ${(result.confidence * 100).toStringAsFixed(0)}% (${result.status})',
                      ),
                    ),
                  ],
                  if (_plateDetection!.warnings.isNotEmpty) ...[
                    const SizedBox(height: 8),
                    Text('Advertencias:',
                        style: Theme.of(context).textTheme.titleSmall),
                    const SizedBox(height: 4),
                    ..._plateDetection!.warnings
                        .map((warning) => Text('- $warning')),
                  ],
                  if (_plateDetection!.candidates.isNotEmpty) ...[
                    const SizedBox(height: 8),
                    Text('Candidatos:',
                        style: Theme.of(context).textTheme.titleSmall),
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
            const Text(
                'Captura la placa para iniciar la deteccion automatica.'),
          if (_isSecurityOperator) ...[
            const SizedBox(height: 16),
            TextField(
              controller: _manualPlateController,
              textCapitalization: TextCapitalization.characters,
              decoration: const InputDecoration(
                labelText: 'Correccion manual de placa (solo seguridad)',
                border: OutlineInputBorder(),
              ),
              onChanged: (_) => setState(() => _plateController.text =
                  _usingManualOverride
                      ? _normalizedManualPlate
                      : (_plateDetection?.plateText ?? '')),
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
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.fromLTRB(18, 10, 18, 14),
          children: [
            const UceTopBar(showBack: true),
            const SizedBox(height: 14),
            Text(
              'Modo entrada',
              style: Theme.of(context).textTheme.headlineSmall,
            ),
            const Text(
              'Registro institucional de ingreso vehicular',
              style: TextStyle(fontSize: 13.5, color: UceParkColors.muted),
            ),
            const SizedBox(height: 16),
            DropdownButtonFormField<PersonType>(
              value: _personType,
              decoration: const InputDecoration(
                  labelText: 'Tipo de persona', border: OutlineInputBorder()),
              items: PersonType.values
                  .map((type) =>
                      DropdownMenuItem(value: type, child: Text(type.label)))
                  .toList(),
              onChanged: (value) =>
                  setState(() => _personType = value ?? PersonType.visitor),
            ),
            const SizedBox(height: 16),
            _buildPlateDetectionCard(),
            const SizedBox(height: 16),
            _buildFaceEvidenceCard(),
            if (showDebugControls) ...[
              const SizedBox(height: 12),
              if (!_useRealFaceFlow)
                SwitchListTile(
                  value: _faceValid,
                  title: const Text('Simulador de rostro valido'),
                  subtitle: Text(_faceValid
                      ? 'La validacion facial pasara.'
                      : 'La validacion facial fallara.'),
                  onChanged: (value) => setState(() => _faceValid = value),
                ),
              const SizedBox(height: 12),
              SwitchListTile(
                value: _livenessValid,
                title: const Text('Simulador de liveness valido'),
                subtitle: Text(_livenessValid
                    ? 'El liveness pasara.'
                    : 'El liveness sera bloqueado.'),
                onChanged: (value) => setState(() => _livenessValid = value),
              ),
              if (!_useRealFaceFlow) ...[
                const SizedBox(height: 20),
                Text('Confianza rostro: ${_faceConfidence.toStringAsFixed(2)}'),
                Slider(
                    value: _faceConfidence,
                    onChanged: (value) =>
                        setState(() => _faceConfidence = value)),
              ],
            ],
            const SizedBox(height: 24),
            FilledButton(
              onPressed: (_submitting ||
                      !_canSubmitWithPlate ||
                      !_hasFaceEvidenceReady ||
                      _processingPlateEvidence ||
                      _uploadingFaceEvidence)
                  ? null
                  : _submit,
              child: _submitting
                  ? const SizedBox(
                      height: 20,
                      width: 20,
                      child: CircularProgressIndicator(strokeWidth: 2))
                  : const Text('Registrar entrada'),
            ),
          ],
        ),
      ),
    );
  }
}
