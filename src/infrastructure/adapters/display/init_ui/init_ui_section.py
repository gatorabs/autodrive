from src.infrastructure.adapters.display.init_ui.build_sections.init import CalibrationUI

def init_system():
    app = CalibrationUI()
    app.mainloop()
    return app.flags_result
