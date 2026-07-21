import 'dart:async';

import 'package:camera/camera.dart';
import 'package:flutter/material.dart';

import '../config/app_config.dart';
import '../models/app_models.dart';
import '../services/api_client.dart';
import '../services/garita_mqtt_service.dart';
import '../services/image_preparation_service.dart';
import '../state/parking_app_scope.dart';
import 'face_camera_capture_screen.dart';

/// Pantalla "Garita fisica": el celular se conecta al mismo broker MQTT que
/// usa garita_controller.py/el ESP32 para saber cuando hay que capturar el
/// rostro de un vehiculo que se presento en la barrera fisica (a diferencia
/// del flujo manual de Entrada/Salida, donde el operador dispara la captura
/// el mismo). Primero llega la placa que ya decidio garita_controller.py,
/// despues se pide el rostro.
class GaritaFisicaScreen extends StatefulWidget {
  const GaritaFisicaScreen({super.key});

  static const routeName = '/garita-fisica';

  @override
  State<GaritaFisicaScreen> createState() => _GaritaFisicaScreenState();
}

enum _Phase {
  needsMqttConfig,
  connecting,
  waitingPresence,
  waitingPlate,
  capturing,
  uploading,
  awaitingResult,
  result,
  error,
}

class _GaritaFisicaScreenState extends State<GaritaFisicaScreen> {
  static const int _maxFaceAttempts = 3;
  static const Duration _plateTimeout = Duration(seconds: 14);

  final GaritaMqttService _mqttService = GaritaMqttService();
  final ApiClient _apiClient = ApiClient();
  final ImagePreparationService _imagePreparationService =
      const ImagePreparationService();
  late final TextEditingController _mqttHostController =
      TextEditingController(text: AppConfig.mqttHost);

  _Phase _phase = _Phase.needsMqttConfig;
  String _statusText = 'Configura el broker MQTT de la garita.';
  String _mode = 'entrada';
  String? _plateText;
  int _faceAttempt = 0;
  bool? _resultAuthorized;
  String _resultMessage = '';

  StreamSubscription<GaritaPresenceEvent>? _presenceSub;
  StreamSubscription<GaritaPlateEvent>? _plateSub;
  StreamSubscription<GaritaResultEvent>? _resultSub;
  StreamSubscription<void>? _retrySub;
  Completer<GaritaPlateEvent>? _pendingPlateCompleter;

  @override
  void initState() {
    super.initState();
    _mqttService.onConnectionChanged = () {
      if (mounted) setState(() {});
    };
    _presenceSub = _mqttService.presenceStream.listen(_onPresence);
    _plateSub = _mqttService.plateStream.listen((event) {
      _pendingPlateCompleter?.complete(event);
      _pendingPlateCompleter = null;
    });
    _resultSub = _mqttService.resultStream.listen(_onResult);
    _retrySub = _mqttService.retryStream.listen(_onRetryRequested);

    if (AppConfig.hasMqttHost) {
      unawaited(_connect());
    }
  }

  @override
  void dispose() {
    _presenceSub?.cancel();
    _plateSub?.cancel();
    _resultSub?.cancel();
    _retrySub?.cancel();
    _mqttService.dispose();
    _mqttHostController.dispose();
    super.dispose();
  }

  Future<void> _connect() async {
    setState(() {
      _phase = _Phase.connecting;
      _statusText = 'Conectando al broker MQTT...';
    });
    final ok = await _mqttService.connect();
    if (!mounted) return;
    setState(() {
      if (ok) {
        _phase = _Phase.waitingPresence;
        _statusText = 'Esperando presencia de un vehiculo...';
      } else {
        _phase = _Phase.needsMqttConfig;
        _statusText = 'No se pudo conectar al broker MQTT. Revisa la IP e intenta de nuevo.';
      }
    });
  }

  void _onPresence(GaritaPresenceEvent event) {
    if (_phase != _Phase.waitingPresence) return;
    setState(() {
      _mode = event.mode;
      _phase = _Phase.waitingPlate;
      _plateText = null;
      _faceAttempt = 0;
      _statusText = 'Vehiculo detectado (${event.mode}). Esperando placa...';
    });
    unawaited(_waitForPlateThenCapture());
  }

  Future<void> _waitForPlateThenCapture() async {
    final completer = Completer<GaritaPlateEvent>();
    _pendingPlateCompleter = completer;
    final event = await completer.future.timeout(
      _plateTimeout,
      onTimeout: () => const GaritaPlateEvent(plateText: 'DESCONOCIDA', confidence: 0),
    );
    _pendingPlateCompleter = null;
    if (!mounted || _phase != _Phase.waitingPlate) return;

    if (event.plateText == 'DESCONOCIDA') {
      setState(() {
        _phase = _Phase.result;
        _resultAuthorized = false;
        _resultMessage = 'Placa no detectada';
        _statusText = 'RECHAZADO';
      });
      _scheduleReturnToWaiting();
      return;
    }

    setState(() {
      _plateText = event.plateText;
      _statusText = 'Placa ${event.plateText} detectada. Captura el rostro.';
    });
    await _runCaptureFlow();
  }

  Future<void> _runCaptureFlow() async {
    if (!mounted) return;
    setState(() {
      _phase = _Phase.capturing;
      _statusText = 'Abriendo camara para capturar el rostro...';
    });

    final selection = ParkingAppScope.of(context).selection;
    if (selection == null) {
      setState(() {
        _phase = _Phase.error;
        _statusText = 'Selecciona universidad, campus y puerta antes de usar la garita fisica.';
      });
      return;
    }

    try {
      final capturedFile = await Navigator.of(context).push<XFile>(
        MaterialPageRoute<XFile>(builder: (_) => const FaceCameraCaptureScreen()),
      );
      if (capturedFile == null) {
        if (!mounted) return;
        setState(() {
          _phase = _Phase.waitingPlate;
          _statusText = 'Captura cancelada. Esperando placa nuevamente...';
        });
        return;
      }

      final draft = await _imagePreparationService.buildDraft(
        file: capturedFile,
        label: 'Rostro garita fisica',
      );

      if (!mounted) return;
      setState(() {
        _phase = _Phase.uploading;
        _statusText = 'Subiendo evidencia de rostro...';
      });

      final imageType =
          _mode == 'entrada' ? EvidenceImageType.faceEntry : EvidenceImageType.faceExit;
      final upload = await _apiClient.uploadEvidence(
        imageType: imageType,
        plate: _plateText ?? 'PENDIENTE',
        universityId: selection.universityId,
        evidence: draft,
      );

      _mqttService.publishFaceEvidence(mode: _mode, imageId: upload.imageId);

      if (!mounted) return;
      setState(() {
        _phase = _Phase.awaitingResult;
        _statusText = 'Foto enviada. Esperando veredicto de parking-service...';
      });
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _phase = _Phase.error;
        _statusText = 'No se pudo capturar o subir el rostro. Intenta nuevamente.';
      });
    }
  }

  void _onResult(GaritaResultEvent event) {
    if (_phase != _Phase.awaitingResult) return;
    setState(() {
      _phase = _Phase.result;
      _resultAuthorized = event.authorized;
      _resultMessage = _translateReason(event.message);
      _statusText = event.authorized ? 'AUTORIZADO' : 'RECHAZADO';
    });
    _scheduleReturnToWaiting();
  }

  /// garita_controller.py pide otra foto (rechazo especificamente por
  /// FACE_NOT_DETECTED, con intentos restantes) sin esperar una nueva
  /// presencia del vehiculo. Solo se atiende mientras seguimos esperando el
  /// resultado de la foto anterior - evita reintentar por un mensaje viejo.
  void _onRetryRequested(void _) {
    if (_phase != _Phase.awaitingResult) return;
    _faceAttempt += 1;
    setState(() {
      _statusText =
          'NO SE DETECTO TU ROSTRO, reintentando ($_faceAttempt/${_maxFaceAttempts - 1})...';
    });
    unawaited(_runCaptureFlow());
  }

  void _scheduleReturnToWaiting() {
    Future.delayed(const Duration(seconds: 4), () {
      if (!mounted || _phase != _Phase.result) return;
      setState(() {
        _phase = _Phase.waitingPresence;
        _statusText = 'Esperando presencia de un vehiculo...';
        _plateText = null;
        _resultAuthorized = null;
        _resultMessage = '';
      });
    });
  }

  String _translateReason(String message) {
    const known = {
      'Payment status is not PAID': 'Pago pendiente',
      'Payment grace period expired': 'Se vencio el tiempo de gracia del pago',
      'Face verification failed': 'El rostro no coincide con el de entrada',
      'Face detection failed': 'No se detecto un rostro valido',
      'Plate does not exist': 'Placa no registrada',
      'Vehicle already inside': 'Este vehiculo ya se encuentra adentro',
      'Permission is not valid': 'Permiso de acceso no valido',
      'Liveness score too low': 'Prueba de vida insuficiente',
    };
    return known[message] ?? message;
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      appBar: AppBar(title: const Text('Garita fisica')),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Row(
                    children: [
                      Icon(
                        _mqttService.isConnected ? Icons.wifi : Icons.wifi_off,
                        color: _mqttService.isConnected ? Colors.green : Colors.red,
                      ),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          _mqttService.isConnected
                              ? 'Conectado a ${AppConfig.mqttHost}:${AppConfig.mqttPort}'
                              : 'Sin conexion MQTT',
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 24),
              if (_phase == _Phase.needsMqttConfig) ...[
                TextField(
                  controller: _mqttHostController,
                  decoration: const InputDecoration(
                    labelText: 'IP del broker MQTT',
                    border: OutlineInputBorder(),
                  ),
                ),
                const SizedBox(height: 12),
                FilledButton(
                  onPressed: () {
                    AppConfig.setMqttHost(_mqttHostController.text.trim());
                    unawaited(_connect());
                  },
                  child: const Text('Conectar'),
                ),
              ] else ...[
                if (_plateText != null)
                  Text('Placa: $_plateText', style: theme.textTheme.titleLarge),
                const SizedBox(height: 12),
                if (_phase == _Phase.result && _resultAuthorized != null)
                  Card(
                    color: _resultAuthorized!
                        ? Colors.green.withValues(alpha: 0.15)
                        : Colors.red.withValues(alpha: 0.15),
                    child: Padding(
                      padding: const EdgeInsets.all(16),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            _resultAuthorized! ? 'AUTORIZADO' : 'RECHAZADO',
                            style: theme.textTheme.headlineSmall,
                          ),
                          const SizedBox(height: 4),
                          Text(_resultMessage),
                        ],
                      ),
                    ),
                  )
                else
                  Column(
                    children: [
                      const CircularProgressIndicator(),
                      const SizedBox(height: 16),
                      Text(_statusText, textAlign: TextAlign.center),
                    ],
                  ),
              ],
              if (_phase == _Phase.error) ...[
                const SizedBox(height: 12),
                Text(_statusText, style: TextStyle(color: theme.colorScheme.error)),
                const SizedBox(height: 12),
                OutlinedButton(
                  onPressed: () => setState(() {
                    _phase = _Phase.waitingPresence;
                    _statusText = 'Esperando presencia de un vehiculo...';
                  }),
                  child: const Text('Volver a esperar'),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}
