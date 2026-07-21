import 'dart:async';
import 'dart:convert';

import 'package:mqtt_client/mqtt_client.dart';
import 'package:mqtt_client/mqtt_server_client.dart';

import '../config/app_config.dart';

/// El celular se suscribe a los mismos topicos MQTT que ya usa el
/// ESP32/garita_controller.py (ucepark/garita/eventos) para enterarse de que
/// hay que capturar, y publica el image_id de la foto ya subida en
/// ucepark/garita/rostro_evidencia para que garita_controller.py complete el
/// flujo con la placa.
class GaritaPresenceEvent {
  const GaritaPresenceEvent({required this.mode});
  final String mode; // "entrada" o "salida"
}

/// Veredicto real que devolvio parking-service (no solo ABRIR/DENEGAR): el
/// motivo (ej. "Payment status is not PAID", "Face verification failed")
/// para mostrarlo tal cual al usuario en vez de un generico "RECHAZADO".
class GaritaResultEvent {
  const GaritaResultEvent({required this.authorized, required this.message, this.faceWarnings = const []});
  final bool authorized;
  final String message;
  final List<String> faceWarnings;
}

/// Placa que garita_controller.py termino de decidir (o "DESCONOCIDA" si se
/// agoto el tiempo buscandola). El celular espera este evento antes de
/// arrancar su propia captura de rostro: primero placa, despues rostro.
class GaritaPlateEvent {
  const GaritaPlateEvent({required this.plateText, required this.confidence});
  final String plateText;
  final double confidence;
}

class GaritaMqttService {
  GaritaMqttService();

  static const String topicPresencia = 'ucepark/garita/eventos';
  static const String topicRostroEvidencia = 'ucepark/garita/rostro_evidencia';
  static const String topicResultadoDetalle = 'ucepark/garita/resultado_detalle';
  static const String topicPlacaDetectada = 'ucepark/garita/placa_detectada';
  // garita_controller.py pide otra foto por aca cuando el rechazo es
  // especificamente por no detectar rostro y todavia quedan intentos (hasta
  // 3 en total) - sin esperar una nueva presencia del vehiculo.
  static const String topicReintentarRostro = 'ucepark/garita/reintentar_rostro';

  MqttServerClient? _client;
  final _presenceController = StreamController<GaritaPresenceEvent>.broadcast();
  // garita_controller.py publica un DENEGAR retenido al arrancar (handshake
  // con el ESP32); el consumidor debe filtrar eventos que no correspondan a
  // una espera activa.
  final _resultController = StreamController<GaritaResultEvent>.broadcast();
  final _plateController = StreamController<GaritaPlateEvent>.broadcast();
  final _retryController = StreamController<void>.broadcast();

  bool _manualDisconnect = false;
  bool _reconnecting = false;
  Timer? _reconnectTimer;

  /// Se llama cada vez que cambia isConnected (conectado <-> caido/reconectando),
  /// para que la UI pueda refrescar el icono sin depender de otro setState.
  void Function()? onConnectionChanged;

  Stream<GaritaPresenceEvent> get presenceStream => _presenceController.stream;
  Stream<GaritaResultEvent> get resultStream => _resultController.stream;
  Stream<GaritaPlateEvent> get plateStream => _plateController.stream;
  Stream<void> get retryStream => _retryController.stream;
  bool get isConnected => _client?.connectionStatus?.state == MqttConnectionState.connected;

  Future<bool> connect() async {
    if (!AppConfig.hasMqttHost) {
      return false;
    }
    _manualDisconnect = false;
    _reconnectTimer?.cancel();
    final ok = await _connectOnce();
    if (!ok) {
      _scheduleReconnect();
    }
    return ok;
  }

  Future<bool> _connectOnce() async {
    final clientId = 'garita-mobile-${DateTime.now().millisecondsSinceEpoch}';
    final client = MqttServerClient(AppConfig.mqttHost, clientId);
    client.port = AppConfig.mqttPort;
    client.keepAlivePeriod = 30;
    client.logging(on: false);
    // MIUI/Android puede cortar el socket en segundo plano; sin esto la app
    // se quedaba "sorda" a ucepark/garita/eventos hasta tocar Conectar de nuevo.
    client.onDisconnected = _handleDisconnected;
    client.setProtocolV311();

    final connMessage = MqttConnectMessage().withClientIdentifier(clientId).startClean();
    client.connectionMessage = connMessage;

    try {
      await client.connect();
    } catch (_) {
      client.disconnect();
      return false;
    }
    if (client.connectionStatus?.state != MqttConnectionState.connected) {
      return false;
    }

    _client = client;
    client.subscribe(topicPresencia, MqttQos.atMostOnce);
    client.subscribe(topicResultadoDetalle, MqttQos.atMostOnce);
    client.subscribe(topicPlacaDetectada, MqttQos.atMostOnce);
    client.subscribe(topicReintentarRostro, MqttQos.atMostOnce);
    client.updates?.listen(_onMessage);
    onConnectionChanged?.call();
    return true;
  }

  void _handleDisconnected() {
    onConnectionChanged?.call();
    if (_manualDisconnect) return;
    _scheduleReconnect();
  }

  void _scheduleReconnect() {
    if (_reconnecting || _manualDisconnect) return;
    _reconnecting = true;
    _reconnectTimer?.cancel();
    _reconnectTimer = Timer(const Duration(seconds: 3), () async {
      _reconnecting = false;
      if (_manualDisconnect) return;
      final ok = await _connectOnce();
      if (!ok) {
        _scheduleReconnect();
      }
    });
  }

  void _onMessage(List<MqttReceivedMessage<MqttMessage>> messages) {
    for (final message in messages) {
      final recMess = message.payload as MqttPublishMessage;
      final raw = MqttPublishPayload.bytesToStringAsString(recMess.payload.message);

      if (message.topic == topicPresencia) {
        try {
          final data = jsonDecode(raw) as Map<String, dynamic>;
          if (data['event'] == 'presencia') {
            final mode = (data['mode'] as String?) ?? 'entrada';
            _presenceController.add(GaritaPresenceEvent(mode: mode));
          }
        } catch (_) {
          // Mensaje no valido, se ignora.
        }
      } else if (message.topic == topicResultadoDetalle) {
        try {
          final data = jsonDecode(raw) as Map<String, dynamic>;
          _resultController.add(GaritaResultEvent(
            authorized: data['authorized'] == true,
            message: (data['message'] as String?) ?? '',
            faceWarnings: (data['face_warnings'] as List?)?.cast<String>() ?? const [],
          ));
        } catch (_) {
          // Mensaje no valido, se ignora.
        }
      } else if (message.topic == topicPlacaDetectada) {
        try {
          final data = jsonDecode(raw) as Map<String, dynamic>;
          _plateController.add(GaritaPlateEvent(
            plateText: (data['plate_text'] as String?) ?? 'DESCONOCIDA',
            confidence: (data['confidence'] as num?)?.toDouble() ?? 0.0,
          ));
        } catch (_) {
          // Mensaje no valido, se ignora.
        }
      } else if (message.topic == topicReintentarRostro) {
        _retryController.add(null);
      }
    }
  }

  void publishFaceEvidence({required String mode, required String imageId}) {
    final client = _client;
    if (client == null || client.connectionStatus?.state != MqttConnectionState.connected) {
      return;
    }
    final payload = jsonEncode({'event': 'rostro_listo', 'mode': mode, 'image_id': imageId});
    final builder = MqttClientPayloadBuilder()..addString(payload);
    client.publishMessage(topicRostroEvidencia, MqttQos.atLeastOnce, builder.payload!);
  }

  void disconnect() {
    _manualDisconnect = true;
    _reconnectTimer?.cancel();
    _client?.disconnect();
    _client = null;
  }

  void dispose() {
    disconnect();
    _presenceController.close();
    _resultController.close();
    _plateController.close();
    _retryController.close();
  }
}
