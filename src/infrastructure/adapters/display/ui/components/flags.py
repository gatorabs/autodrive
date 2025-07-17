from src.infrastructure.adapters.display.ui.helpers.ui_helper import save_ui_state
from src.infrastructure.constants.ui_constants.file_constants import DEFAULT_UI_PATH

def make_flag_command(tk_controls, vars, k, v, shared_controls=None):
    def cmd():
        tk_controls[k] = v.get()
        if k == "WEBVIEW":
            shared_controls["WEBVIEW"] = v.get()
            save_ui_state(tk_controls, DEFAULT_UI_PATH)
        if k == "NEW_PID":
            shared_controls["NEW_PID"] = v.get()
            save_ui_state(tk_controls, DEFAULT_UI_PATH)
    return cmd

