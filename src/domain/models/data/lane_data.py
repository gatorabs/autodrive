from dataclasses import dataclass


CAR_SPEED_DATA = "CAR_SPEED_DATA"
CAR_DIRECTION_DATA = "CAR_DIRECTION_DATA"


@dataclass
class LaneData:
    car_speed_data: int = 255
    car_direction_data: int = 180

    def update(self, data: dict) -> None:
        if CAR_SPEED_DATA in data:
            self.car_speed_data = data[CAR_SPEED_DATA]
        if CAR_DIRECTION_DATA in data:
            self.car_direction_data = data[CAR_DIRECTION_DATA]

    def to_payload(self) -> dict:
        return {
            CAR_SPEED_DATA: self.car_speed_data,
            CAR_DIRECTION_DATA: self.car_direction_data,
        }
