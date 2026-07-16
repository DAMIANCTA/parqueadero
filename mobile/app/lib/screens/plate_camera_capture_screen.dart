import 'dart:async';

import 'package:camera/camera.dart';
import 'package:flutter/material.dart';

class PlateCameraCaptureScreen extends StatefulWidget {
  const PlateCameraCaptureScreen({super.key});

  @override
  State<PlateCameraCaptureScreen> createState() =>
      _PlateCameraCaptureScreenState();
}

class _PlateCameraCaptureScreenState extends State<PlateCameraCaptureScreen>
    with WidgetsBindingObserver {
  CameraController? _controller;
  bool _loading = true;
  bool _ready = false;
  bool _capturing = false;
  String? _cameraError;
  int _currentShot = 0;

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
        (camera) => camera.lensDirection == CameraLensDirection.back,
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
        _currentShot = 0;
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
            'No se pudo iniciar la camara. Verifica permisos e intenta de nuevo.';
      });
    }
  }

  String _buildCameraErrorMessage(CameraException error) {
    switch (error.code) {
      case 'CameraAccessDenied':
      case 'cameraPermission':
        return 'Se necesita permiso de camara para capturar la placa.';
      case 'CameraAccessDeniedWithoutPrompt':
        return 'La camara fue bloqueada previamente. Habilitala desde ajustes del dispositivo.';
      case 'AudioAccessDenied':
        return 'El dispositivo rechazo permisos requeridos para la captura.';
      default:
        return 'No se pudo abrir la camara: ${error.description ?? error.code}.';
    }
  }

  Future<void> _captureThreePhotos() async {
    final controller = _controller;
    if (_capturing || controller == null || !controller.value.isInitialized) {
      return;
    }

    setState(() {
      _capturing = true;
      _currentShot = 0;
      _cameraError = null;
    });

    final shots = <XFile>[];

    try {
      for (var index = 0; index < 3; index++) {
        if (!mounted) return;
        setState(() {
          _currentShot = index + 1;
        });
        final shot = await controller.takePicture();
        shots.add(shot);
        if (index < 2) {
          await Future<void>.delayed(const Duration(milliseconds: 300));
        }
      }

      if (!mounted) return;
      Navigator.of(context).pop(shots);
    } on CameraException catch (error) {
      if (!mounted) return;
      setState(() {
        _cameraError =
            'Fallo la captura de placa: ${error.description ?? error.code}.';
      });
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(_cameraError!)),
      );
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _cameraError =
            'No se pudieron capturar las 3 fotos. Intenta nuevamente.';
      });
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
            content: Text(
                'No se pudieron capturar las 3 fotos. Intenta nuevamente.')),
      );
    } finally {
      if (mounted) {
        setState(() {
          _capturing = false;
          if (_currentShot < 3) {
            _currentShot = 0;
          }
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
        title: const Text('Capturar placa'),
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
                    Color(0x99000000),
                    Color(0x22000000),
                    Color(0xAA000000),
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
                    'Coloque la placa dentro del recuadro',
                    style: theme.textTheme.titleMedium?.copyWith(
                      color: Colors.white,
                      fontWeight: FontWeight.w600,
                    ),
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 8),
                  Text(
                    _capturing
                        ? 'Capturando placa...'
                        : 'La app tomara 3 fotos seguidas automaticamente.',
                    style: theme.textTheme.bodyMedium
                        ?.copyWith(color: Colors.white70),
                    textAlign: TextAlign.center,
                  ),
                  const Spacer(),
                  Center(
                    child: Container(
                      width: 280,
                      height: 120,
                      decoration: BoxDecoration(
                        border: Border.all(
                            color: const Color(0xFF7A1F2E), width: 3),
                        borderRadius: BorderRadius.circular(12),
                        boxShadow: const [
                          BoxShadow(
                              color: Color(0x557A1F2E),
                              blurRadius: 18,
                              spreadRadius: 2),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(height: 16),
                  Center(
                    child: Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 16, vertical: 10),
                      decoration: BoxDecoration(
                        color: Colors.black.withOpacity(0.45),
                        borderRadius: BorderRadius.circular(999),
                        border: Border.all(color: Colors.white24),
                      ),
                      child: Text(
                        _capturing
                            ? 'Foto $_currentShot/3'
                            : 'Listo para capturar 3 fotos',
                        style: theme.textTheme.bodyMedium?.copyWith(
                          color: Colors.white,
                          fontWeight: FontWeight.w600,
                        ),
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
                      onPressed: _capturing ? null : _captureThreePhotos,
                      style: FilledButton.styleFrom(
                        backgroundColor: const Color(0xFF15294D),
                        foregroundColor: Colors.white,
                        padding: const EdgeInsets.symmetric(vertical: 16),
                      ),
                      icon: _capturing
                          ? const SizedBox(
                              height: 18,
                              width: 18,
                              child: CircularProgressIndicator(
                                  strokeWidth: 2, color: Colors.white),
                            )
                          : const Icon(Icons.photo_camera),
                      label: Text(
                          _capturing ? 'Capturando placa...' : 'Tomar 3 fotos'),
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
