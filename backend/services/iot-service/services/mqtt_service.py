from repositories.mqtt_repository import MqttRepository
from schemas.iot import GateActionRequest, LegacyGateOpenRequest, LegacyGateStatusRequest


class MqttService:
    def __init__(self) -> None:
        self.repository = MqttRepository()

    def start_listener(self) -> None:
        self.repository.start_listener()

    def stop_listener(self) -> None:
        self.repository.stop_listener()

    def open_gate(self, gate_id: str, command: GateActionRequest) -> dict:
        return self.repository.publish_command(
            gate_id=gate_id,
            command_code="ABRIR",
            reason=command.reason,
            university_id=command.university_id,
            campus_id=command.campus_id,
            plate=command.plate,
            session_id=command.session_id,
        )

    def deny_gate(self, gate_id: str, command: GateActionRequest) -> dict:
        return self.repository.publish_command(
            gate_id=gate_id,
            command_code="DENEGAR",
            reason=command.reason,
            university_id=command.university_id,
            campus_id=command.campus_id,
            plate=command.plate,
            session_id=command.session_id,
        )

    def get_gate_status(self, gate_id: str) -> dict:
        return self.repository.get_gate_status(gate_id)

    def publish_legacy_open(self, command: LegacyGateOpenRequest) -> dict:
        result = self.open_gate(
            command.gate_id,
            GateActionRequest(
                university_id=command.university_id,
                campus_id=command.campus_id,
                plate=command.plate,
                session_id=command.session_id,
                reason=command.reason,
            ),
        )
        return {
            "gate_id": command.gate_id,
            "command": command.command,
            "published": result["published"],
            "topic": result["topic"],
            "status_topic": result["event_topic"],
            "payload": {
                "command": command.command,
                "command_code": result["command_code"],
                "plate": command.plate,
                "session_id": command.session_id,
                "reason": command.reason,
            },
        }

    def publish_legacy_status(self, status: LegacyGateStatusRequest) -> dict:
        return self.repository.publish_legacy_status(
            gate_id=status.gate_id,
            plate=status.plate,
            reason=status.reason,
            event_type=status.event_type,
            access_status=status.access_status,
        )
