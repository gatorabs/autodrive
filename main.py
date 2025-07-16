from src.core import *

def main():
    mp.set_start_method('spawn')

    user_flags = prepare_initial_flags()
    calibrated_data = load_data(CALIBRATION_FILE)
    initial_tk = {**calibrated_data, **user_flags}

    with mp.Manager() as manager:
        shared_controls = manager.dict(
            init_shared_controls(user_flags, calibrated_data)
        )

        tk_controls   = manager.dict(initial_tk)
        shared_frames = manager.dict()

        print_initial_flags(shared_controls)

        processes = create_processes(
            shared_controls,
            shared_frames,
            tk_controls,
            user_flags
        )

        flask_proc = None
        last_webview = shared_controls.get("WEBVIEW")

        for p in processes:
            p.start()

        try:
            while True:
                curr_webview = shared_controls.get("WEBVIEW")

                flask_proc, last_webview  = handle_flask_process(
                    current_webview=curr_webview,
                    last_webview=last_webview,
                    flask_proc=flask_proc,
                    shared_frames=shared_frames,
                    shared_controls=shared_controls
                )

        except KeyboardInterrupt:
            shared_controls["RUNNING"] = False
            for p in processes:
                if p.is_alive():
                    p.terminate()
            if flask_proc is not None and flask_proc.is_alive():
                flask_proc.terminate()

if __name__ == '__main__':
    main()