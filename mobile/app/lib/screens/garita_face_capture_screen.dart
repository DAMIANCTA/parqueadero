import 'dart:async';
import 'dart:math' as math;

import 'package:camera/camera.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:google_mlkit_face_detection/google_mlkit_face_detection.dart';
import 'package:wakelock_plus/wakelock_plus.dart';

import '../config/app_config.dart';
import '../models/app_models.dart';
import '../models/history_entry.dart';
import '../services/api_client.dart';
import '../services/garita_mqtt_service.dart';
import '../services/image_preparation_service.dart';
import '../services/wake_screen_service.dart';
import '../state/parking_app_scope.dart';
import '../theme/ucepark_theme.dart';
import '../widgets/uce_widgets.dart';

/// Pantalla "Garita fisica": el celular se conecta al mismo broker MQTT que
/// usa garita_controller.py/el ESP32 para saber cuando hay que capturar el
/// rostro de un vehiculo que se presento en la barrera fisica (a diferencia
/// del flujo manual de Entrada/Salida, donde el operador dispara la captura
/// el mismo). Primero llega la placa que ya decidio garita_controller.py,
/// despues se captura el rostro automaticamente cuando la persona se coloca
/// bien frente a la camara (camara embebida en esta misma pantalla, sin
/// navegar a otra ruta).
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

enum _FaceAlignState { none, detectedNotAligned, aligned }

/// El resultado (rechazo o autorizacion) puede llegar del backend en
/// CUALQUIERA de estas fases: garita_controller.py puede rechazar apenas
/// detecta la placa (ej. "vehiculo ya esta adentro"), mucho antes de que el
/// celular termine de alinear+capturar+subir el rostro. Si el guard solo
/// aceptara el resultado en `awaitingResult`, ese rechazo temprano se
/// perderia y la pantalla se quedaria "cargando" para siempre.
const _activeCycle = <_Phase>{
  _Phase.waitingPlate,
  _Phase.capturing,
  _Phase.uploading,
  _Phase.awaitingResult,
};

class _GaritaFisicaScreenState extends State<GaritaFisicaScreen> {
  static const int _maxFaceAttempts = 3;
  static const Duration _plateTimeout = Duration(seconds: 14);

  static const double _alignDxDyTolerance = 0.15;
  static const double _alignMinSizeRatio = 0.30;
  static const double _alignMaxSizeRatio = 0.65;
  static const Duration _requiredAlignedDuration = Duration(milliseconds: 700);
  static const Duration _faceLossGracePeriod = Duration(milliseconds: 450);

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
  String? _lastFaceImageId;

  // Mientras se espera un vehiculo la pantalla puede apagarse sola (ahorro
  // de bateria); apenas hay algo que mostrar/hacer (placa detectada en
  // adelante) se fuerza a que se mantenga encendida. `_wakelockSyncedPhase`
  // evita llamar al canal nativo/plugin en cada rebuild si la fase no
  // cambio.
  static const _wakeScreenPhases = <_Phase>{
    _Phase.waitingPlate,
    _Phase.capturing,
    _Phase.uploading,
    _Phase.awaitingResult,
    _Phase.result,
  };
  _Phase? _wakelockSyncedPhase;

  void _syncWakelock() {
    if (_wakelockSyncedPhase == _phase) return;
    _wakelockSyncedPhase = _phase;
    if (_wakeScreenPhases.contains(_phase)) {
      unawaited(WakelockPlus.enable());
    } else {
      unawaited(WakelockPlus.disable());
    }
  }

  StreamSubscription<GaritaPresenceEvent>? _presenceSub;
  StreamSubscription<GaritaPlateEvent>? _plateSub;
  StreamSubscription<GaritaResultEvent>? _resultSub;
  StreamSubscription<void>? _retrySub;
  Completer<GaritaPlateEvent>? _pendingPlateCompleter;

  CameraController? _cameraController;
  bool _cameraReady = false;
  FaceDetector? _faceDetector;
  bool _isDetectingFace = false;
  DateTime _lastProcessedFrame = DateTime.fromMillisecondsSinceEpoch(0);
  Face? _lastFace;
  DateTime? _lastFaceSeenAt;
  bool _faceAligned = false;
  DateTime? _alignedSince;
  Timer? _countdownTimer;
  int? _countdownValue;
  bool _autoCaptureTriggered = false;

  @override
  void initState() {
    super.initState();
    _faceDetector = FaceDetector(
      options: FaceDetectorOptions(
        performanceMode: FaceDetectorMode.fast,
        enableTracking: false,
      ),
    );
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

    unawaited(_initCamera());

    if (AppConfig.hasMqttHost) {
      unawaited(_connect());
    }
  }

  @override
  void dispose() {
    // GaritaMqttService.dispose() llama a disconnect(), que dispara
    // onConnectionChanged sincronamente. En ese punto `mounted` todavia da
    // true (el Element pasa a defunct ANTES de que el framework llame a
    // dispose(), pero State._element no se limpia hasta despues), asi que el
    // guard `if (mounted)` de ese callback no evita el setState() invalido.
    // Hay que anular el callback antes de disponer el servicio.
    _mqttService.onConnectionChanged = null;
    _presenceSub?.cancel();
    _plateSub?.cancel();
    _resultSub?.cancel();
    _retrySub?.cancel();
    _mqttService.dispose();
    _mqttHostController.dispose();
    _countdownTimer?.cancel();
    _faceDetector?.close();
    _cameraController?.dispose();
    unawaited(WakelockPlus.disable());
    super.dispose();
  }

  Future<void> _initCamera() async {
    try {
      final cameras = await availableCameras();
      if (cameras.isEmpty) return;
      final selected = cameras.firstWhere(
        (camera) => camera.lensDirection == CameraLensDirection.front,
        orElse: () => cameras.first,
      );
      final controller = CameraController(
        selected,
        ResolutionPreset.medium,
        enableAudio: false,
        imageFormatGroup: defaultTargetPlatform == TargetPlatform.android
            ? ImageFormatGroup.nv21
            : ImageFormatGroup.bgra8888,
      );
      await controller.initialize();
      if (!mounted) {
        await controller.dispose();
        return;
      }
      setState(() {
        _cameraController = controller;
        _cameraReady = true;
      });
    } catch (_) {
      // Sin camara disponible: se sigue escuchando presencia igual, solo
      // no habra auto-captura (el operador tendria que usar otro flujo).
    }
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
        _statusText =
            'No se pudo conectar al broker MQTT. Revisa la IP e intenta de nuevo.';
      }
    });
  }

  void _onPresence(GaritaPresenceEvent event) {
    if (_phase != _Phase.waitingPresence) return;
    // Apenas se detecta el vehiculo se prende la pantalla ya mismo, aunque
    // se hubiera apagado sola por inactividad mientras se esperaba.
    unawaited(WakeScreenService.wakeScreenNow());
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
      onTimeout: () =>
          const GaritaPlateEvent(plateText: 'DESCONOCIDA', confidence: 0),
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
    });
    await _enterCapturingPhase();
  }

  Future<void> _enterCapturingPhase({String? message}) async {
    if (!mounted) return;
    _autoCaptureTriggered = false;
    _alignedSince = null;
    _faceAligned = false;
    _lastFace = null;
    _cancelCountdown();

    setState(() {
      _phase = _Phase.capturing;
      _statusText = message ?? 'Coloca tu rostro dentro del marco';
    });

    final controller = _cameraController;
    if (controller != null &&
        controller.value.isInitialized &&
        !controller.value.isStreamingImages) {
      await controller.startImageStream(_handleCameraImage);
    }
  }

  void _handleCameraImage(CameraImage image) {
    if (_isDetectingFace ||
        _faceDetector == null ||
        _phase != _Phase.capturing) {
      return;
    }
    final now = DateTime.now();
    if (now.difference(_lastProcessedFrame) <
        const Duration(milliseconds: 150)) {
      return;
    }
    _lastProcessedFrame = now;

    final controller = _cameraController;
    if (controller == null) return;
    final inputImage =
        _inputImageFromCameraImage(image, controller.description);
    if (inputImage == null) return;

    _isDetectingFace = true;
    _faceDetector!
        .processImage(inputImage)
        .then((faces) => _updateAlignment(
              faces,
              Size(image.width.toDouble(), image.height.toDouble()),
              controller.description.sensorOrientation,
            ))
        .catchError((_) {})
        .whenComplete(() => _isDetectingFace = false);
  }

  InputImage? _inputImageFromCameraImage(
      CameraImage image, CameraDescription description) {
    final rotation =
        InputImageRotationValue.fromRawValue(description.sensorOrientation);
    if (rotation == null) return null;

    final format = InputImageFormatValue.fromRawValue(image.format.raw);
    if (format == null) return null;
    if (format != InputImageFormat.nv21 &&
        format != InputImageFormat.bgra8888) {
      return null;
    }
    if (image.planes.length != 1) return null;

    final plane = image.planes.first;
    return InputImage.fromBytes(
      bytes: plane.bytes,
      metadata: InputImageMetadata(
        size: Size(image.width.toDouble(), image.height.toDouble()),
        rotation: rotation,
        format: format,
        bytesPerRow: plane.bytesPerRow,
      ),
    );
  }

  Size _effectiveImageSize(Size rawSize, int sensorOrientation) {
    final rotated = sensorOrientation == 90 || sensorOrientation == 270;
    return rotated ? Size(rawSize.height, rawSize.width) : rawSize;
  }

  void _updateAlignment(
      List<Face> faces, Size rawImageSize, int sensorOrientation) {
    if (!mounted || _phase != _Phase.capturing) return;
    final imageSize = _effectiveImageSize(rawImageSize, sensorOrientation);

    Face? best;
    for (final face in faces) {
      if (best == null ||
          face.boundingBox.width * face.boundingBox.height >
              best.boundingBox.width * best.boundingBox.height) {
        best = face;
      }
    }

    final now = DateTime.now();
    if (best != null) {
      _lastFaceSeenAt = now;
    } else if (_lastFaceSeenAt != null &&
        now.difference(_lastFaceSeenAt!) < _faceLossGracePeriod) {
      best = _lastFace;
    }

    var aligned = false;
    if (best != null) {
      final box = best.boundingBox;
      final centerX = box.left + box.width / 2;
      final centerY = box.top + box.height / 2;
      final dx = (centerX - imageSize.width / 2).abs() / imageSize.width;
      final dy = (centerY - imageSize.height / 2).abs() / imageSize.height;
      final faceSize = math.max(box.width, box.height);
      final imgSizeMax = math.max(imageSize.width, imageSize.height);
      final sizeRatio = faceSize / imgSizeMax;
      aligned = dx < _alignDxDyTolerance &&
          dy < _alignDxDyTolerance &&
          sizeRatio >= _alignMinSizeRatio &&
          sizeRatio <= _alignMaxSizeRatio;
    }

    if (aligned) {
      _alignedSince ??= now;
    } else {
      _alignedSince = null;
    }

    if (!mounted) return;
    setState(() {
      _lastFace = best;
      _faceAligned = aligned;
    });

    _evaluateCountdown(now);
  }

  void _evaluateCountdown(DateTime now) {
    if (_autoCaptureTriggered) return;
    if (_faceAligned && _alignedSince != null) {
      final heldFor = now.difference(_alignedSince!);
      if (heldFor >= _requiredAlignedDuration && _countdownTimer == null) {
        _startCountdown();
      }
    } else {
      _cancelCountdown();
    }
  }

  void _startCountdown() {
    if (!mounted) return;
    setState(() => _countdownValue = 2);
    _countdownTimer = Timer.periodic(const Duration(seconds: 1), (timer) {
      if (!mounted || _phase != _Phase.capturing) {
        timer.cancel();
        _countdownTimer = null;
        return;
      }
      if (!_faceAligned) {
        _cancelCountdown();
        return;
      }
      final next = (_countdownValue ?? 1) - 1;
      if (next <= 0) {
        timer.cancel();
        _countdownTimer = null;
        setState(() => _countdownValue = null);
        unawaited(_triggerAutoCapture());
        return;
      }
      setState(() => _countdownValue = next);
    });
  }

  void _cancelCountdown() {
    _countdownTimer?.cancel();
    _countdownTimer = null;
    if (_countdownValue != null) {
      if (mounted) {
        setState(() => _countdownValue = null);
      } else {
        _countdownValue = null;
      }
    }
  }

  Future<void> _triggerAutoCapture() async {
    if (_autoCaptureTriggered || _phase != _Phase.capturing) return;
    _autoCaptureTriggered = true;

    final controller = _cameraController;
    if (controller == null || !controller.value.isInitialized) {
      _autoCaptureTriggered = false;
      return;
    }

    final selection = ParkingAppScope.of(context).selection;
    if (selection == null) {
      if (!mounted) return;
      setState(() {
        _phase = _Phase.error;
        _statusText =
            'Selecciona universidad, campus y puerta antes de usar la garita fisica.';
      });
      return;
    }

    try {
      if (controller.value.isStreamingImages) {
        await controller.stopImageStream();
      }
      final photo = await controller.takePicture();
      if (!mounted || _phase != _Phase.capturing) return;

      setState(() {
        _phase = _Phase.uploading;
        _statusText = 'Subiendo evidencia de rostro...';
      });

      final draft = await _imagePreparationService.buildDraft(
        file: photo,
        label: 'Rostro garita fisica',
      );
      if (!mounted || _phase != _Phase.uploading) return;

      final imageType = _mode == 'entrada'
          ? EvidenceImageType.faceEntry
          : EvidenceImageType.faceExit;
      final upload = await _apiClient.uploadEvidence(
        imageType: imageType,
        plate: _plateText ?? 'PENDIENTE',
        universityId: selection.universityId,
        evidence: draft,
      );
      if (!mounted || _phase != _Phase.uploading) return;
      _lastFaceImageId = upload.imageId;

      _mqttService.publishFaceEvidence(mode: _mode, imageId: upload.imageId);

      setState(() {
        _phase = _Phase.awaitingResult;
        _statusText = 'Foto enviada. Esperando veredicto de parking-service...';
      });
    } catch (_) {
      if (!mounted) return;
      if (_phase == _Phase.capturing || _phase == _Phase.uploading) {
        setState(() {
          _phase = _Phase.error;
          _statusText =
              'No se pudo capturar o subir el rostro. Intenta nuevamente.';
        });
      }
    } finally {
      _autoCaptureTriggered = false;
    }
  }

  void _onResult(GaritaResultEvent event) {
    if (!_activeCycle.contains(_phase)) return;
    _abortActiveCapture();

    final translated = _translateReason(event.message);
    ParkingAppScope.of(context).addHistory(
      HistoryEntry(
        mode: _mode == 'entrada' ? ModeType.entry : ModeType.exit,
        plateText: _plateText ?? 'DESCONOCIDA',
        authorized: event.authorized,
        message: translated,
        status: event.authorized ? 'AUTHORIZED' : 'REJECTED',
        timestamp: DateTime.now(),
        faceImageId: _lastFaceImageId,
      ),
    );

    setState(() {
      _phase = _Phase.result;
      _resultAuthorized = event.authorized;
      _resultMessage = translated;
      _statusText = event.authorized ? 'AUTORIZADO' : 'RECHAZADO';
    });
    _scheduleReturnToWaiting();
  }

  /// Corta cualquier alineacion/countdown/stream de camara en curso cuando
  /// llega un resultado anticipado (ej. rechazo por "vehiculo ya adentro"
  /// publicado antes de que termine la captura+subida del rostro).
  void _abortActiveCapture() {
    _countdownTimer?.cancel();
    _countdownTimer = null;
    _countdownValue = null;
    _alignedSince = null;
    _faceAligned = false;
    _lastFace = null;
    _autoCaptureTriggered = true;
    final controller = _cameraController;
    if (controller != null && controller.value.isStreamingImages) {
      unawaited(controller.stopImageStream().catchError((_) {}));
    }
  }

  /// garita_controller.py pide otra foto (rechazo especificamente por
  /// FACE_NOT_DETECTED, con intentos restantes) sin esperar una nueva
  /// presencia del vehiculo. Solo se atiende mientras seguimos esperando el
  /// resultado de la foto anterior - evita reintentar por un mensaje viejo.
  void _onRetryRequested(void _) {
    if (_phase != _Phase.awaitingResult) return;
    _faceAttempt += 1;
    unawaited(_enterCapturingPhase(
      message:
          'No se detecto tu rostro, reintento $_faceAttempt/${_maxFaceAttempts - 1}. '
          'Coloca tu rostro dentro del marco.',
    ));
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
      'Plate not detected': 'Placa no detectada',
    };
    return known[message] ?? message;
  }

  _FaceAlignState get _alignState {
    if (_lastFace == null) return _FaceAlignState.none;
    return _faceAligned
        ? _FaceAlignState.aligned
        : _FaceAlignState.detectedNotAligned;
  }

  String _capturingHintText() {
    if (_lastFace == null) return 'Coloca tu rostro dentro del marco';
    return _faceAligned ? 'Mantente asi...' : 'Centra tu rostro en el marco';
  }

  // La camara se activa apenas se detecta el vehiculo (evento de presencia,
  // _Phase.waitingPlate) y se mantiene visible durante todo el ciclo de
  // captura. Mientras todavia no hay vehiculo (esperando presencia) o la
  // pantalla esta en config/error, no hay nada que mostrar todavia: se deja
  // en negro con el mensaje de estado (el hardware de camara sigue
  // inicializado de fondo, solo se oculta la vista previa).
  static const _cameraOffPhases = <_Phase>{
    _Phase.needsMqttConfig,
    _Phase.connecting,
    _Phase.waitingPresence,
    _Phase.error,
  };
  bool get _showCameraPreview => !_cameraOffPhases.contains(_phase);

  @override
  Widget build(BuildContext context) {
    _syncWakelock();
    return Scaffold(
      backgroundColor: Colors.black,
      body: Stack(
        fit: StackFit.expand,
        children: [
          if (_showCameraPreview && _cameraReady && _cameraController != null)
            CameraPreview(_cameraController!)
          else
            Container(color: Colors.black),
          if (_phase == _Phase.capturing)
            Positioned.fill(
              child: CustomPaint(painter: _FaceOvalPainter(state: _alignState)),
            ),
          if (_phase != _Phase.result) Center(child: _centerOverlay()),
          Positioned(
            top: 0,
            left: 0,
            right: 0,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                _buildTopBar(),
                if (_plateText != null) _buildPlateCard(),
              ],
            ),
          ),
          if (_phase == _Phase.result && _resultAuthorized != null)
            _buildResultOverlay(),
        ],
      ),
    );
  }

  /// Se dibuja como su propia capa a pantalla completa (con scrim oscuro
  /// detras) en vez de compartir el `Center` generico de los demas estados,
  /// para que quede grande y centrado sin depender de cuanto espacio le
  /// quede libre a los demas overlays (top bar, tarjeta de placa, etc.).
  Widget _buildResultOverlay() {
    return Positioned.fill(
      child: Container(
        color: Colors.black.withValues(alpha: 0.55),
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 32),
            child: UceHero(
              authorized: _resultAuthorized!,
              title:
                  _resultAuthorized! ? 'Acceso permitido' : 'Acceso denegado',
              description: _resultAuthorized!
                  ? 'Rostro verificado: la barrera se abrirá automáticamente.'
                  : 'La barrera permanece cerrada.',
              detailChip: _resultMessage.isEmpty ? null : _resultMessage,
            ),
          ),
        ),
      ),
    );
  }

  /// El chip de conexion refleja el ESP32 real (via ucepark/garita/estado,
  /// online/offline retenido - ver GaritaMqttService.espOnline), no solo si
  /// el celular sigue conectado al broker: el celular puede estar
  /// perfectamente conectado mientras la garita fisica esta apagada/sin
  /// WiFi.
  String _connectionLabel() {
    if (!_mqttService.isConnected) return 'Sin conexión MQTT';
    return switch (_mqttService.espOnline) {
      true => 'ESP32 conectado',
      false => 'ESP32 desconectado',
      null => 'Verificando ESP32…',
    };
  }

  Widget _buildTopBar() {
    return SafeArea(
      bottom: false,
      child: Padding(
        padding: const EdgeInsets.fromLTRB(8, 6, 12, 0),
        child: Row(
          children: [
            _BackButtonChip(onTap: () => Navigator.of(context).maybePop()),
            const Spacer(),
            if (_phase == _Phase.capturing) ...[
              const _LiveDotChip(),
              const SizedBox(width: 8),
            ],
            _ConnectionChip(
              connected:
                  _mqttService.isConnected && _mqttService.espOnline == true,
              label: _connectionLabel(),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildPlateCard() {
    return Padding(
      padding: const EdgeInsets.fromLTRB(12, 8, 12, 0),
      child: UceCard(
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Text(
              'Placa detectada',
              style: TextStyle(
                fontSize: 12.5,
                fontWeight: FontWeight.w800,
                color: UceParkColors.navy,
              ),
            ),
            const SizedBox(width: 8),
            Text(
              _plateText!,
              style: const TextStyle(
                fontSize: 13.5,
                fontWeight: FontWeight.w800,
                color: UceParkColors.blue,
              ),
            ),
            const Spacer(),
            const StatusBadge.blue('Verificando'),
          ],
        ),
      ),
    );
  }

  Widget? _centerOverlay() {
    if (_phase == _Phase.needsMqttConfig) {
      return _buildConfigForm();
    }
    if (_phase == _Phase.error) {
      return _buildErrorOverlay();
    }
    if (_phase == _Phase.capturing && _countdownValue != null) {
      return Text(
        '$_countdownValue',
        style: const TextStyle(
          color: Colors.white,
          fontSize: 72,
          fontWeight: FontWeight.bold,
        ),
      );
    }
    return _buildStatusBanner();
  }

  Widget _buildConfigForm() {
    return Container(
      width: 320,
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
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
        ],
      ),
    );
  }

  /// Ventana flotante para errores que NO son de conexion MQTT (ej. fallo al
  /// capturar/subir el rostro): antes se reusaba `_buildConfigForm()` para
  /// cualquier `_Phase.error`, mostrando el formulario de IP del broker sin
  /// relacion con el problema real. Aca se resalta el mensaje de error real
  /// y se ofrece reintentar la captura directamente (sin esperar un nuevo
  /// vehiculo, ya que la placa/modo siguen vigentes).
  Widget _buildErrorOverlay() {
    return Container(
      padding: const EdgeInsets.all(20),
      margin: const EdgeInsets.symmetric(horizontal: 24),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: UceParkColors.danger, width: 1.5),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Icon(Icons.error_outline,
              color: UceParkColors.danger, size: 32),
          const SizedBox(height: 10),
          Text(
            _statusText,
            style: const TextStyle(
              color: UceParkColors.dangerDark,
              fontSize: 17,
              fontWeight: FontWeight.w700,
            ),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 16),
          SizedBox(
            width: double.infinity,
            child: FilledButton(
              onPressed: () => unawaited(_enterCapturingPhase()),
              child: const Text('Reintentar'),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildStatusBanner() {
    // El resultado (AUTORIZADO/RECHAZADO) ya no pasa por aca: se dibuja
    // aparte en `_buildResultOverlay()` como capa propia a pantalla
    // completa (ver build()).
    if (_phase == _Phase.awaitingResult) {
      return const _AnalyzingPill(text: 'Analizando…');
    }

    if (_phase == _Phase.capturing) {
      final color = switch (_alignState) {
        _FaceAlignState.aligned => UceParkColors.scan,
        _FaceAlignState.detectedNotAligned => Colors.amber,
        _FaceAlignState.none => Colors.white70,
      };
      return _AnalyzingPill(text: _capturingHintText(), color: color);
    }

    return _AnalyzingPill(text: _statusText, showSpinner: false);
  }
}

class _BackButtonChip extends StatelessWidget {
  const _BackButtonChip({required this.onTap});

  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(12),
      child: Container(
        width: 36,
        height: 36,
        decoration: BoxDecoration(
          color: Colors.black.withValues(alpha: 0.45),
          borderRadius: BorderRadius.circular(12),
        ),
        child: const Icon(Icons.arrow_back, color: Colors.white, size: 20),
      ),
    );
  }
}

class _LiveDotChip extends StatelessWidget {
  const _LiveDotChip();

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      decoration: BoxDecoration(
        color: Colors.black.withValues(alpha: 0.45),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            width: 7,
            height: 7,
            decoration: const BoxDecoration(
              color: Color(0xFFFF5252),
              shape: BoxShape.circle,
            ),
          ),
          const SizedBox(width: 6),
          const Text(
            'EN VIVO',
            style: TextStyle(
              color: Colors.white,
              fontSize: 10.5,
              fontWeight: FontWeight.w800,
              letterSpacing: 0.5,
            ),
          ),
        ],
      ),
    );
  }
}

class _ConnectionChip extends StatelessWidget {
  const _ConnectionChip({required this.connected, required this.label});

  final bool connected;
  final String label;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      decoration: BoxDecoration(
        color: Colors.black.withValues(alpha: 0.45),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            connected ? Icons.wifi : Icons.wifi_off,
            color: connected ? UceParkColors.scan : Colors.redAccent,
            size: 15,
          ),
          const SizedBox(width: 6),
          ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 150),
            child: Text(
              label,
              style: const TextStyle(color: Colors.white, fontSize: 11),
              overflow: TextOverflow.ellipsis,
            ),
          ),
        ],
      ),
    );
  }
}

/// Píldora oscura translúcida usada para los estados intermedios (esperando
/// presencia/placa, alineando rostro, analizando resultado) — estilo
/// "Analizando rostro..." del mockup de referencia.
class _AnalyzingPill extends StatelessWidget {
  const _AnalyzingPill({
    required this.text,
    this.color = Colors.white70,
    this.showSpinner = true,
  });

  final String text;
  final Color color;
  final bool showSpinner;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 18),
      margin: const EdgeInsets.symmetric(horizontal: 24),
      decoration: BoxDecoration(
        color: Colors.black.withValues(alpha: 0.65),
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: color, width: 1.5),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          if (showSpinner) ...[
            SizedBox(
              width: 18,
              height: 18,
              child: CircularProgressIndicator(strokeWidth: 2.4, color: color),
            ),
            const SizedBox(width: 12),
          ],
          Flexible(
            child: Text(
              text,
              textAlign: TextAlign.center,
              style: const TextStyle(
                color: Colors.white,
                fontSize: 21,
                fontWeight: FontWeight.w800,
                height: 1.3,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _FaceOvalPainter extends CustomPainter {
  const _FaceOvalPainter({required this.state});

  final _FaceAlignState state;

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2);
    final ovalRect = Rect.fromCenter(
      center: center,
      width: size.width * 0.62,
      height: size.height * 0.62,
    );
    final bracketRect = ovalRect.inflate(18);

    final color = switch (state) {
      _FaceAlignState.aligned => UceParkColors.scan,
      _FaceAlignState.detectedNotAligned => Colors.amber,
      _FaceAlignState.none => Colors.white70,
    };

    final ovalPaint = Paint()
      ..color = color
      ..style = PaintingStyle.stroke
      ..strokeWidth = 3;
    _drawDashedOval(canvas, ovalRect, ovalPaint);

    final bracketPaint = Paint()
      ..color = color
      ..style = PaintingStyle.stroke
      ..strokeWidth = 4
      ..strokeCap = StrokeCap.round;
    _drawCornerBrackets(canvas, bracketRect, bracketPaint);
  }

  void _drawDashedOval(Canvas canvas, Rect rect, Paint paint,
      {double dashLength = 10, double gapLength = 7}) {
    final path = Path()..addOval(rect);
    for (final metric in path.computeMetrics()) {
      var distance = 0.0;
      var draw = true;
      while (distance < metric.length) {
        final next =
            math.min(distance + (draw ? dashLength : gapLength), metric.length);
        if (draw) {
          canvas.drawPath(metric.extractPath(distance, next), paint);
        }
        distance = next;
        draw = !draw;
      }
    }
  }

  void _drawCornerBrackets(Canvas canvas, Rect rect, Paint paint,
      {double armLength = 26}) {
    final tl = rect.topLeft;
    final tr = rect.topRight;
    final bl = rect.bottomLeft;
    final br = rect.bottomRight;

    canvas.drawLine(tl, tl + Offset(armLength, 0), paint);
    canvas.drawLine(tl, tl + Offset(0, armLength), paint);
    canvas.drawLine(tr, tr + Offset(-armLength, 0), paint);
    canvas.drawLine(tr, tr + Offset(0, armLength), paint);
    canvas.drawLine(bl, bl + Offset(armLength, 0), paint);
    canvas.drawLine(bl, bl + Offset(0, -armLength), paint);
    canvas.drawLine(br, br + Offset(-armLength, 0), paint);
    canvas.drawLine(br, br + Offset(0, -armLength), paint);
  }

  @override
  bool shouldRepaint(covariant _FaceOvalPainter oldDelegate) =>
      oldDelegate.state != state;
}
