import time
from src.domain.constants.pid_constants import (
    DT_FILTERED,
    DERIV_ALPHA,
    DERIV_FILTERED,
)


class PIDV2Controller:
    def __init__(
        self,
        set_point,
        kp,
        ki,
        kd,
        min_output,
        max_output,
        logger,
        dt_filtered=DT_FILTERED,
        deriv_filtered=DERIV_FILTERED,
        deriv_alpha=DERIV_ALPHA,
    ):
        self.set_point = set_point
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.min_output = min_output
        self.max_output = max_output
        self.integral = 0
        self.last_error = 0
        self.last_time = time.monotonic()
        self.dt_filtered = dt_filtered
        self.deriv_filtered = deriv_filtered
        self.deriv_alpha = deriv_alpha
        self.logger = logger
        logger.info("Inicializando com PID V2.")

    def calculate(self, input_val):
        now = time.monotonic()
        raw_dt = now - self.last_time
        raw_dt = min(raw_dt, 0.1)  # evita dt muito grande
        self.dt_filtered = 0.8 * self.dt_filtered + 0.2 * raw_dt
        dt = max(self.dt_filtered, 1e-3)

        error = input_val - self.set_point

        # dead-band no erro (ajuste conforme seu ruído)
        if abs(error) < 0.5:
            error = 0

        # Termo P
        p = self.kp * error

        # Termo D (filtrado)
        raw_deriv = (error - self.last_error) / dt
        self.deriv_filtered = (
            self.deriv_alpha * raw_deriv + (1 - self.deriv_alpha) * self.deriv_filtered
        )
        d = self.kd * self.deriv_filtered

        # Termo I com anti-windup proporcional ao espaço restante em P+D
        self.integral += self.ki * error * dt
        max_int = self.max_output - (p + d)
        min_int = self.min_output - (p + d)
        self.integral = max(min(self.integral, max_int), min_int)

        # Soma tudo e aplica clamp final
        output = p + self.integral + d
        output = max(min(output, self.max_output), self.min_output)

        # dead-band na saída (opcional)
        if abs(output) < 2:
            output = 0

        self.last_error = error
        self.last_time = now
        return output
