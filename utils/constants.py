
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
        "SHOW_VIDEO": True,
        "SHOW_EDGES": True,
        "SHOW_ROI": True,
        "SHOW_PERSON_DETECTION": True,
        "F_Canny": 20,
        "S_Canny": 152,
        "Speed": 1,
        "Side": 1,
        "KP": 0.3,
        "KI": 0.005,
        "KD": 0.01,
        "ROI_START": 200,
        "ROI_END": 220,
        "ROI_X_START": 80,
        "ROI_X_END": 400,
        "Person": 0,
        "Traffic": 0
    }