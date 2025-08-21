# PID tuning parameters
KP = 0.3
KI = 0.003
KD = 0.015
MIN_OUTPUT = -32
MAX_OUTPUT = 32
TARGET_CENTER_DISTANCE = 80

# Filters for PIDV2Controller
DT_FILTERED = 0.03
DERIV_ALPHA = 0.1
DERIV_FILTERED = 0.0

FALLBACK_PID_INPUT = "PID input não é finito, resetando e mantendo última direção"
FALLBACK_PID_OUTPUT = "PID output não é finito, resetando e mantendo última direção"