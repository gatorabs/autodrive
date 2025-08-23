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

