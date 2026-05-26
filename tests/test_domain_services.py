import unittest

from src.domain.models.lane_data.lane_data import LaneData
from src.domain.models.object_data.object_data import ObjectData
from src.domain.services.safety_service import publish_emergency_stop
from src.domain.services.traffic_light_service import (
    TRAFFIC_LIGHT_GREEN,
    TRAFFIC_LIGHT_RED,
    evaluate_state,
)


class DomainServiceTests(unittest.TestCase):
    def test_traffic_light_red_requests_stop(self):
        shared = {}
        lane = LaneData(car_speed_data=120)

        result = evaluate_state(shared, lane, TRAFFIC_LIGHT_RED)

        self.assertTrue(result.should_stop)
        self.assertEqual(result.target_speed, 0)

    def test_traffic_light_green_keeps_running_when_no_stop_state(self):
        result = evaluate_state({}, LaneData(car_speed_data=120), TRAFFIC_LIGHT_GREEN)

        self.assertFalse(result.should_stop)
        self.assertIsNone(result.target_speed)

    def test_person_detection_forces_zero_speed(self):
        shared = {}
        lane = LaneData(car_speed_data=120)
        obj = ObjectData(object_person_data=1, traffic_light_data=TRAFFIC_LIGHT_GREEN)

        updated_speed = publish_emergency_stop(obj, shared, lane, {}, now=1.0)

        self.assertEqual(updated_speed, 0)
        self.assertEqual(lane.car_speed_data, 0)
        self.assertEqual(shared["CAR_INFO"]["CAR_SPEED_DATA"], 0)


if __name__ == "__main__":
    unittest.main()
