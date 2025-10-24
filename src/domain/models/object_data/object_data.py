from dataclasses import dataclass


@dataclass
class ObjectData:
    custom_object_data: int = 0
    object_person_data: int = 0
    traffic_light_data: int = 2
    custom_object_label: str = ""

    def update(self, data: dict) -> None:
        if "CUSTOM_OBJECT_DATA" in data:
            self.custom_object_data = data["CUSTOM_OBJECT_DATA"]
        if "CUSTOM_OBJECT_LABEL" in data:
            self.custom_object_label = data["CUSTOM_OBJECT_LABEL"] or ""
        if "OBJECT_PERSON_DATA" in data:
            self.object_person_data = data["OBJECT_PERSON_DATA"]
        if "TRAFFIC_LIGHT_DATA" in data:
            self.traffic_light_data = data["TRAFFIC_LIGHT_DATA"]
