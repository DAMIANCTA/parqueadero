from repositories.mqtt_repository import MqttRepository
from schemas.iot import GateOpenRequest


class MqttService:
    def __init__(self) -> None:
        self.repository = MqttRepository()

    def publish_gate_open(self, command: GateOpenRequest) -> dict:
        return self.repository.publish_open_command(
            university_id=command.university_id,
            campus_id=command.campus_id,
            gate_id=command.gate_id,
            plate=command.plate,
            session_id=command.session_id,
            reason=command.reason,
            command=command.command,
        )
