from src.core.__init__sender import *

def data_sender_process(lane_queue,
                        object_queue,
                        shared_controls,
                        verbose=True):

    set_process_priority("high")
    logger = Logger("SerialCommunicator", verbose=verbose)

    serial_comm = SerialCommunicator(
        com_port=shared_controls.get("SENDER_COM"),
        send_data=shared_controls.get("SEND_DATA", False),
        logger=logger
    )

    lane_data = {"speed": 255, "direction": 180}
    obj_data  = {"person": 0, "semaforo": 0}

    send_interval = 0.01
    last_send = time.monotonic()

    try:
        while shared_controls.get("RUNNING", True):
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
                obj_data.get("person", 0) == 1
                or shared_controls.get("EMERGENCY_STOP", 0) == 1
                or obj_data.get("semaforo", 0) == 0
            ):
                lane_data["speed"] = 0
                car_info = shared_controls.get("car_info", {})
                car_info["speed"] = 0
                shared_controls["car_info"] = car_info

            now = time.monotonic()
            if now - last_send >= send_interval:
                payload = [
                    lane_data["direction"],
                    lane_data["speed"],
                    obj_data["semaforo"]
                ]
                try:
                    serial_comm.send(payload)
                except Exception as e:
                    logger.error(f"Falha ao enviar dados: {e}")
                last_send = now

    except Exception as e:
        logger.error(f"Erro inesperado no loop: {e}")
    finally:
        serial_comm.close()
        logger.warning("Comunicação serial encerrada.")
