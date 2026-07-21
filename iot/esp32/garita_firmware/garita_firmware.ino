#include <WiFi.h>
#include <PubSubClient.h>
#include <ESP32Servo.h>
#include <WiFiManager.h> // Librería WiFiManager de tzapu
#include <Preferences.h>  // Para guardar configuración en memoria flash

// Firmware de la garita física: agrega alternancia de modo entrada/salida
// (un solo ESP32 haciendo de las dos garitas) y publica la presencia como
// JSON a garita_controller.py / iot-service en los tópicos ucepark/garita/*.

// --- Pines ---
const int pinTrig = 27;
const int pinEcho = 34;
const int ledVerde = 32;
const int ledRojo = 25;
const int ledAmari = 14;
const int pinServo = 12;

// --- Configuración de Red y MQTT ---
char mqtt_server[40] = "192.168.1.50"; // Valor por defecto
bool shouldSaveConfig = false;

WiFiClient espClient;
PubSubClient client(espClient);
Servo miBarrera;
Preferences preferences;

// --- Tópicos MQTT (coinciden con iot-service/config.py de parking-service) ---
const char* TOPIC_PRESENCIA = "ucepark/garita/eventos";
const char* TOPIC_COMANDOS = "ucepark/garita/comandos";

// --- Variables de Estado ---
bool analizando = false;
unsigned long ultimoComandoTiempo = 0;
const unsigned long cooldownTiempo = 5000; // Cooldown de 5 segundos para reactivación
bool scriptConnectedOnce = false;          // Indica si el script de Python ya se sincronizó

// --- Modo entrada/salida (persistido en Preferences) ---
String modoActual = "entrada"; // "entrada" o "salida"

// Variables para control de clicks del botón BOOT
int buttonPressCount = 0;
unsigned long lastButtonPressTime = 0;
bool lastButtonState = HIGH;

void callback(char* topic, byte* payload, unsigned int length);

// Callback de WiFiManager para indicar que se debe guardar la configuración
void saveConfigCallback() {
  Serial.println("Nueva configuración detectada. Se guardará al conectar...");
  shouldSaveConfig = true;
}

void alternarModo() {
  modoActual = (modoActual == "entrada") ? "salida" : "entrada";
  preferences.begin("garita-config", false);
  preferences.putString("modo", modoActual);
  preferences.end();

  Serial.print("Modo cambiado a: ");
  Serial.println(modoActual);

  // Feedback: 1 parpadeo amarillo = entrada, 2 parpadeos = salida
  int parpadeos = (modoActual == "entrada") ? 1 : 2;
  for (int i = 0; i < parpadeos; i++) {
    digitalWrite(ledAmari, HIGH);
    delay(200);
    digitalWrite(ledAmari, LOW);
    delay(200);
  }
}

// Función no bloqueante para: (1) click corto = alterna modo entrada/salida,
// (2) triple-click en <1.5s = reset físico de WiFi/MQTT.
void checkBootButton() {
  bool currentButtonState = digitalRead(0);

  if (currentButtonState == LOW && lastButtonState == HIGH) {
    delay(50); // Debounce
    if (digitalRead(0) == LOW) {
      buttonPressCount++;
      lastButtonPressTime = millis();
      Serial.print("Presión de BOOT detectada: ");
      Serial.print(buttonPressCount);
      Serial.println("/3");

      digitalWrite(ledAmari, HIGH);
      delay(100);
      digitalWrite(ledAmari, LOW);

      while (digitalRead(0) == LOW) {
        delay(10);
      }
    }
  }
  lastButtonState = currentButtonState;

  // Ventana de 1.5s cerrada sin llegar a triple-click: decide la accion.
  if (buttonPressCount > 0 && (millis() - lastButtonPressTime > 1500)) {
    if (buttonPressCount == 1) {
      alternarModo();
    }
    // count == 2: se ignora (evita alternar modo por doble-click accidental
    // camino a un triple-click que no se completo).
    Serial.println("Tiempo de espera agotado. Reiniciando contador de presiones.");
    buttonPressCount = 0;
  }

  if (buttonPressCount >= 3) {
    Serial.println("[RESET] Boton BOOT presionado 3 veces. Restableciendo WiFi y MQTT...");

    for (int i = 0; i < 15; i++) {
      digitalWrite(ledVerde, HIGH);
      digitalWrite(ledAmari, LOW);
      delay(80);
      digitalWrite(ledVerde, LOW);
      digitalWrite(ledAmari, HIGH);
      delay(80);
    }
    digitalWrite(ledAmari, LOW);

    WiFi.disconnect(true, true);
    delay(200);

    WiFiManager wm;
    wm.resetSettings();

    preferences.begin("garita-config", false);
    preferences.clear();
    preferences.end();

    Serial.println("Configuracion borrada por completo. Reiniciando...");
    ESP.restart();
  }
}

void setup() {
  Serial.begin(115200);
  pinMode(ledVerde, OUTPUT); pinMode(ledRojo, OUTPUT); pinMode(ledAmari, OUTPUT);
  pinMode(pinTrig, OUTPUT); pinMode(pinEcho, INPUT);
  miBarrera.attach(pinServo);

  pinMode(0, INPUT_PULLUP);

  digitalWrite(ledAmari, LOW);
  digitalWrite(ledVerde, LOW);
  digitalWrite(ledRojo, LOW);

  preferences.begin("garita-config", false);
  String saved_mqtt = preferences.getString("mqtt_server", "192.168.1.50");
  saved_mqtt.toCharArray(mqtt_server, 40);
  modoActual = preferences.getString("modo", "entrada");
  Serial.print("IP de MQTT Broker cargada de memoria: ");
  Serial.println(mqtt_server);
  Serial.print("Modo cargado de memoria: ");
  Serial.println(modoActual);
  preferences.end();

  WiFiManager wm;
  wm.setSaveConfigCallback(saveConfigCallback);

  WiFiManagerParameter custom_mqtt_server("server", "MQTT Broker IP", mqtt_server, 40);
  wm.addParameter(&custom_mqtt_server);

  Serial.println("Fase 1: Conectando a WiFi (Parpadeando Amarillo)...");
  wm.setConfigPortalBlocking(false);
  wm.autoConnect("Garita-Config");

  unsigned long lastBlink = 0;
  bool blinkState = false;

  while (WiFi.status() != WL_CONNECTED) {
    wm.process();
    checkBootButton();

    if (millis() - lastBlink > 400) {
      lastBlink = millis();
      blinkState = !blinkState;
      digitalWrite(ledAmari, blinkState ? HIGH : LOW);
    }
    delay(10);
  }

  digitalWrite(ledAmari, LOW);
  digitalWrite(ledVerde, HIGH);
  delay(1500);
  digitalWrite(ledVerde, LOW);

  if (shouldSaveConfig) {
    preferences.begin("garita-config", false);
    String new_mqtt = String(custom_mqtt_server.getValue());
    new_mqtt.trim();
    if (new_mqtt.length() > 0) {
      new_mqtt.toCharArray(mqtt_server, 40);
      preferences.putString("mqtt_server", new_mqtt);
      Serial.print("Nueva IP de MQTT guardada en memoria: ");
      Serial.println(mqtt_server);
    }
    preferences.end();
  }

  Serial.println("WiFi conectado exitosamente!");
  Serial.print("Direccion IP del ESP32: ");
  Serial.println(WiFi.localIP());

  client.setServer(mqtt_server, 1883);
  client.setCallback(callback);
}

void callback(char* topic, byte* payload, unsigned int length) {
  String cmd = "";
  for (unsigned int i = 0; i < length; i++) cmd += (char)payload[i];

  Serial.print("Comando recibido: ");
  Serial.println(cmd);

  if (!scriptConnectedOnce) {
    scriptConnectedOnce = true;
    digitalWrite(ledAmari, LOW);
    digitalWrite(ledVerde, HIGH);
    delay(2000);
    digitalWrite(ledVerde, LOW);

    digitalWrite(ledRojo, HIGH);
    Serial.println("[FASE FINAL COMPLETADA] Script Python conectado. Sistema listo.");
    return;
  }

  if (cmd == "ABRIR") {
    digitalWrite(ledAmari, LOW);
    digitalWrite(ledVerde, HIGH);
    miBarrera.write(90);
    delay(4000);
    miBarrera.write(0);
    digitalWrite(ledVerde, LOW);
    digitalWrite(ledRojo, HIGH);
    analizando = false;
    ultimoComandoTiempo = millis();
  } else if (cmd == "DENEGAR") {
    digitalWrite(ledAmari, LOW);
    digitalWrite(ledRojo, HIGH);
    analizando = false;
    ultimoComandoTiempo = millis();
  }
}

void loop() {
  checkBootButton();

  if (!client.connected()) {
    digitalWrite(ledRojo, HIGH);
    digitalWrite(ledAmari, LOW);
    digitalWrite(ledVerde, LOW);

    while (!client.connected()) {
      checkBootButton();

      Serial.print("Intentando conexion MQTT a ");
      Serial.print(mqtt_server);
      Serial.println("...");

      if (client.connect("Garita01")) {
        client.subscribe(TOPIC_COMANDOS);
        Serial.println("Conectado al Broker MQTT.");

        digitalWrite(ledRojo, LOW);
        for (int i = 0; i < 2; i++) {
          digitalWrite(ledVerde, HIGH); delay(250);
          digitalWrite(ledVerde, LOW); delay(250);
        }

        if (!scriptConnectedOnce) {
          digitalWrite(ledAmari, HIGH);
          Serial.println("Fase 3: Esperando inicio de script Python (Amarillo encendido)...");
        } else {
          digitalWrite(ledRojo, HIGH);
        }
      } else {
        for (int i = 0; i < 200; i++) {
          checkBootButton();
          delay(10);
        }
      }
    }
  }

  client.loop();

  if (scriptConnectedOnce) {
    if (!analizando && (millis() - ultimoComandoTiempo > cooldownTiempo)) {
      digitalWrite(pinTrig, HIGH); delayMicroseconds(10); digitalWrite(pinTrig, LOW);
      long dist = pulseIn(pinEcho, HIGH) * 0.034 / 2;

      if (dist > 0 && dist < 20) {
        analizando = true;
        digitalWrite(ledRojo, LOW);
        digitalWrite(ledAmari, HIGH);
        String payload = "{\"event\":\"presencia\",\"mode\":\"" + modoActual + "\"}";
        client.publish(TOPIC_PRESENCIA, payload.c_str());
        Serial.print("Vehiculo detectado. Enviando presencia (modo=");
        Serial.print(modoActual);
        Serial.println(") a MQTT...");
      }
    }
  }
}
