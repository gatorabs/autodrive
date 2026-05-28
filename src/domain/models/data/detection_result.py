from dataclasses import dataclass, field

from src.domain.constants.object_detection_constants import CUSTOM_OBJECT_PRIORITY
from src.domain.services.traffic_light_service import TRAFFIC_LIGHT_GREEN

from .object_data import ObjectData


@dataclass(frozen=True)
class DetectionResult:
    person_detected: bool = False
    traffic_light_state: int = TRAFFIC_LIGHT_GREEN
    custom_labels: frozenset[str] = field(default_factory=frozenset)

    @classmethod
    def from_labels(
        cls,
        *,
        person_detected: bool,
        traffic_light_state: int,
        custom_labels,
    ):
        return cls(
            person_detected=person_detected,
            traffic_light_state=traffic_light_state,
            custom_labels=frozenset(custom_labels or ()),
        )

    def to_object_data(self) -> ObjectData:
        custom_label = ""
        custom_value = 0
        for label, code in CUSTOM_OBJECT_PRIORITY:
            if label in self.custom_labels:
                custom_label = label
                custom_value = code
                break

        return ObjectData(
            custom_object_data=custom_value,
            custom_object_label=custom_label,
            object_person_data=1 if self.person_detected else 0,
            traffic_light_data=self.traffic_light_state,
        )
