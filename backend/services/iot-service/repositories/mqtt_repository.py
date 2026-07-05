import json

from paho.mqtt import publish

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
        auth = None
        if settings.mqtt_username:
            auth = {
                "username": settings.mqtt_username,
                "password": settings.mqtt_password or "",
            }

        publish.single(
            topic,
            payload=json.dumps(payload),
            hostname=settings.mqtt_host,
            port=settings.mqtt_port,
            qos=settings.mqtt_qos,
            keepalive=settings.mqtt_keepalive,
            auth=auth,
        )

        return {
            "gate_id": gate_id,
            "command": command,
            "published": True,
            "topic": topic,
            "status_topic": status_topic,
            "payload": payload,
        }
