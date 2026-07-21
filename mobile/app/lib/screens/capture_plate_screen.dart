import 'package:camera/camera.dart';
import 'package:flutter/material.dart';

import '../widgets/camera_preview_panel.dart';

class CapturePlateScreen extends StatefulWidget {
  const CapturePlateScreen({super.key});

  @override
  State<CapturePlateScreen> createState() => _CapturePlateScreenState();
}

class _CapturePlateScreenState extends State<CapturePlateScreen> {
  CameraController? _controller;
  final TextEditingController _plateController = TextEditingController();
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
        final controller = CameraController(
            cameras.first, ResolutionPreset.medium,
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
    _plateController.dispose();
    super.dispose();
  }

  Future<void> _useManualPlate() async {
    final plate = _plateController.text.trim().toUpperCase();
    if (plate.isEmpty) return;
    if (_controller != null && _controller!.value.isInitialized) {
      await _controller!.takePicture();
    }
    if (!mounted) return;
    Navigator.of(context).pop(plate);
  }

  void _simulateDetection() {
    Navigator.of(context).pop('ABC1234');
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Captura de placa')),
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
                      'Puedes escribir la placa manualmente o usar deteccion simulada.',
                ),
              ),
            const SizedBox(height: 16),
            TextField(
              controller: _plateController,
              textCapitalization: TextCapitalization.characters,
              decoration: const InputDecoration(
                labelText: 'Placa manual',
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 12),
            FilledButton.icon(
              onPressed: _useManualPlate,
              icon: const Icon(Icons.edit),
              label:
                  Text(_ready ? 'Usar captura y placa' : 'Usar placa manual'),
            ),
            const SizedBox(height: 12),
            OutlinedButton.icon(
              onPressed: _simulateDetection,
              icon: const Icon(Icons.auto_fix_high),
              label: const Text('Simular deteccion'),
            ),
          ],
        ),
      ),
    );
  }
}
