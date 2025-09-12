from src.infrastructure.constants.ui_constants.file_constants import (
    CALIBRATION_FILE,
    get_profile_calibration_file,
)


def test_profile_1_uses_dedicated_file():
    profile1 = get_profile_calibration_file(1)
    profile2 = get_profile_calibration_file(2)
    assert profile1.endswith("calibration_profile_1.json")
    assert profile2.endswith("calibration_profile_2.json")
    assert profile1 != CALIBRATION_FILE

