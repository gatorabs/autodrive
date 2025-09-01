from src.application.system_initializer import SystemInitializer
from src.infrastructure.adapters.display.init_ui.build_sections.init import CalibrationUI


def init_system(initializer: SystemInitializer):
    app = CalibrationUI(initializer)
    app.mainloop()
    return app.flags_result
