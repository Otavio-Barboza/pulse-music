# imports gerais
from multiprocessing.connection import Client
from pathlib import Path
import subprocess, sys, time


PIPE_NAME = r"\\.\pipe\pulse_music_information"


class InformationProcess:

    _process: subprocess.Popen | None = None
    _connection = None


    @classmethod
    def get_information_executable(cls) -> Path:

        if getattr(sys, "frozen", False):
            return (
                Path(sys.executable).parent
                / "information_main.exe"
            )

        return (
            Path(__file__).resolve().parents[3]
            / "assets"
            / "app"
            / "information_main.exe"
        )

    @classmethod
    def start(cls):

        if cls._process is not None:
            return

        information_executable = (
            cls.get_information_executable()
        )

        if not information_executable.exists():
            raise FileNotFoundError(
                f"Executável de informações não encontrado: "
                f"{information_executable}"
            )

        print("[MAIN INFORMATION] Iniciando processo de informações...")

        cls._process = subprocess.Popen(
            [str(information_executable)]
        )

        cls.connect()

    @classmethod
    def connect(cls):
        from core.information.service.information_service import InformationService

        for _ in range(50):
            try:
                cls._connection = Client(
                    PIPE_NAME,
                    family = "AF_PIPE"
                )

                print("[MAIN INFORMATION] Conectado ao processo de informações.")


                InformationService.notify_callback_event("initializate_genius")

                return
            except (
                ConnectionRefusedError,
                FileExistsError,
                OSError
            ):
                time.sleep(0.1)

        raise(
            "Não foi possível conectar ao information_main.exe"
        )

    @classmethod
    def send(cls, data: dict, timeout = 10):
        if cls._connection is None:
            raise(
                "Processo de informações não conectado."
            )

        try:
            cls._connection.send(data)
            return cls._connection.recv()
        except (
            BrokenPipeError,
            EOFError,
            OSError
        ) as error:
            raise RuntimeError(
                "A conexão com o information_main.exe foi encerrada."
            ) from error

    @classmethod
    def shutdown(cls):

        if cls._connection is not None:
            try:
                cls._connection.close()
            except Exception:
                pass

            cls._connection = None
        
        if cls._process is None:
            return

        print("[MAIN INFORMATION] Encerrando processo de informações...")

        try:
            cls._process.terminate()
            cls._process.wait(timeout = 5)
        except subprocess.TimeoutExpired:
            cls._process.kill()
        finally:
            cls._process = None
            print("[MAIN INFORMATION] Encerrado")