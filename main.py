import multiprocessing as mp

from src.bootstrap import (
    build_process_manager,
    create_runtime_state,
    terminate_runtime_processes,
)

def main():
    mp.set_start_method('spawn')

    with mp.Manager() as manager:
        shared_controls, tk_controls, shared_frames, user_flags = create_runtime_state(manager)

        manager_instance = build_process_manager(
            shared_controls=shared_controls,
            shared_frames=shared_frames,
            tk_controls=tk_controls,
            user_flags=user_flags,
        )

        processes = manager_instance.create_all_processes()

        last_webview = None
        last_manual_mode = None

        try:
            while shared_controls.is_running():
                current_webview = shared_controls.webview
                current_manual_mode = shared_controls.manual_mode

                _, last_webview = manager_instance.handle_flask_process(
                    current_webview=current_webview,
                    last_webview=last_webview
                )

                _, last_manual_mode = manager_instance.handle_lane_object_processes(
                    current_manual_mode=current_manual_mode,
                    last_manual_mode=last_manual_mode
                )

        except KeyboardInterrupt:
            terminate_runtime_processes(processes, manager_instance)

if __name__ == '__main__':
    main()
