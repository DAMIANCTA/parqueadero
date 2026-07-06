from repositories.mqtt_repository import MqttRepository
from schemas.iot import GateOpenRequest, GateStatusRequest


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

    def publish_gate_status(self, status: GateStatusRequest) -> dict:
        return self.repository.publish_status(
            university_id=status.university_id,
            campus_id=status.campus_id,
            gate_id=status.gate_id,
            plate=status.plate,
            barrier=status.barrier,
            device_status=status.device_status,
            reason=status.reason,
            event_type=status.event_type,
            access_status=status.access_status,
        )
