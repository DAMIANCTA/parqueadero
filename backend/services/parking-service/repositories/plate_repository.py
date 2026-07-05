class PlateRepository:
    def normalize_and_validate(self, plate_text: str, confidence_plate: float, min_confidence: float) -> str:
        normalized_plate = plate_text.strip().upper().replace(" ", "")
        if confidence_plate < min_confidence:
            raise ValueError("Plate confidence too low")
        return normalized_plate
