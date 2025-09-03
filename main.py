import multiprocessing as mp

from src.application.configuration.system_initializer import SystemInitializer
from src.infrastructure.data.repository.calibration_repository import load_data
from src.presentation.init_ui.init_ui_section import init_system
from src.infrastructure.constants.ui_constants.file_constants import CALIBRATION_FILE
from src.infrastructure.services.process_service import ProcessManager
from src.infrastructure.utils.process_utils import terminate_if_alive

def main():
    mp.set_start_method('spawn')

    initializer = SystemInitializer()
    user_flags = init_system(initializer)
    calibrated_data = load_data(CALIBRATION_FILE)
    initial_tk = {**calibrated_data, **user_flags}

    with mp.Manager() as manager:
        shared_controls = manager.dict(initializer.init_shared_controls(user_flags))
        tk_controls     = manager.dict(initial_tk)
        shared_frames   = manager.dict()

        manager_instance = ProcessManager(
            shared_controls=shared_controls,
            shared_frames=shared_frames,
            tk_controls=tk_controls,
            user_flags=user_flags
        )

        processes = manager_instance.create_all_processes()

        last_webview = None
        last_manual_mode = None

        try:
            while shared_controls.get("RUNNING", True):
                current_webview = shared_controls.get("WEBVIEW")
                current_manual_mode = shared_controls.get("MANUAL_MD")

                _, last_webview = manager_instance.handle_flask_process(
                    current_webview=current_webview,
                    last_webview=last_webview
                )

                _, last_manual_mode = manager_instance.handle_lane_object_processes(
                    current_manual_mode=current_manual_mode,
                    last_manual_mode=last_manual_mode
                )

        except KeyboardInterrupt:
            for p in processes:
                terminate_if_alive(p)
            for proc in (manager_instance.flask_proc, manager_instance.lane_proc, manager_instance.object_proc):
                terminate_if_alive(proc)

if __name__ == '__main__':
    main()
