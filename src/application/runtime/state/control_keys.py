"""
Central names for shared runtime-control dictionaries.

This module is intentionally additive for now. Existing string literals can be
migrated gradually to these constants without changing runtime behavior.
"""

# Lifecycle and process flags.
RUNNING = "RUNNING"
WEBVIEW = "WEBVIEW"
MANUAL_MODE = "MANUAL_MD"
NEW_PID = "NEW_PID"

# Safety flags.
SAFE_STOP = "SAFE_STOP"
OBJECT_SAFE_STOP = "OBJ_SAFE_STOP"
EMERGENCY_STOP = "EMERGENCY_STOP"

# Shared telemetry and frame keys.
CAR_INFO = "CAR_INFO"
TIME_INFO = "TIME_INFO"
MAX_HEIGHT = "MAX_HEIGHT"
CAMERA_FRAME = "CAMERA_FRAME"
NORMAL_FRAME = "NORMAL_FRAME"
EDGES_FRAME = "EDGES_FRAME"
OBJECT_FRAME = "OBJECT_FRAME"
TAB2_FRAME = "TAB2_FRAME"
WARPED_ROI_FRAME = "WARPED_ROI_FRAME"

# Lane and car payload keys.
CAR_SPEED_DATA = "CAR_SPEED_DATA"
CAR_DIRECTION_DATA = "CAR_DIRECTION_DATA"
SPEED_OVERRIDE = "SPEED_OVERRIDE"

# Object detection payload keys.
OBJECT_SERIAL_DATA = "OBJECT_SERIAL_DATA"
CUSTOM_OBJECT_DATA = "CUSTOM_OBJECT_DATA"
CUSTOM_OBJECT_LABEL = "CUSTOM_OBJECT_LABEL"
OBJECT_PERSON_DATA = "OBJECT_PERSON_DATA"
TRAFFIC_LIGHT_DATA = "TRAFFIC_LIGHT_DATA"

# Source and communication controls.
SEND_DATA = "SEND_DATA"
SEND_LOGS = "SEND_LOGS"
SENDER_COM = "SENDER_COM"
SECURITY_COM = "SECURITY_COM"
LANE_SOURCE = "LANE_SOURCE"
LANE_SOURCE_TAB2 = "LANE_SOURCE_TAB2"
OBJECT_SOURCE = "OBJECT_SOURCE"
DETECTED_CAMERAS = "DETECTED_CAMERAS"

# UI/control values used by processing services.
SPEED = "Speed"
SIDE = "Side"
LINES = "Lines"
DISTANCE = "Distance"
SHOW_INFO = "SHOW_INFO"
SHOW_LINES = "SHOW_LINES"
SHOW_ROI = "SHOW_ROI"
FIRST_CANNY = "F_Canny"
SECOND_CANNY = "S_Canny"

# PID control gains.
PID_KP = "KP"
PID_KI = "KI"
PID_KD = "KD"

# Camera & perspective warp points.
WARP_TL_X = "tl_x"
WARP_TL_Y = "tl_y"
WARP_TR_X = "tr_x"
WARP_TR_Y = "tr_y"
WARP_BL_X = "bl_x"
WARP_BL_Y = "bl_y"
WARP_BR_X = "br_x"
WARP_BR_Y = "br_y"

# Object detection thresholds.
PERSON_THRESHOLD = "Person"
SEMAFORO_THRESHOLD = "SEMAFORO"
PEOPLE_REGION = "PeopleRegion"
SIGN_STOP = "PLACA_PARE"
SIGN_DETOUR = "PLACA_DESVIO"
SIGN_SPEED_BUMP = "PLACA_LOMBADA"

# YOLO confidence thresholds.
BASE_CONFIDENCE = "BaseConf"
CUSTOM_CONFIDENCE = "CustomConf"
SEMAFORO_CONFIDENCE = "SemaforoConf"
TIMESTAMP = "Timestamp"

# Stop-ramp behavior.
STOP_DECELERATION_STEP = "StopDecelerationStep"
STOP_RAMP_INTERVAL = "StopRampInterval"
SEMAFORO_STOP_DECELERATION_STEP = "SEMAFORO_StopDecelerationStep"
SEMAFORO_STOP_RAMP_INTERVAL = "SEMAFORO_StopRampInterval"

# Manual driving controls.
MANUAL_DIRECTION = "MANUAL_DIRECTION"
MANUAL_SPEED = "MANUAL_SPEED"

# CUDA/hardware status, populated at startup.
CUDA_AVAILABLE = "CUDA_AVAILABLE"
CUDA_DEVICE_NAME = "CUDA_DEVICE_NAME"
CUDA_STATUS_MESSAGE = "CUDA_STATUS_MESSAGE"
