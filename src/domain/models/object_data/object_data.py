from dataclasses import dataclass


@dataclass
class ObjectData:
    custom_object_data: int = 0
    object_person_data: int = 0
    traffic_light_data: int = 0
    stop_sign_data: int = 0
    detour_sign_data: int = 0
    speed_bump_sign_data: int = 0

    def update(self, data: dict) -> None:
        if "CUSTOM_OBJECT_DATA" in data:
            self.custom_object_data = data["CUSTOM_OBJECT_DATA"]
        if "OBJECT_PERSON_DATA" in data:
            self.object_person_data = data["OBJECT_PERSON_DATA"]
        if "TRAFFIC_LIGHT_DATA" in data:
            self.traffic_light_data = data["TRAFFIC_LIGHT_DATA"]
        if "STOP_SIGN_DATA" in data:
            self.stop_sign_data = data["STOP_SIGN_DATA"]
        if "DETOUR_SIGN_DATA" in data:
            self.detour_sign_data = data["DETOUR_SIGN_DATA"]
        if "SPEED_BUMP_SIGN_DATA" in data:
            self.speed_bump_sign_data = data["SPEED_BUMP_SIGN_DATA"]
