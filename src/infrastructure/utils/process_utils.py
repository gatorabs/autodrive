"""Utility helpers for working with multiprocessing processes."""


def terminate_if_alive(process, timeout=3):
    """Gracefully terminate a process if it is still alive after joining."""
    if process and process.is_alive():
        process.join(timeout=timeout)
        if process.is_alive():
            process.terminate()
