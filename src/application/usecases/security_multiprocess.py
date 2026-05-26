
import time
from typing import Callable

from src.application.ports import LoggerPort, SerialSender
from src.infrastructure.services.data_sender_service import change_serial_port

def security_process(
    shared_controls,
    logger_factory: Callable[..., LoggerPort],
    serial_communicator_factory: Callable[..., SerialSender],
    priority_setter: Callable[[str], None],
    verbose=True,
):

    priority_setter("above_normal")
    logger = logger_factory("SecurityCommunicator", verbose=verbose)

    current_com = shared_controls.security_com
    serial_comm = serial_communicator_factory(
        com_port=shared_controls.security_com,
        open_for_receive=True,
        logger=logger,
    )

    last_send = time.monotonic()
    send_interval = 0.01

    try:
        while shared_controls.is_running():
            new_com = shared_controls.security_com
            current_com = change_serial_port(
                new_com=new_com,
                current_com=current_com,
                serial_comm=serial_comm,
                shared_controls=shared_controls,
                logger=logger,
                open_for_receive=True,
            )

            now = time.monotonic()
            if now - last_send >= send_interval:
                try:
                    data = serial_comm.receive()
                except Exception as read_err:
                    logger.error(
                        f"Erro na leitura serial de segurança: {read_err}"
                    )
                    shared_controls.emergency_stop = 0
                else:
                    if data and (b"s" in data or b"S" in data):
                        shared_controls.emergency_stop = 1
                        logger.info("Emergency Stop triggered!")
                    else:
                        shared_controls.emergency_stop = 0
                last_send = now

    except Exception as e:
        logger.error(f"Security Process Error: {e}")
    finally:
        serial_comm.close()
        logger.info("Comunicação serial de segurança finalizada.")
