import 'package:camera/camera.dart';
import 'package:flutter/material.dart';

import '../models/app_models.dart';
import '../services/liveness/liveness_service.dart';
import '../widgets/camera_preview_panel.dart';

class CaptureFaceScreen extends StatefulWidget {
  const CaptureFaceScreen({super.key});

  @override
  State<CaptureFaceScreen> createState() => _CaptureFaceScreenState();
}

class _CaptureFaceScreenState extends State<CaptureFaceScreen> {
  final LivenessService _livenessService = LivenessService();
  CameraController? _controller;
  late LivenessChallenge _challenge;
  bool _ready = false;
  bool _loading = true;
  bool _validating = false;
  LivenessCheckResult? _lastResult;

  @override
  void initState() {
    super.initState();
    _challenge = _livenessService.nextChallenge();
    _initializeCamera();
  }

  Future<void> _initializeCamera() async {
    try {
      final cameras = await availableCameras();
      if (cameras.isNotEmpty) {
        final selectedCamera = cameras.firstWhere(
          (camera) => camera.lensDirection == CameraLensDirection.front,
          orElse: () => cameras.first,
        );
        final controller = CameraController(
            selectedCamera, ResolutionPreset.medium,
            enableAudio: false);
        await controller.initialize();
        if (!mounted) return;
        setState(() {
          _controller = controller;
          _ready = true;
          _loading = false;
        });
        return;
      }
    } catch (_) {}

    if (!mounted) return;
    setState(() {
      _ready = false;
      _loading = false;
    });
  }

  @override
  void dispose() {
    _controller?.dispose();
    super.dispose();
  }

  void _refreshChallenge() {
    setState(() {
      _challenge = _livenessService.nextChallenge();
      _lastResult = null;
    });
  }

  Future<void> _capture() async {
    setState(() {
      _validating = true;
      _lastResult = null;
    });

    if (_controller != null && _controller!.value.isInitialized) {
      try {
        await _controller!.takePicture();
      } catch (_) {}
    }

    final result = await _livenessService.performCheck(
      challenge: _challenge,
      cameraReady: _ready,
    );

    if (!mounted) return;
    if (!result.accepted) {
      setState(() {
        _lastResult = result;
        _validating = false;
      });
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
            content: Text(result.failureReason ??
                'La validacion de liveness no fue aprobada.')),
      );
      return;
    }

    Navigator.of(context).pop(result);
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(title: const Text('Captura de rostro')),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            if (_loading)
              const Expanded(child: Center(child: CircularProgressIndicator()))
            else
              Expanded(
                child: CameraPreviewPanel(
                  controller: _controller,
                  isReady: _ready,
                  title: 'Camara no disponible',
                  subtitle:
                      'Puedes simular la captura para continuar el flujo.',
                ),
              ),
            const SizedBox(height: 16),
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: theme.colorScheme.surfaceContainerHighest,
                borderRadius: BorderRadius.circular(8),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Reto activo', style: theme.textTheme.titleMedium),
                  const SizedBox(height: 8),
                  Text(_challenge.label, style: theme.textTheme.bodyLarge),
                  const SizedBox(height: 4),
                  Text(_challenge.instruction),
                  const SizedBox(height: 12),
                  Text(
                    'Proveedor actual: ${_livenessService.activeProviderName}',
                    style: theme.textTheme.bodySmall,
                  ),
                ],
              ),
            ),
            if (_lastResult != null) ...[
              const SizedBox(height: 12),
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: _lastResult!.accepted
                      ? Colors.green.withOpacity(0.10)
                      : Colors.orange.withOpacity(0.12),
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(
                    color: _lastResult!.accepted ? Colors.green : Colors.orange,
                  ),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      _lastResult!.accepted
                          ? 'Liveness aprobado'
                          : 'Liveness rechazado',
                      style: theme.textTheme.titleSmall,
                    ),
                    const SizedBox(height: 8),
                    Text(
                        'Score: ${_lastResult!.livenessScore.toStringAsFixed(2)}'),
                    Text('Frames simulados: ${_lastResult!.frames.length}'),
                    if (_lastResult!.failureReason != null) ...[
                      const SizedBox(height: 6),
                      Text(_lastResult!.failureReason!),
                    ],
                  ],
                ),
              ),
            ],
            const SizedBox(height: 16),
            FilledButton.icon(
              onPressed: _loading || _validating ? null : _capture,
              icon: const Icon(Icons.verified_user),
              label: Text(
                  _validating ? 'Validando reto...' : 'Iniciar validacion'),
            ),
            const SizedBox(height: 12),
            OutlinedButton.icon(
              onPressed: _loading || _validating ? null : _refreshChallenge,
              icon: const Icon(Icons.refresh),
              label: const Text('Cambiar reto'),
            ),
          ],
        ),
      ),
    );
  }
}
