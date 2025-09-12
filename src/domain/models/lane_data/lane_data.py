from dataclasses import dataclass


@dataclass
class LaneData:
    car_speed_data: int = 255
    car_direction_data: int = 180

    def update(self, data: dict) -> None:
        if "CAR_SPEED_DATA" in data:
            self.car_speed_data = data["CAR_SPEED_DATA"]
        if "CAR_DIRECTION_DATA" in data:
            self.car_direction_data = data["CAR_DIRECTION_DATA"]
