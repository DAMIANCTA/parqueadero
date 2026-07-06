import json
import uuid

from paho.mqtt import client as mqtt_client

from config import settings


class MqttRepository:
    def build_command_topic(self, university_id: str, campus_id: str, gate_id: str) -> str:
        return f"universities/{university_id}/campuses/{campus_id}/gates/{gate_id}/cmd"

    def build_status_topic(self, university_id: str, campus_id: str, gate_id: str) -> str:
        return f"universities/{university_id}/campuses/{campus_id}/gates/{gate_id}/status"

    def publish_open_command(
        self,
        university_id: str,
        campus_id: str,
        gate_id: str,
        plate: str,
        session_id: str | None,
        reason: str,
        command: str = "open",
    ) -> dict:
        topic = self.build_command_topic(
            university_id=university_id,
            campus_id=campus_id,
            gate_id=gate_id,
        )
        status_topic = self.build_status_topic(
            university_id=university_id,
            campus_id=campus_id,
            gate_id=gate_id,
        )
        payload = {
            "command": command,
            "plate": plate,
            "session_id": session_id,
            "reason": reason,
        }
        self._publish_message(topic=topic, payload=payload)

        return {
            "gate_id": gate_id,
            "command": command,
            "published": True,
            "topic": topic,
            "status_topic": status_topic,
            "payload": payload,
        }

    def publish_status(
        self,
        *,
        university_id: str,
        campus_id: str,
        gate_id: str,
        plate: str,
        barrier: str,
        device_status: str,
        reason: str,
        event_type: str,
        access_status: str,
    ) -> dict:
        topic = self.build_status_topic(
            university_id=university_id,
            campus_id=campus_id,
            gate_id=gate_id,
        )
        payload = {
            "barrier": barrier,
            "device_status": device_status,
            "university_id": university_id,
            "campus_id": campus_id,
            "gate_id": gate_id,
            "plate": plate,
            "reason": reason,
            "event_type": event_type,
            "access_status": access_status,
            "last_event": f"{event_type}:{access_status}:{reason}",
        }
        self._publish_message(topic=topic, payload=payload)

        return {
            "gate_id": gate_id,
            "published": True,
            "topic": topic,
            "payload": payload,
        }

    def _publish_message(self, *, topic: str, payload: dict) -> None:
        client = self._build_client()
        try:
            client.connect(
                host=settings.mqtt_host,
                port=settings.mqtt_port,
                keepalive=settings.mqtt_keepalive,
            )
            client.loop_start()
            publish_result = client.publish(topic, payload=json.dumps(payload), qos=settings.mqtt_qos)
            publish_result.wait_for_publish(timeout=5)
            if not publish_result.is_published():
                raise RuntimeError(f"MQTT publish not confirmed for topic {topic}")
        finally:
            try:
                client.loop_stop()
            finally:
                client.disconnect()

    def _build_client(self) -> mqtt_client.Client:
        client_id = f"iot-service-{uuid.uuid4().hex[:8]}"
        try:
            client = mqtt_client.Client(mqtt_client.CallbackAPIVersion.VERSION2, client_id=client_id)
        except AttributeError:  # pragma: no cover - compatibility with older paho versions
            client = mqtt_client.Client(client_id=client_id)

        if settings.mqtt_username:
            client.username_pw_set(settings.mqtt_username, settings.mqtt_password or "")
        return client
