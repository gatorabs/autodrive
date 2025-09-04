import time

from src.infrastructure.adapters.serial.serial_comm import SerialCommunicator
from queue import Empty

def publish_emergency_stop(obj_data, shared_controls, lane_data):
    if (
        obj_data.get("OBJECT_PERSON_DATA", 0) == 1
        or shared_controls.get("EMERGENCY_STOP", 0) == 1
        or obj_data.get("TRAFFIC_LIGHT_DATA", 0) == 0
    ):
        lane_data["CAR_SPEED_DATA"] = 0
        car_info = shared_controls.get("CAR_INFO", {})
        car_info["CAR_SPEED_DATA"] = 0
        shared_controls["CAR_INFO"] = car_info

def switch_serial_com(serial_comm, new_com, current_com, shared_controls, open_for_receive, logger):
    if new_com != current_com:
        logger.info(f"Alterando porta serial: {current_com} -> {new_com}")
        serial_comm.close()
        serial_comm = SerialCommunicator(
            com_port=new_com,
            send_data=shared_controls.get("SEND_DATA", True),
            open_for_receive=open_for_receive,
            logger=logger
        )
        return serial_comm, new_com
    return serial_comm, current_com

def handle_object_queue(manual_md, object_queue, obj_data):
    if manual_md:
        obj_data["OBJECT_PERSON_DATA"] = 0
        obj_data["TRAFFIC_LIGHT_DATA"] = 2
        while not object_queue.empty():
            try:
                object_queue.get_nowait()
            except Empty:
                break
    else:
        try:
            new_obj = object_queue.get_nowait()
            obj_data.update(new_obj)
        except Empty:
            pass

def publish(lane_data, obj_data, serial_comm, logger, current_com, verbose):
    payload = [
        lane_data["CAR_DIRECTION_DATA"],
        lane_data["CAR_SPEED_DATA"],
        obj_data["TRAFFIC_LIGHT_DATA"]
    ]

    if not ensure_serial_connection(serial_comm, current_com, logger):
        return

    try:
        serial_comm.send(payload, verbose)
    except Exception as e:
        logger.error(f"Falha ao enviar dados: {e}")
        serial_comm.close()

def ensure_serial_connection(serial_comm, current_com, logger, cooldown=8.0):
    if not hasattr(serial_comm, "_warn_unavailable"):
        serial_comm._warn_unavailable = False
    if not hasattr(serial_comm, "_last_reconnect_try"):
        serial_comm._last_reconnect_try = 0.0

    def is_open():
        port = getattr(serial_comm, "serial_port", None)
        try:
            return bool(port) and getattr(port, "is_open", False)
        except Exception:
            return False

    if is_open():
        serial_comm._warn_unavailable = False
        return True

    try:
        available = set(serial_comm.list_available_ports())
    except Exception as exc:
        if not serial_comm._warn_unavailable:
            logger.warning(f"Não foi possível listar portas ({exc}); não tentarei reconectar.")
            serial_comm._warn_unavailable = True
        return False

    if current_com not in available:
        if not serial_comm._warn_unavailable:
            logger.warning(f"Porta {current_com} indisponível; envio será pulado.")
            serial_comm._warn_unavailable = True
        return False

    now = time.monotonic()
    if now - serial_comm._last_reconnect_try < cooldown:
        return False
    serial_comm._last_reconnect_try = now

    try:
        logger.info(f"Reconectando em {current_com}")
        serial_comm.reconnect()
    except Exception as exc:
        logger.error(f"Reconexão falhou em {current_com}: {exc}")

    if is_open():
        serial_comm._warn_unavailable = False
        return True

    if not serial_comm._warn_unavailable:
        logger.warning(f"Falha ao abrir {current_com}; envio será pulado.")
        serial_comm._warn_unavailable = True
    return False
