import re


def derive_subject_hint(object_path: str, person_id: str | None = None) -> str:
    if person_id:
        return _normalize(person_id)

    filename = object_path.split("/")[-1]
    stem = filename.rsplit(".", 1)[0]
    stem = re.sub(r"(?i)(?:[-_]?)(enroll|probe|compare|left|right|blink|entry|exit|selfie|face|image)$", "", stem)
    stem = re.sub(r"(?i)(?:[-_]?)(a|b|c|d)$", "", stem)
    normalized = _normalize(stem)
    return normalized or "unknown-subject"


def _normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())
