import time

class PIDController:
    def __init__(self, set_point, kp, ki, kd, min_output, max_output, logger):
        self.set_point = set_point
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.min_output = min_output
        self.max_output = max_output
        self.integral = 0
        self.last_error = 0
        self.last_time = time.monotonic()
        self.logger = logger
        logger.info("Inicializando com PID V1.")

    def calculate(self, input_val):
        now = time.monotonic()
        delta_time = now - self.last_time
        if delta_time <= 0:
            delta_time = 1e-3

        error = input_val - self.set_point

        # Termo proporcional
        p = self.kp * error

        # Termo integral com anti-windup
        self.integral += self.ki * error * delta_time
        self.integral = max(min(self.integral, self.max_output), self.min_output)

        # Termo derivativo
        d = self.kd * (error - self.last_error) / delta_time

        output = p + self.integral + d
        output = max(min(output, self.max_output), self.min_output)

        if abs(output) < 2:
            output = 0

        self.last_error = error
        self.last_time = now

        return output

    def reset(self):
        self.integral = 0
        self.last_error = 0
        self.last_time = time.monotonic()

    def fallback(self, msg):
        self.logger.warning(f"{msg}")
        self.reset()
