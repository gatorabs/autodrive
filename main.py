from src.core import *

def main():
    mp.set_start_method('spawn')

    user_flags = setup_flag_interface()
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

        for p in processes:
            p.start()

        try:
            for p in processes:
                p.join()
        except KeyboardInterrupt:
            print("Interrompido pelo usuário.")
            shared_controls["RUNNING"] = False
            for p in processes:
                if p.is_alive():
                    p.terminate()

if __name__ == '__main__':
    main()