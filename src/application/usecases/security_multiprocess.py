
from src.core.__init__sender import *

def security_process(shared_controls, verbose=True):

    set_process_priority("above_normal")
    logger = Logger("SecurityCommunicator", verbose=verbose)

    current_com = shared_controls.get("SECURITY_COM")
    serial_comm = SerialCommunicator(
        com_port=shared_controls.get("SECURITY_COM"),
        open_for_receive=True,
        logger=logger,
    )

    last_send = time.monotonic()
    send_interval = 0.01

    try:
        while shared_controls.get("RUNNING", True):
            new_com = shared_controls.get("SECURITY_COM")
            serial_comm, current_com = switch_serial_com(
                serial_comm=serial_comm,
                new_com=new_com,
                current_com=current_com,
                shared_controls=shared_controls,
                open_for_receive=True,
                logger=logger
            )

            now = time.monotonic()
            if now - last_send >= send_interval:
                try:
                    data = serial_comm.receive()
                except Exception as read_err:
                    logger.error(
                        f"Erro na leitura serial de segurança: {read_err}"
                    )
                    shared_controls["EMERGENCY_STOP"] = 0
                else:
                    if data and (b"s" in data or b"S" in data):
                        shared_controls["EMERGENCY_STOP"] = 1
                        logger.info("Emergency Stop triggered!")
                    else:
                        shared_controls["EMERGENCY_STOP"] = 0
                last_send = now

    except Exception as e:
        logger.error(f"Security Process Error: {e}")
    finally:
        serial_comm.close()
        logger.info("Comunicação serial de segurança finalizada.")