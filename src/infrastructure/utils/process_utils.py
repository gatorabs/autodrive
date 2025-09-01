def terminate_if_alive(process, timeout=3):
    if process and process.is_alive():
        process.join(timeout=timeout)
        if process.is_alive():
            process.terminate()
