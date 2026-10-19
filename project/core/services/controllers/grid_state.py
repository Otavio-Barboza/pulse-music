# imports gerais
from enum import Enum
import inspect, asyncio


class GridMode(Enum):
    ARTIST = 'artist'
    ALBUM = 'album'


class OpenGrid(Enum):
    OPEN = "open"
    CLOSE = "close"
    
    
class GridState:
    # Auxiliares para a trocar de conteúdo das paginas da grid.
    current_mode: GridMode | None = None
    open_grid: OpenGrid = OpenGrid.CLOSE

    _callbacks = {}

    
    @classmethod
    def register_callback(cls, event: str, func: callable):
        if event not in cls._callbacks:
            cls._callbacks[event] = []
        cls._callbacks[event].append(func)
        

    @classmethod
    def notify(cls, event: str, data = None):
        if event not in cls._callbacks:
            print(f'Evento de atualização não existente: {event}')
            return
        for func in cls._callbacks[event]:
            try:
                if inspect.iscoroutinefunction(func):
                    asyncio.create_task(func(data) if data is not None else func())
                else:
                    res = func(data) if data is not None else func()
                    if inspect.isawaitable(res):
                        asyncio.create_task(res)
            except Exception as e:
                print(e)


    @classmethod
    def set_current_mode(cls, mode: GridMode | None):
        cls.current_mode = mode


    @classmethod
    def set_open_grid(cls, mode: OpenGrid):
        cls.open_grid = mode