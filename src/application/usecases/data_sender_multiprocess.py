from src.core.__init__sender import *

def data_sender_process(lane_queue,
                        object_queue,
                        shared_controls,
                        tk_controls,
                        verbose=True):

    set_process_priority("high")
    logger = Logger("SerialCommunicator", verbose=verbose)
    current_com = shared_controls.get("SENDER_COM")

    serial_comm = SerialCommunicator(
        com_port=current_com,
        send_data=shared_controls.get("SEND_DATA", False),
        logger=logger
    )

    lane_data = {"CAR_SPEED_DATA": 255, "CAR_DIRECTION_DATA": 180}
    obj_data  = {"OBJECT_PERSON_DATA": 0, "TRAFFIC_LIGHT_DATA": 0}

    send_interval = 0.01
    last_send = time.monotonic()

    try:
        while shared_controls.get("RUNNING", True):
            new_com = shared_controls.get("SENDER_COM")
            serial_comm, current_com = switch_serial_com(
                serial_comm=serial_comm,
                new_com=new_com,
                current_com=current_com,
                shared_controls=shared_controls,
                logger=logger
            )

            now = time.monotonic()
            remaining = send_interval - (now - last_send)

            if remaining < 0:
                remaining = 0

            try:
                new_lane = lane_queue.get(timeout=remaining)
                lane_data.update(new_lane)
            except Empty:
                pass

            if shared_controls.get("MANUAL_MD", False):
                obj_data["OBJECT_PERSON_DATA"] = 0
                obj_data["TRAFFIC_LIGHT_DATA"] = 1
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

            publish_emergency_stop(obj_data=obj_data,
                                   shared_controls=shared_controls,
                                   lane_data=lane_data)

            publish(obj_data=obj_data,
                    lane_data=lane_data,
                    serial_comm=serial_comm,
                    logger=logger,
                    verbose=tk_controls.get("SEND_LOGS"))

            last_send = now


    except Exception as e:
        logger.error(f"Erro inesperado no loop: {e}")
    finally:
        serial_comm.close()
        logger.warning("Comunicação serial encerrada.")
