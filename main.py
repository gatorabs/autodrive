from src.core import *

def main():
    mp.set_start_method('spawn')

    user_flags = init_system()
    calibrated_data = load_data(CALIBRATION_FILE)
    initial_tk = {**calibrated_data, **user_flags}

    with mp.Manager() as manager:
        shared_controls = manager.dict(init_shared_controls(user_flags))
        tk_controls     = manager.dict(initial_tk)
        shared_frames   = manager.dict()

        manager_instance = ProcessManager(
            shared_controls=shared_controls,
            shared_frames=shared_frames,
            tk_controls=tk_controls,
            user_flags=user_flags
        )

        processes = manager_instance.create_all_processes()
        for p in processes:
            p.start()

        flask_proc = None
        last_webview = None

        try:
            while True:
                current_webview = shared_controls.get("WEBVIEW")
                flask_proc, last_webview = manager_instance.handle_flask_process(
                    current_webview=current_webview,
                    last_webview=last_webview
                )

        except KeyboardInterrupt:
            shared_controls["RUNNING"] = False
            for p in processes:
                if p.is_alive():
                    p.terminate()
            if flask_proc and flask_proc.is_alive():
                flask_proc.terminate()

if __name__ == '__main__':
    main()