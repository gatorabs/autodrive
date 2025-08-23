from unittest.mock import MagicMock, patch

from src.application.usecases.security_multiprocess import security_process


def test_security_process_initializes_serial_and_sets_priority():
    shared_controls = {"RUNNING": False, "SECURITY_COM": "COM1"}

    with patch("src.application.usecases.security_multiprocess.set_process_priority") as mock_prio, \
         patch("src.application.usecases.security_multiprocess.SerialCommunicator", return_value=MagicMock()) as mock_serial, \
         patch("src.application.usecases.security_multiprocess.Logger"):
        security_process(shared_controls, verbose=False)

    mock_prio.assert_called_once_with("above_normal")
    assert mock_serial.call_args.kwargs["com_port"] == "COM1"
    assert mock_serial.call_args.kwargs["open_for_receive"] is True


def test_security_process_triggers_emergency_stop_on_signal():
    shared_controls = {"RUNNING": True, "SECURITY_COM": "COM1"}
    serial_mock = MagicMock()

    def receive_side_effect():
        shared_controls["RUNNING"] = False
        return b"s"

    serial_mock.receive.side_effect = receive_side_effect

    with patch("src.application.usecases.security_multiprocess.set_process_priority"), \
         patch("src.application.usecases.security_multiprocess.SerialCommunicator", return_value=serial_mock), \
         patch("src.application.usecases.security_multiprocess.switch_serial_com", return_value=(serial_mock, "COM1")), \
         patch("src.application.usecases.security_multiprocess.time.monotonic", side_effect=[0, 0.02]), \
         patch("src.application.usecases.security_multiprocess.Logger") as mock_logger:
        security_process(shared_controls, verbose=False)

    assert shared_controls["EMERGENCY_STOP"] == 1
    mock_logger.return_value.info.assert_any_call("Emergency Stop triggered!")

