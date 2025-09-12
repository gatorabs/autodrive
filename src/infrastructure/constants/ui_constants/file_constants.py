import os

CALIBRATION_FILE = os.path.join("config", "calibration_data.json")
DEFAULTS_FILE    = os.path.join("config", "defaults.json")
DEFAULT_UI_PATH  = os.path.join("config", "init_ui_defaults.json")


def get_profile_defaults_file(profile_index: int) -> str:
    """Retorna o caminho do arquivo de padrões para o perfil solicitado.

    O perfil ``1`` utiliza o arquivo ``defaults.json`` existente para manter
    compatibilidade com o comportamento atual. Perfis adicionais utilizam o
    padrão ``defaults_profile_<n>.json`` dentro da pasta ``config``.
    """

    if profile_index <= 1:
        return DEFAULTS_FILE
    return os.path.join("config", f"defaults_profile_{profile_index}.json")


def get_profile_calibration_file(profile_index: int) -> str:
    """Retorna o caminho do arquivo de calibração para o perfil solicitado.

    O perfil ``1`` reutiliza ``calibration_data.json`` para manter
    compatibilidade com o comportamento atual. Perfis adicionais utilizam o
    padrão ``calibration_profile_<n>.json`` dentro da pasta ``config``.
    """

    if profile_index <= 1:
        return CALIBRATION_FILE
    return os.path.join("config", f"calibration_profile_{profile_index}.json")
