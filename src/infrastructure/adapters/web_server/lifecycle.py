import requests


def shutdown_flask_server(shutdown_url: str, logger) -> None:
    try:
        requests.post(url=shutdown_url, timeout=3)
    except Exception as exc:
        logger.error(f"Erro ao chamar shutdown: {exc}")
