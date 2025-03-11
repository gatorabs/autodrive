import os
import psutil

def set_process_priority(level):
    try:
        p = psutil.Process(os.getpid())
        if os.name == "nt":  # Windows
            priority_classes = {
                "high": psutil.HIGH_PRIORITY_CLASS,
                "above_normal": psutil.ABOVE_NORMAL_PRIORITY_CLASS,
                "normal": psutil.NORMAL_PRIORITY_CLASS,
                "below_normal": psutil.BELOW_NORMAL_PRIORITY_CLASS,
                "idle": psutil.IDLE_PRIORITY_CLASS
            }
            p.nice(priority_classes.get(level, psutil.NORMAL_PRIORITY_CLASS))
        else:  # Linux/macOS
            priority_values = {
                "high": -10,
                "above_normal": -5,
                "normal": 0,
                "below_normal": 5,
                "idle": 10
            }
            os.nice(priority_values.get(level, 0))
    except Exception as e:
        print(f"Failed to set priority: {e}")
