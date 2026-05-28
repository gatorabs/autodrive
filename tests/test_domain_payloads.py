import unittest

from src.domain.models.data.object_data import ObjectData
from src.domain.models.data.lane_data import LaneData


class DomainPayloadTests(unittest.TestCase):
    def test_lane_data_updates_and_preserves_queue_payload_shape(self):
        lane_data = LaneData()

        lane_data.update({"CAR_SPEED_DATA": 120, "CAR_DIRECTION_DATA": 45})

        self.assertEqual(lane_data.car_speed_data, 120)
        self.assertEqual(lane_data.car_direction_data, 45)
        self.assertEqual(
            lane_data.to_payload(),
            {"CAR_SPEED_DATA": 120, "CAR_DIRECTION_DATA": 45},
        )

    def test_object_data_updates_and_preserves_queue_payload_shape(self):
        object_data = ObjectData()

        object_data.update(
            {
                "CUSTOM_OBJECT_DATA": 3,
                "CUSTOM_OBJECT_LABEL": "PLACA_LOMBADA",
                "OBJECT_PERSON_DATA": 1,
                "TRAFFIC_LIGHT_DATA": 0,
            }
        )

        self.assertEqual(object_data.custom_object_data, 3)
        self.assertEqual(object_data.custom_object_label, "PLACA_LOMBADA")
        self.assertEqual(object_data.object_person_data, 1)
        self.assertEqual(object_data.traffic_light_data, 0)
        self.assertEqual(
            object_data.to_payload(),
            {
                "OBJECT_PERSON_DATA": 1,
                "TRAFFIC_LIGHT_DATA": 0,
                "CUSTOM_OBJECT_DATA": 3,
                "CUSTOM_OBJECT_LABEL": "PLACA_LOMBADA",
            },
        )


if __name__ == "__main__":
    unittest.main()
