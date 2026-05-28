from src.infrastructure.constants.runtime import (
    ANSI_GREEN,
    ANSI_RED,
    ANSI_RESET,
    ANSI_YELLOW,
)

class Logger:
    """
    Classe para log colorido com controle de verbosidade:
      - nome do processo sempre em amarelo
      - INFO em verde
      - WARNING em vermelho
      - ERROR em vermelho
      - se verbose=False, não imprime nada
    """

    def __init__(self, process_name: str, verbose: bool = True):
        self.process_name = process_name
        self.verbose = verbose

    def info(self, message: str):
        if not self.verbose:
            return
        print(f"{ANSI_YELLOW}[{self.process_name}]{ANSI_GREEN}[INFO] {message}{ANSI_RESET}")

    def warning(self, message: str):
        if not self.verbose:
            return
        print(f"{ANSI_YELLOW}[{self.process_name}]{ANSI_RED}[WARNING] {message}{ANSI_RESET}")

    def error(self, message: str):
        if not self.verbose:
            return
        print(f"{ANSI_YELLOW}[{self.process_name}]{ANSI_RED}[ERROR] {message}{ANSI_RESET}")
