from src.core.__init__sender import *

def data_sender_process(lane_queue,
                        object_queue,
                        shared_controls,
                        tk_controls,
                        verbose=True):

    set_process_priority("high")
    logger = Logger("SerialCommunicator", verbose=verbose)

    serial_comm = SerialCommunicator(
        com_port=shared_controls.get("SENDER_COM"),
        send_data=shared_controls.get("SEND_DATA", False),
        logger=logger
    )

    lane_data = {"CAR_SPEED_DATA": 255, "CAR_DIRECTION_DATA": 180}
    obj_data  = {"OBJECT_PERSON_DATA": 0, "TRAFFIC_LIGHT_DATA": 0}

    send_interval = 0.01
    last_send = time.monotonic()

    try:
        while shared_controls.get("RUNNING", True):
            logger.verbose = tk_controls.get("SEND_LOGS")

            now = time.monotonic()
            remaining = send_interval - (now - last_send)

            if remaining < 0:
                remaining = 0

            try:
                new_lane = lane_queue.get(timeout=remaining)
                lane_data.update(new_lane)
            except Empty:
                pass

            try:
                new_obj = object_queue.get_nowait()
                obj_data.update(new_obj)
            except Empty:
                pass

            if (
                obj_data.get("OBJECT_PERSON_DATA", 0) == 1
                or shared_controls.get("EMERGENCY_STOP", 0) == 1
                or obj_data.get("TRAFFIC_LIGHT_DATA", 0) == 0
            ):
                lane_data["CAR_SPEED_DATA"] = 0
                car_info = shared_controls.get("CAR_INFO", {})
                car_info["CAR_SPEED_DATA"] = 0
                shared_controls["CAR_INFO"] = car_info

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
            last_send = now


    except Exception as e:
        logger.error(f"Erro inesperado no loop: {e}")
    finally:
        serial_comm.close()
        logger.warning("Comunicação serial encerrada.")
