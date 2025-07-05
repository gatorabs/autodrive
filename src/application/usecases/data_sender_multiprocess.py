from src.core.__init__sender import *

def data_sender_process(lane_queue,
                        object_queue,
                        shared_controls,
                        verbose=True):

    set_process_priority("high")
    logger = Logger("SerialCommunicator", verbose=verbose)

    com_port = shared_controls.get("SENDER_COM")
    send_data = shared_controls.get("SEND_DATA")

    serial_comm = SerialCommunicator(com_port=com_port,
                                     send_data=send_data,
                                     logger=logger)

    lane_data = {"speed": 255, "direction": 180}
    obj_data = {"person": 0, "semaforo": 0}
    send_interval = 0.01  # intervalo de envio em segundos
    last_send_time = time.time()

    try:
        while shared_controls.get("RUNNING", True):
            # Atualiza dados de faixa se houver
            try:
                new_lane_data = lane_queue.get_nowait()
                lane_data.update(new_lane_data)
            except Empty:
                pass

            # Atualiza dados de objetos se houver
            try:
                new_obj_data = object_queue.get_nowait()
                obj_data.update(new_obj_data)
            except Empty:
                pass

            # Condição de parada de emergência
            if obj_data.get("person", 0) == 1 or shared_controls.get("EMERGENCY_STOP", 0) == 1 or obj_data.get("semaforo", 0) == 0:
                lane_data["speed"] = 0
                car_info = shared_controls.get("car_info", {})
                car_info["speed"] = 0
                shared_controls["car_info"] = car_info

            current_time = time.time()
            elapsed = current_time - last_send_time
            if elapsed >= send_interval:
                data_to_send = [
                    lane_data.get("direction", 180),
                    lane_data.get("speed", 255),
                    obj_data.get("semaforo", 0)
                ]
                try:
                    serial_comm.send(data_to_send)
                except Exception as e:
                    logger.error(f"Falha ao enviar dados: {e}")
                last_send_time = current_time

    except Exception as e:
        logger.error(f"Erro inesperado: {e}")
    finally:
        serial_comm.close()
        logger.warning(f"Comunicação serial encerrada.")
