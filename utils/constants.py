
tl = (20, 0)
tr = (300, 0)
bl = (0, 20)
br = (320, 20)

# Cores ANSI
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"
ORANGE = "\033[35m"


flags = {
        "SEND_DATA": True,
        "RUNNING": True,
        "WEBVIEW": False,
}


track_flags = {
        "SHOW_ROI": True,
        "F_Canny": 20,
        "S_Canny": 152,
        "Speed": 1,
        "Side": 1,
        "KP": 0.3,
        "KI": 0.005,
        "KD": 0.01,
        "Person": 0,
        "Traffic": 0,
        "tl_x": 120, "tl_y": 180,
        "tr_x": 381, "tr_y": 180,
        "bl_x": 41, "bl_y": 220,
        "br_x": 440, "br_y": 220,
    }
