from src.application.configuration.system_initializer import SystemInitializer
from src.presentation.init_ui.build_sections.init import CalibrationUI


def init_system(initializer: SystemInitializer):
    app = CalibrationUI(initializer)
    app.mainloop()
    return app.flags_result
