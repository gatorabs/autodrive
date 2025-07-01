from src.infrastructure.constants.colors_constants import YELLOW, RED, GREEN, RESET

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
        print(f"{YELLOW}[{self.process_name}]{GREEN}[INFO] {message}{RESET}")

    def warning(self, message: str):
        if not self.verbose:
            return
        print(f"{YELLOW}[{self.process_name}]{RED}[WARNING] {message}{RESET}")

    def error(self, message: str):
        if not self.verbose:
            return
        print(f"{YELLOW}[{self.process_name}]{RED}[ERROR] {message}{RESET}")
