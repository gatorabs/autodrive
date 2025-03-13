import time

from controllers.serial_comm import SerialCommunicator
from processing.priorities_processor import set_process_priority


def data_sender_process(lane_queue, object_queue, shared_controls):
    set_process_priority("above_normal")
    SEND_DATA = True
    com_port = shared_controls.get("SENDER_COM")
    serial_comm = SerialCommunicator(com_port, send_data=SEND_DATA)

    lane_data = {"speed": 255, "direction": 180}
    obj_data = {"person": 0, "semaforo": 0}
    send_interval = 0.01  # intervalo de envio em segundos
    last_send_time = time.time()

    try:
        while True:
            if not lane_queue.empty():
                lane_data = lane_queue.get()
            if not object_queue.empty():
                obj_data = object_queue.get()

            if obj_data.get("person", 0) == 1 or shared_controls.get("EMERGENCY_STOP", 0) == 1:
                lane_data["speed"] = 0

            current_time = time.time()
            if (current_time - last_send_time) >= send_interval:
                data_to_send = [
                    lane_data.get("direction", 180),
                    lane_data.get("speed", 255),
                    obj_data.get("semaforo", 0)
                ]
                serial_comm.send(data_to_send)
                last_send_time = time.time()
            else:
                sleep_time = max(0, send_interval - (current_time - last_send_time))
                time.sleep(sleep_time)
    except Exception as e:
        print("Data Sender Error:", e)
    finally:
        serial_comm.close()