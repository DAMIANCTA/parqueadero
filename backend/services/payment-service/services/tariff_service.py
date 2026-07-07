from datetime import datetime
import math

from config import settings


class TariffService:
    def calculate_amount(self, entry_time: datetime, current_time: datetime | None = None) -> float:
        current = current_time or datetime.utcnow().astimezone()
        duration_hours = max((current - entry_time).total_seconds() / 3600, 0)
        billed_hours = max(math.ceil(duration_hours), 1)
        if billed_hours <= 1:
            return settings.fixed_first_hour_amount
        return settings.fixed_first_hour_amount + (billed_hours - 1) * settings.additional_hour_amount

    def calculate_duration_minutes(self, entry_time: datetime, current_time: datetime | None = None) -> int:
        current = current_time or datetime.utcnow().astimezone()
        seconds = max((current - entry_time).total_seconds(), 0)
        return math.ceil(seconds / 60)
