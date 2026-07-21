import 'package:camera/camera.dart';
import 'package:flutter/material.dart';

import '../theme/ucepark_theme.dart';

class FaceCameraCaptureScreen extends StatefulWidget {
  const FaceCameraCaptureScreen({super.key});

  @override
  State<FaceCameraCaptureScreen> createState() =>
      _FaceCameraCaptureScreenState();
}

class _FaceCameraCaptureScreenState extends State<FaceCameraCaptureScreen>
    with WidgetsBindingObserver {
  CameraController? _controller;
  bool _loading = true;
  bool _ready = false;
  bool _capturing = false;
  String? _cameraError;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _initializeCamera();
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    _disposeController();
    super.dispose();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    final controller = _controller;
    if (controller == null || !controller.value.isInitialized) {
      return;
    }

    if (state == AppLifecycleState.inactive ||
        state == AppLifecycleState.paused) {
      _disposeController();
      if (mounted) {
        setState(() {
          _ready = false;
        });
      }
      return;
    }

    if (state == AppLifecycleState.resumed && mounted && !_capturing) {
      _initializeCamera();
    }
  }

  Future<void> _disposeController() async {
    final controller = _controller;
    _controller = null;
    if (controller != null) {
      await controller.dispose();
    }
  }

  Future<void> _initializeCamera() async {
    if (_capturing) {
      return;
    }

    setState(() {
      _loading = true;
      _cameraError = null;
    });

    try {
      final cameras = await availableCameras();
      if (cameras.isEmpty) {
        throw CameraException(
            'camera-not-found', 'No se encontro una camara disponible.');
      }

      final selectedCamera = cameras.firstWhere(
        (camera) => camera.lensDirection == CameraLensDirection.front,
        orElse: () => cameras.first,
      );

      final controller = CameraController(
        selectedCamera,
        ResolutionPreset.high,
        enableAudio: false,
        imageFormatGroup: ImageFormatGroup.jpeg,
      );

      await controller.initialize();
      await controller.setFlashMode(FlashMode.off);
      await _disposeController();

      if (!mounted) {
        await controller.dispose();
        return;
      }

      setState(() {
        _controller = controller;
        _loading = false;
        _ready = true;
        _cameraError = null;
      });
    } on CameraException catch (error) {
      if (!mounted) return;
      setState(() {
        _loading = false;
        _ready = false;
        _cameraError = _buildCameraErrorMessage(error);
      });
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _loading = false;
        _ready = false;
        _cameraError =
            'No se pudo iniciar la camara frontal. Verifica permisos e intenta de nuevo.';
      });
    }
  }

  String _buildCameraErrorMessage(CameraException error) {
    switch (error.code) {
      case 'CameraAccessDenied':
      case 'cameraPermission':
        return 'Se necesita permiso de camara para capturar el rostro.';
      case 'CameraAccessDeniedWithoutPrompt':
        return 'La camara fue bloqueada previamente. Habilitala desde ajustes del dispositivo.';
      default:
        return 'No se pudo abrir la camara frontal: ${error.description ?? error.code}.';
    }
  }

  Future<void> _captureFace() async {
    final controller = _controller;
    if (_capturing || controller == null || !controller.value.isInitialized) {
      return;
    }

    setState(() {
      _capturing = true;
      _cameraError = null;
    });

    try {
      final shot = await controller.takePicture();
      if (!mounted) return;
      Navigator.of(context).pop(shot);
    } on CameraException catch (error) {
      if (!mounted) return;
      final message =
          'Fallo la captura de rostro: ${error.description ?? error.code}.';
      setState(() {
        _cameraError = message;
      });
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(message)),
      );
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _cameraError = 'No se pudo capturar el rostro. Intenta nuevamente.';
      });
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
            content:
                Text('No se pudo capturar el rostro. Intenta nuevamente.')),
      );
    } finally {
      if (mounted) {
        setState(() {
          _capturing = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      backgroundColor: Colors.black,
      appBar: AppBar(
        title: const Text('Capturar rostro'),
      ),
      body: SafeArea(
        child: Stack(
          fit: StackFit.expand,
          children: [
            if (_ready && _controller != null)
              CameraPreview(_controller!)
            else
              Container(color: Colors.black),
            Container(
              decoration: const BoxDecoration(
                gradient: LinearGradient(
                  begin: Alignment.topCenter,
                  end: Alignment.bottomCenter,
                  colors: [
                    Color(0xAA000000),
                    Color(0x22000000),
                    Color(0xBB000000),
                  ],
                ),
              ),
            ),
            Padding(
              padding: const EdgeInsets.fromLTRB(20, 24, 20, 24),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  Text(
                    'Coloque su rostro dentro de la guia',
                    style: theme.textTheme.titleMedium?.copyWith(
                      color: Colors.white,
                      fontWeight: FontWeight.w600,
                    ),
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 8),
                  Text(
                    _capturing
                        ? 'Capturando rostro...'
                        : 'Mire al frente y mantenga el rostro centrado.',
                    style: theme.textTheme.bodyMedium
                        ?.copyWith(color: Colors.white70),
                    textAlign: TextAlign.center,
                  ),
                  const Spacer(),
                  Center(
                    child: Container(
                      width: 240,
                      height: 320,
                      decoration: BoxDecoration(
                        border: Border.all(
                            color: UceParkColors.biometric, width: 3),
                        borderRadius: BorderRadius.circular(999),
                        boxShadow: [
                          BoxShadow(
                              color: UceParkColors.biometric
                                  .withValues(alpha: 0.35),
                              blurRadius: 18,
                              spreadRadius: 2),
                        ],
                      ),
                    ),
                  ),
                  const Spacer(),
                  if (_loading)
                    const Center(
                      child:
                          CircularProgressIndicator(color: Colors.tealAccent),
                    )
                  else if (_cameraError != null)
                    Container(
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(
                        color: Colors.white,
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Text(
                            _cameraError!,
                            style: theme.textTheme.bodyMedium,
                            textAlign: TextAlign.center,
                          ),
                          const SizedBox(height: 12),
                          FilledButton.icon(
                            onPressed: _capturing ? null : _initializeCamera,
                            icon: const Icon(Icons.refresh),
                            label: const Text('Reintentar camara'),
                          ),
                        ],
                      ),
                    )
                  else
                    FilledButton.icon(
                      onPressed: _capturing ? null : _captureFace,
                      icon: _capturing
                          ? const SizedBox(
                              height: 20,
                              width: 20,
                              child: CircularProgressIndicator(
                                strokeWidth: 2,
                                color: Colors.white,
                              ),
                            )
                          : const Icon(Icons.face_retouching_natural),
                      label: Text(_capturing
                          ? 'Capturando rostro...'
                          : 'Capturar rostro'),
                    ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
