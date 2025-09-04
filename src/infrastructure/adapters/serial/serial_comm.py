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
        self.serial_port = None
        self.send_data = send_data
        self.send_interval = send_interval
        self.com_port = com_port
        self.logger = logger
        self.baud_rate = baud_rate
        self.last_send_time = None
        self._warn_unavailable = False
        self._last_reconnect_try = 0.0
        self._port_available = False

        if send_data or open_for_receive:
            available_ports = self.list_available_ports()

            if self.com_port and self.com_port in available_ports:
                try:
                    self.start_com_port()
                except Exception as e:
                    self.logger.error(f"Erro ao abrir {com_port}: {e}")
                    self.serial_port = None
            else:
                self.logger.warning(
                    f"Porta {self.com_port} não está disponível no sistema."
                )
                self.serial_port = None

    def start_com_port(self, interval=8):
        self.serial_port = serial.Serial(self.com_port, self.baud_rate)
        time.sleep(interval)
        self.logger.info(
            f"Porta {self.com_port} aberta a {self.baud_rate} bps"
        )

    @staticmethod
    def list_available_ports() -> List[str]:
        return [p.device for p in list_ports.comports()]

    def send(self, data, verbose=False):
        if not self.send_data:
            return

        now = time.monotonic()
        if self.last_send_time is not None and (now - self.last_send_time) < self.send_interval:
            return

        data_string = ",".join(str(d) for d in data) + "#"

        if self.serial_port and self.serial_port.is_open:
            try:
                self.serial_port.write(data_string.encode())
                if verbose:
                    self.logger.info(f"{data_string}")
                self.serial_port.flush()
                self.last_send_time = now
            except Exception as e:
                raise  # Repassa para o processo
        else:
            raise ConnectionError("Serial não está aberta")

    def receive(self):
        if self.serial_port and self.serial_port.in_waiting > 0:
            return self.serial_port.read(self.serial_port.in_waiting)
        return None

    def close(self):
        if getattr(self, "serial_port", None):
            try:
                self.serial_port.close()
                self.logger.info(f"Porta {self.com_port} fechada com sucesso.")
            except Exception as e:
                self.logger.warning(f"Erro ao fechar a porta: {e}")
            finally:
                self.serial_port = None
                self.last_send_time = None

    def change_port(self, new_port, send_data, open_for_receive):
        old_port = self.com_port
        self.close()
        if self.logger:
            self.logger.info(f"Alterando porta serial: {old_port} -> {new_port}")
        self.com_port = new_port
        self.send_data = send_data
        self._warn_unavailable = False
        self._last_reconnect_try = 0.0
        self._port_available = False

        if send_data or open_for_receive:
            available_ports = self.list_available_ports()
            if self.com_port and self.com_port in available_ports:
                try:
                    self.start_com_port()
                except Exception as e:
                    if self.logger:
                        self.logger.error(f"Erro ao abrir {self.com_port}: {e}")
                    self.serial_port = None
            else:
                if self.logger:
                    self.logger.warning(
                        f"Porta {self.com_port} não está disponível no sistema."
                    )
                self.serial_port = None
        else:
            self.serial_port = None

    def reconnect(self):
        if self.com_port not in self.list_available_ports():
            self.serial_port = None
            return False

        self.close()
        try:
            if self.com_port not in self.list_available_ports():
                self.serial_port = None
                return False
            self.start_com_port()
            return True
        except Exception:
            self.serial_port = None
            return False

    def ensure_connection(self, cooldown: float = 2.0) -> bool:
        def is_open() -> bool:
            port = getattr(self, "serial_port", None)
            try:
                return bool(port) and getattr(port, "is_open", False)
            except Exception:
                return False

        if is_open():
            self._warn_unavailable = False
            return True

        try:
            available = set(self.list_available_ports())
        except Exception as exc:
            if not self._warn_unavailable and self.logger:
                self.logger.warning(
                    f"Não foi possível listar portas ({exc}); não tentarei reconectar."
                )
                self._warn_unavailable = True
            return False

        now = time.monotonic()
        if self.com_port not in available:
            if not self._warn_unavailable and self.logger:
                self.logger.warning(
                    f"Porta {self.com_port} indisponível; envio será pulado."
                )
                self._warn_unavailable = True
            self._port_available = False
            self._last_reconnect_try = now
            return False

        if not self._port_available:
            self._port_available = True
            self._last_reconnect_try = now
            return False

        if now - self._last_reconnect_try < cooldown:
            return False
        self._last_reconnect_try = now

        try:
            if self.logger:
                self.logger.info(f"Reconectando em {self.com_port}")
            self.reconnect()
        except Exception as exc:
            if self.logger:
                self.logger.error(f"Reconexão falhou em {self.com_port}: {exc}")

        if is_open():
            self._warn_unavailable = False
            return True

        if not self._warn_unavailable and self.logger:
            self.logger.warning(
                f"Falha ao abrir {self.com_port}; envio será pulado."
            )
            self._warn_unavailable = True
        return False