import time

from controllers.serial_comm import SerialCommunicator
from processing.priorities_processor import set_process_priority


def security_process(shared_controls):
    set_process_priority("high")
    OPEN_FOR_RECEIVE = True
    BAUD_RATE = 115200
    security_com_port = shared_controls.get("SECURITY_COM")
    sec_serial = SerialCommunicator(security_com_port, baud_rate=BAUD_RATE, open_for_receive=OPEN_FOR_RECEIVE)
    try:
        while True:
            data = sec_serial.receive()
            if data is not None:
                if b's' in data or b'S' in data:
                    shared_controls["EMERGENCY_STOP"] = 1
                    print("Emergency Stop triggered!")
                else:
                    shared_controls["EMERGENCY_STOP"] = 0
            else:
                shared_controls["EMERGENCY_STOP"] = 0
            time.sleep(0.01)
    except Exception as e:
        print("Security Process Error:", e)
    finally:
        sec_serial.close()
