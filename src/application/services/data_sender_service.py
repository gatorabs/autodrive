from src.infrastructure.adapters.serial.serial_comm import SerialCommunicator

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

def switch_serial_com(serial_comm, new_com, current_com, shared_controls, logger):
    if new_com != current_com:
        logger.info(f"Alterando porta serial: {current_com} -> {new_com}")
        serial_comm.close()
        serial_comm = SerialCommunicator(
            com_port=new_com,
            send_data=shared_controls.get("SEND_DATA", False),
            logger=logger
        )
        return serial_comm, new_com
    return serial_comm, current_com

def publish(lane_data, obj_data, serial_comm, logger):
    payload = [
        lane_data["CAR_DIRECTION_DATA"],
        lane_data["CAR_SPEED_DATA"],
        obj_data["TRAFFIC_LIGHT_DATA"]
    ]

    try:
        serial_comm.send(payload)
    except Exception as e:
        logger.error(f"Falha ao enviar dados: {e}")
        try:
            serial_comm.reconnect()
        except Exception as re:
            logger.error(f"Reconexão falhou: {re}")