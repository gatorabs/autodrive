from dataclasses import dataclass


@dataclass
class ObjectData:
    object_person_data: int = 0
    traffic_light_data: int = 0

    def update(self, data: dict) -> None:
        if "OBJECT_PERSON_DATA" in data:
            self.object_person_data = data["OBJECT_PERSON_DATA"]
        if "TRAFFIC_LIGHT_DATA" in data:
            self.traffic_light_data = data["TRAFFIC_LIGHT_DATA"]
