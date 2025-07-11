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
        self.com_port = com_port
        self.logger = logger
        self.baud_rate = baud_rate
        self.last_send_time = None

        if send_data or open_for_receive:
            try:
                self.serial_port = serial.Serial(com_port, baud_rate)
                time.sleep(8)
                self.logger.info(f"Porta {self.com_port} aberta a {self.baud_rate} bps")
            except Exception as e:
                self.logger.error(f"Erro ao abrir {com_port}: {e}")
                self.serial_port = None

    @staticmethod
    def list_available_ports() -> List[str]:
        return [p.device for p in list_ports.comports()]

    def send(self, data):
        if (self.last_send_time is None or
                (time.monotonic() - self.last_send_time) >= self.send_interval):
            data_string = ",".join(str(d) for d in data) + "#"
            self.logger.info(data_string)
            if self.send_data and self.serial_port:
                self.serial_port.write(data_string.encode())
                self.serial_port.flush()
            self.last_send_time = time.monotonic()

    def receive(self):
        if self.serial_port and self.serial_port.in_waiting > 0:
            return self.serial_port.read(self.serial_port.in_waiting)
        return None

    def close(self):
        self.serial_port.flush()
        if self.serial_port:
            self.serial_port.close()

    def reconnect(self):
        self.logger.info(f"Tentando reconectar na porta {self.com_port}...")

        # Fecha a porta atual com segurança
        if self.serial_port:
            try:
                self.serial_port.flush()
                self.serial_port.close()
                self.logger.info(f"Porta {self.com_port} fechada com sucesso.")
            except Exception as e:
                self.logger.warning(f"Erro ao fechar a porta: {e}")
            finally:
                self.serial_port = None
                self.last_send_time = None

        # Tenta reabrir a porta
        try:
            self.serial_port = serial.Serial(self.com_port, self.baud_rate)
            time.sleep(2)  # espera reset do Arduino
            self.logger.info(f"Porta {self.com_port} reaberta com sucesso.")
        except Exception as e:
            self.logger.error(f"Erro ao reabrir {self.com_port}: {e}")
            self.serial_port = None


