import time
from typing import List
from serial.tools import list_ports
import serial

class SerialCommunicator:
    def __init__(self,
                 com_port,
                 baud_rate=115200,
                 send_interval=0.1,
                 send_data=False,
                 open_for_receive=False,
                 logger=None):

        self.send_data = send_data
        self.send_interval = send_interval
        self.last_send_time = time.time()
        self.com_port = com_port
        self.logger = logger
        self.baud_rate = baud_rate

        if send_data or open_for_receive:
            try:
                self.serial_port = serial.Serial(com_port, baud_rate)
                self.logger.info(f"Porta {self.com_port} aberta a {self.baud_rate} bps")
                time.sleep(1)

            except Exception as e:
                self.logger.error(f"Erro ao abrir {com_port}: {e}")
                self.serial_port = None

    @staticmethod
    def list_available_ports() -> List[str]:
        return [p.device for p in list_ports.comports()]

    def send(self, data):
        if (time.time() - self.last_send_time) >= self.send_interval:
            data_string = ",".join(str(d) for d in data) + ",#"
            #print(data_string)
            if self.send_data and self.serial_port:
                self.serial_port.write(data_string.encode())
            self.last_send_time = time.time()

    def receive(self):
        if self.serial_port and self.serial_port.in_waiting > 0:
            return self.serial_port.read(self.serial_port.in_waiting)
        return None

    def close(self):
        if self.serial_port:
            self.serial_port.close()
