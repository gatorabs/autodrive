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
        if not self.send_data:
            return

        now = time.monotonic()
        if self.last_send_time is not None and (now - self.last_send_time) < self.send_interval:
            return

        data_string = ",".join(str(d) for d in data) + "#"

        if self.serial_port and self.serial_port.is_open:
            try:
                self.serial_port.write(data_string.encode())
                self.logger.info(f"{data_string}")
                self.serial_port.flush()
                self.last_send_time = now
            except Exception as e:
                self.logger.error(f"Erro ao enviar dados: {e}")
                raise  # Repassa para o processo
        else:
            raise ConnectionError("Serial não está aberta")

    def receive(self):
        if self.serial_port and self.serial_port.in_waiting > 0:
            return self.serial_port.read(self.serial_port.in_waiting)
        return None

    def close(self):
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

    def reconnect(self):
        self.logger.info(f"Tentando reconectar na porta {self.com_port}...")

        if self.com_port not in self.list_available_ports():
            self.logger.warning(f"Porta {self.com_port} não está disponível no sistema.")
            self.serial_port = None
            return

        self.close()

        # Tenta reabrir a porta
        try:
            self.serial_port = serial.Serial(self.com_port, self.baud_rate)
            time.sleep(8)
            self.logger.info(f"Porta {self.com_port} reaberta com sucesso.")
        except Exception as e:
            self.logger.error(f"Erro ao reabrir {self.com_port}: {e}")
            self.serial_port = None