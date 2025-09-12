from dataclasses import dataclass


@dataclass
class LaneData:
    """Data packet for lane-related telemetry."""
    car_speed_data: int = 255
    car_direction_data: int = 180

    def update(self, data: dict) -> None:
        if "CAR_SPEED_DATA" in data:
            self.car_speed_data = data["CAR_SPEED_DATA"]
        if "CAR_DIRECTION_DATA" in data:
            self.car_direction_data = data["CAR_DIRECTION_DATA"]


@dataclass
class ObjectData:
    """Data packet for object detection telemetry."""
    object_person_data: int = 0
    traffic_light_data: int = 0

    def update(self, data: dict) -> None:
        if "OBJECT_PERSON_DATA" in data:
            self.object_person_data = data["OBJECT_PERSON_DATA"]
        if "TRAFFIC_LIGHT_DATA" in data:
            self.traffic_light_data = data["TRAFFIC_LIGHT_DATA"]
