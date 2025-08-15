# PID parâmetros
KP = 0.3
KI = 0.003
KD = 0.015
MIN_OUTPUT = -32
MAX_OUTPUT = 32
TARGET_CENTER_DISTANCE = 80

FALLBACK_PID_INPUT = "Entrada do PID não é finita, resetando e mantendo última direção"
FALLBACK_PID_OUTPUT = "PID output não é finito, resetando e mantendo última direção"