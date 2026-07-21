from __future__ import annotations

from datetime import UTC, datetime
import json
import threading
import uuid

from paho.mqtt import client as mqtt_client

from config import settings


class MqttRepository:
    _lock = threading.Lock()
    _gate_states: dict[str, dict] = {}
    _listener_client: mqtt_client.Client | None = None
    _listener_started = False
    _mqtt_connected = False

    def start_listener(self) -> None:
        if not settings.iot_enabled:
            self._set_mqtt_connected(False)
            self._ensure_gate_state(settings.iot_gate_default_id)
            return

        with self._lock:
            if self.__class__._listener_started:
                return
            self.__class__._listener_started = True

        try:
            client = self._build_client(client_prefix="iot-listener")
            client.on_connect = self._on_connect
            client.on_disconnect = self._on_disconnect
            client.on_message = self._on_message
            client.connect(
                host=settings.mqtt_host,
                port=settings.mqtt_port,
                keepalive=settings.mqtt_keepalive,
            )
            client.loop_start()
            self.__class__._listener_client = client
            print(
                "iot-service mqtt_listener_started "
                f"host={settings.mqtt_host} port={settings.mqtt_port} event_topic={settings.iot_gate_event_topic}"
            )
        except Exception as exc:  # pragma: no cover - depends on broker availability
            self._set_mqtt_connected(False)
            print(
                "iot-service mqtt_listener_start_failed "
                f"host={settings.mqtt_host} port={settings.mqtt_port} error={exc}"
            )

    def stop_listener(self) -> None:
        client = self.__class__._listener_client
        if client is not None:
            try:
                client.loop_stop()
            finally:
                try:
                    client.disconnect()
                except Exception:
                    pass
        with self._lock:
            self.__class__._listener_client = None
            self.__class__._listener_started = False
            self.__class__._mqtt_connected = False

    def publish_command(
        self,
        *,
        gate_id: str,
        command_code: str,
        reason: str,
        university_id: str | None = None,
        campus_id: str | None = None,
        plate: str | None = None,
        session_id: str | None = None,
    ) -> dict:
        gate_state = self._ensure_gate_state(gate_id)
        timestamp = self._utc_now()
        if not settings.iot_enabled:
            status = "OFFLINE"
            with self._lock:
                gate_state.update(
                    {
                        "status": status,
                        "last_command": command_code,
                        "last_command_at": timestamp,
                        "last_updated_at": timestamp,
                        "last_reason": reason,
                        "university_id": university_id,
                        "campus_id": campus_id,
                        "plate": plate,
                        "session_id": session_id,
                    }
                )
            return self._command_response(
                gate_id=gate_id,
                command_code=command_code,
                published=False,
                reason=reason,
                timestamp=timestamp,
            )

        published = self._publish_text_command(settings.iot_gate_command_topic, command_code)
        status = "OPENED" if command_code == "ABRIR" else "DENIED"
        with self._lock:
            gate_state.update(
                {
                    "status": status,
                    "last_command": command_code,
                    "last_command_at": timestamp,
                    "last_updated_at": timestamp,
                    "last_reason": reason,
                    "university_id": university_id,
                    "campus_id": campus_id,
                    "plate": plate,
                    "session_id": session_id,
                }
            )
        print(
            "iot-service mqtt_command_published "
            f"gate_id={gate_id} command={command_code} published={published} "
            f"topic={settings.iot_gate_command_topic} reason={reason}"
        )
        return self._command_response(
            gate_id=gate_id,
            command_code=command_code,
            published=published,
            reason=reason,
            timestamp=timestamp,
        )

    def get_gate_status(self, gate_id: str) -> dict:
        gate_state = self._ensure_gate_state(gate_id)
        with self._lock:
            payload = {
                "gate_id": gate_id,
                "status": gate_state["status"] if self.__class__._mqtt_connected else "OFFLINE",
                "mqtt_connected": self.__class__._mqtt_connected,
                "command_topic": settings.iot_gate_command_topic,
                "event_topic": settings.iot_gate_event_topic,
                "last_event_type": gate_state.get("last_event_type"),
                "last_event_payload": gate_state.get("last_event_payload"),
                "last_presence_at": gate_state.get("last_presence_at"),
                "last_presence_mode": gate_state.get("last_presence_mode"),
                "last_command": gate_state.get("last_command"),
                "last_command_at": gate_state.get("last_command_at"),
                "last_updated_at": gate_state.get("last_updated_at"),
                "last_reason": gate_state.get("last_reason"),
                "university_id": gate_state.get("university_id"),
                "campus_id": gate_state.get("campus_id"),
                "plate": gate_state.get("plate"),
                "session_id": gate_state.get("session_id"),
            }
        return payload

    def publish_legacy_status(
        self,
        *,
        gate_id: str,
        plate: str,
        reason: str,
        event_type: str,
        access_status: str,
    ) -> dict:
        timestamp = self._utc_now()
        status = "DENIED" if access_status.lower() == "rejected" else "OPENED"
        gate_state = self._ensure_gate_state(gate_id)
        with self._lock:
            gate_state.update(
                {
                    "status": status,
                    "last_event_type": event_type,
                    "last_event_payload": access_status,
                    "last_updated_at": timestamp,
                    "last_reason": reason,
                    "plate": plate,
                }
            )
        return {
            "gate_id": gate_id,
            "published": True,
            "topic": settings.iot_gate_event_topic,
            "payload": {
                "gate_id": gate_id,
                "plate": plate,
                "reason": reason,
                "event_type": event_type,
                "access_status": access_status,
            },
        }

    def _command_response(
        self,
        *,
        gate_id: str,
        command_code: str,
        published: bool,
        reason: str,
        timestamp: str,
    ) -> dict:
        status = "OPENED" if command_code == "ABRIR" else "DENIED"
        return {
            "gate_id": gate_id,
            "status": status,
            "command": "open" if command_code == "ABRIR" else "deny",
            "command_code": command_code,
            "published": published,
            "topic": settings.iot_gate_command_topic,
            "mqtt_connected": self.__class__._mqtt_connected,
            "payload": command_code,
            "event_topic": settings.iot_gate_event_topic,
            "timestamp": timestamp,
            "reason": reason,
        }

    def _publish_text_command(self, topic: str, payload: str) -> bool:
        client = self._build_client()
        try:
            client.connect(
                host=settings.mqtt_host,
                port=settings.mqtt_port,
                keepalive=settings.mqtt_keepalive,
            )
            client.loop_start()
            publish_result = client.publish(topic, payload=payload, qos=settings.mqtt_qos)
            publish_result.wait_for_publish(timeout=5)
            published = publish_result.is_published()
            self._set_mqtt_connected(published)
            return published
        except Exception as exc:  # pragma: no cover - depends on broker/runtime
            self._set_mqtt_connected(False)
            print(f"iot-service mqtt_publish_failed topic={topic} payload={payload} error={exc}")
            return False
        finally:
            try:
                client.loop_stop()
            finally:
                try:
                    client.disconnect()
                except Exception:
                    pass

    def _on_connect(self, client, userdata, flags, reason_code, properties=None) -> None:  # pragma: no cover - runtime callback
        topic = settings.iot_gate_event_topic
        client.subscribe(topic, qos=settings.mqtt_qos)
        self._set_mqtt_connected(True)
        print(f"iot-service mqtt_listener_connected event_topic={topic} reason_code={reason_code}")

    def _on_disconnect(self, client, userdata, flags, reason_code, properties=None) -> None:  # pragma: no cover - runtime callback
        self._set_mqtt_connected(False)
        print(f"iot-service mqtt_listener_disconnected reason_code={reason_code}")

    def _on_message(self, client, userdata, message) -> None:  # pragma: no cover - runtime callback
        payload = message.payload.decode("utf-8", errors="ignore").strip()
        gate_id = settings.iot_gate_default_id
        gate_state = self._ensure_gate_state(gate_id)
        timestamp = self._utc_now()

        mode = None
        try:
            data = json.loads(payload)
        except (ValueError, TypeError):
            data = None

        if isinstance(data, dict) and data.get("event") == "presencia":
            event_type = "PRESENCE_DETECTED"
            mode = data.get("mode")
        elif payload.upper() == "PRESENCIA":
            event_type = "PRESENCE_DETECTED"
        else:
            event_type = "EVENT_RECEIVED"

        status = "PRESENCE_DETECTED" if event_type == "PRESENCE_DETECTED" else gate_state["status"]
        with self._lock:
            gate_state.update(
                {
                    "status": status,
                    "last_event_type": event_type,
                    "last_event_payload": payload,
                    "last_updated_at": timestamp,
                }
            )
            if event_type == "PRESENCE_DETECTED":
                gate_state["last_presence_at"] = timestamp
                if mode is not None:
                    gate_state["last_presence_mode"] = mode
        print(
            "iot-service mqtt_event_received "
            f"gate_id={gate_id} topic={message.topic} payload={payload} event_type={event_type} mode={mode}"
        )

    def _ensure_gate_state(self, gate_id: str) -> dict:
        with self._lock:
            if gate_id not in self.__class__._gate_states:
                self.__class__._gate_states[gate_id] = {
                    "status": "IDLE" if self.__class__._mqtt_connected else "OFFLINE",
                    "last_event_type": None,
                    "last_event_payload": None,
                    "last_presence_at": None,
                    "last_presence_mode": None,
                    "last_command": None,
                    "last_command_at": None,
                    "last_updated_at": None,
                    "last_reason": None,
                    "university_id": None,
                    "campus_id": None,
                    "plate": None,
                    "session_id": None,
                }
            return self.__class__._gate_states[gate_id]

    def _set_mqtt_connected(self, connected: bool) -> None:
        with self._lock:
            self.__class__._mqtt_connected = connected
            for gate_state in self.__class__._gate_states.values():
                if connected and gate_state["status"] == "OFFLINE":
                    gate_state["status"] = "IDLE"
                elif not connected:
                    gate_state["status"] = "OFFLINE"

    def _build_client(self, client_prefix: str = "iot-service") -> mqtt_client.Client:
        client_id = f"{client_prefix}-{uuid.uuid4().hex[:8]}"
        try:
            client = mqtt_client.Client(mqtt_client.CallbackAPIVersion.VERSION2, client_id=client_id)
        except AttributeError:  # pragma: no cover - compatibility with older paho versions
            client = mqtt_client.Client(client_id=client_id)
        if settings.mqtt_username:
            client.username_pw_set(settings.mqtt_username, settings.mqtt_password or "")
        return client

    @staticmethod
    def _utc_now() -> str:
        return datetime.now(UTC).isoformat()
