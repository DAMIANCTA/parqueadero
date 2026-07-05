import 'package:camera/camera.dart';
import 'package:flutter/material.dart';

import '../widgets/camera_preview_panel.dart';

class CaptureFaceScreen extends StatefulWidget {
  const CaptureFaceScreen({super.key});

  @override
  State<CaptureFaceScreen> createState() => _CaptureFaceScreenState();
}

class _CaptureFaceScreenState extends State<CaptureFaceScreen> {
  CameraController? _controller;
  bool _ready = false;
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _initializeCamera();
  }

  Future<void> _initializeCamera() async {
    try {
      final cameras = await availableCameras();
      if (cameras.isNotEmpty) {
        final controller = CameraController(cameras.first, ResolutionPreset.medium, enableAudio: false);
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

  Future<void> _capture() async {
    if (_controller != null && _controller!.value.isInitialized) {
      await _controller!.takePicture();
    }
    if (!mounted) return;
    Navigator.of(context).pop('face-${DateTime.now().millisecondsSinceEpoch}');
  }

  @override
  Widget build(BuildContext context) {
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
                  subtitle: 'Puedes simular la captura para continuar el flujo.',
                ),
              ),
            const SizedBox(height: 16),
            FilledButton.icon(
              onPressed: _loading ? null : _capture,
              icon: const Icon(Icons.camera_alt),
              label: Text(_ready ? 'Capturar rostro' : 'Simular rostro'),
            ),
          ],
        ),
      ),
    );
  }
}
