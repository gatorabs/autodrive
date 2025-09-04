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

def publish(lane_data, obj_data, serial_comm, logger, verbose):
    payload = [
        lane_data["CAR_DIRECTION_DATA"],
        lane_data["CAR_SPEED_DATA"],
        obj_data["TRAFFIC_LIGHT_DATA"]
    ]

    if not serial_comm.ensure_connection():
        return

    try:
        serial_comm.send(payload, verbose)
    except Exception as e:
        logger.error(f"Falha ao enviar dados: {e}")
        serial_comm.close()

def change_serial_port(
    new_com,
    current_com,
    serial_comm,
    shared_controls,
    logger=None,
    open_for_receive=False,
):
    if not new_com or new_com == current_com:
        return current_com

    serial_comm.change_port(
        new_port=new_com,
        send_data=shared_controls.get("SEND_DATA", False),
        open_for_receive=open_for_receive,
    )
    if logger:
        logger.info(f"Porta serial alterada: {current_com} -> {new_com}")
    return new_com

