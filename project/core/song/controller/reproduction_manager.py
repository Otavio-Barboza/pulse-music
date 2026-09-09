# imports de back-end
from core.song.model.song import Song
from core.song.model.data_song import PlayerState, ReproductionConfiguration
from core.song.model.reproduction import Reproduction
from core.song.model.player import Player
from core.song.model.audio import AudioProcess
from core.song.enum.song_enum import ReproductionMode
from core.song.repository.song_repository import SongRepository
from core.lyrics.controller.lyrics_services import LyricsServices
from core.services.controllers.async_manager import AsyncManager

# import geral
from pathlib import Path
import random, threading, time, asyncio


class ReproductionManager:

    state = PlayerState()
    configuration = ReproductionConfiguration()

    current_font: ReproductionMode = Reproduction.current_reproduction

    _queue: list[Song] = []
    _random_queue: list[Song] = []
    _current_index: int = 0

    _is_monitoring: bool = False
    _slider_dragging: bool = False

    _callbacks: dict[str, list] = {
        "volume" : [],
        "total_time" : [],
        "slider_position" : [],
        "current_song" : [], # callback para marcar musica que estiver tocando no momento.
        "slider" : [],
        "actualization_container" : [],
        "play/pause" : [],
        "repeat" : [],
        "shuffle" : []
    }

    LyricsServices.register_callback(
        event = "get_lyrics",
        callback = LyricsServices.get_lyric
    )

    # CALLBACKS
    @classmethod
    def register_callback(cls, event: str, callback: callable):
        cls._callbacks[event].append(callback)

    @classmethod
    def notify(cls, event: str):
        for callback in cls._callbacks.get(event, []):
            callback(cls)

    
    # FONTE
    @classmethod
    def set_font(cls):
        cls.current_font = Reproduction.return_current_reproduction()
        
        cls._queue = Reproduction.return_songs_for_mode()[:]
        cls._random_queue = cls._queue[:]
        random.shuffle(cls._random_queue)

        cls._current_index = 0

        print(f"(set_fonte) - Fonte atual: {cls.current_font}")

    @classmethod
    def update_queues(cls):        
        if (
            cls._queue is None
            or cls.current_font != ReproductionMode.FAVORITE
        ):
            return
                
        cls._queue.clear()
        cls._queue.extend(Reproduction.return_songs_for_mode())

        cls._random_queue.clear()
        cls._random_queue.extend(cls._queue[:])
        random.shuffle(cls._random_queue)

    @classmethod
    def update_queue_scanner(cls, *_):
        try:
            # print(f"_queue: {cls._queue}")

            cls._queue.clear()
                
            if _songs_for_mode := Reproduction.return_songs_for_mode()[:] is None:
                # print(f"Músicas como None: {_songs_for_mode}")
                return
            
            cls._queue.extend(Reproduction.return_songs_for_mode()[:])

            # print(f"_random_queue: {cls._random_queue}")
            cls._random_queue.clear()
            cls._random_queue.extend(cls._queue[:])

            # print(cls.state.current_song)
            if cls.state.current_song is None:
                return

            index: int
            song: Song
            for index, song in enumerate(cls._queue):
                # print(song.key, cls.state.current_song.key)
                if song.key == cls.state.current_song.key:
                    cls._current_index = index
                    break
        except Exception as error:
            print(f"(update_queue_scanner): {error}")

    # MÚSICA
    @classmethod
    def get_index(cls, key: str):
        
        index: int
        song: Song
        for index, song in enumerate(cls._queue):
            if song.key == key:
                cls._current_index = index
                break

    @classmethod
    def play(cls):
        cls.state.current_time = 0

        cls.start()

        if not cls._queue:
            return

        if not cls.configuration.shuffle:
            song: Song = cls._queue[cls._current_index]
        elif cls.configuration.shuffle and cls.configuration.repeat:
            song: Song = cls._queue[cls._current_index]
        elif cls.configuration.shuffle and not cls.configuration.repeat:
            song: Song = cls._random_queue[cls._current_index]

        cls.state.current_song = song
        cls.state.current_time = 0


        if (
            ReproductionManager.current_font == ReproductionMode.ARTIST
            or ReproductionManager.current_font == ReproductionMode.ALBUM
        ):
            Player.load_song(
                Path(song.path)
            )
        elif (
            ReproductionManager.current_font == ReproductionMode.PLAYLIST
            or ReproductionManager.current_font == ReproductionMode.FAVORITE
        ):
            Player.load_song(
                Path(song.path) / f"{song.name}.mp3"
            )
        else:
            return
            
        Player.play()

        cls.set_is_playing(True)

        cls.notify('actualization_container')
        cls.notify('play/pause')
        cls.notify('current_song')
        
        AsyncManager.create_task(
            LyricsServices.notify_callback_lyrics(
                event = 'get_lyrics',
                data = {
                    'key' : cls.state.current_song.key,
                    'name' : cls.get_name(),
                    'artist' : cls.get_artist()
                }
            )
        )

        if LyricsServices.expanded_screen:
            LyricsServices.notify(
                event = 'actualization_lyric',
                data = None
            )

    @classmethod
    def set_is_playing(cls, value: bool):
        cls.state.is_playing = value


    # CONTROLES
    @classmethod
    def toggle_play_pause(cls):
        cls.set_is_playing(not cls.state.is_playing)

        if cls.state.is_playing:
            Player.play()
        else:
            Player.pause()

        cls.notify('play/pause')
    
    @classmethod
    def next(cls):
        if not cls._queue:
            return
        
        cls._current_index += 1

        if cls._current_index >= len(cls._queue):
            cls._current_index = 0

        cls.play()

    @classmethod
    def previous(cls):
        if not cls._queue:
            return
        
        cls._current_index -= 1

        if cls._current_index < 0:
            cls._current_index = len(cls._queue) - 1

        cls.play()

    
    # CONFIGURAÇÕES
    @classmethod
    def toggle_shuffle(cls):

        cls.configuration.shuffle = not cls.configuration.shuffle
        print(f"SHUFFLE: {cls.configuration.shuffle}")
        cls.notify('shuffle')

    @classmethod
    def toggle_repeat(cls):

        cls.configuration.repeat = not cls.configuration.repeat
        print(f"REPEAT: {cls.configuration.repeat}")
        cls.notify('repeat')

    
    # MONITOR
    @classmethod
    def set_drag_slider(cls, value: bool):
        cls._slider_dragging = value

    @classmethod
    def start(cls):
        if cls._is_monitoring:
            return

        # Registra o recebimento do evento de término enviado pelo audio_main.exe.
        AudioProcess.register_event_callback(
            event = "song_finished",
            callback = cls._on_song_finished
        )

        cls.start_time_monitor()
        cls._is_monitoring = True

    @classmethod
    def start_time_monitor(cls):

        def loop():
            """
                Monitora continuamente o estado da reprodução.

                O áudio executa em um processo separado.
                Este monitor apenas recebe informações desse processo e atualiza o estado da aplicação.
            """

            while True:

                if (
                    cls.state.is_playing 
                    and not cls._slider_dragging
                ):
                    # O AudioProcess mantém o estado recebido do audio_main.exe
                    current_duration = Player.current_duration()

                    if (
                        cls.state.total_time != current_duration
                        or current_duration == 0.0
                    ):
                        cls.update_total_time()
                        cls.notify("slider")

                    # Obtém a posição atual através do estado recebido do processo de áudio.
                    cls.update_time(
                        Player.current_position()
                    )
                    
                time.sleep(0.2)

        # O monitor continua sendo executado fora do fluxo principal da aplicação.
        threading.Thread(
            target = loop,
            daemon = True
        ).start()


    # TEMPO
    @classmethod
    def update_time(cls, time: float):
        cls.state.current_time = time
        cls.notify('slider_position')

    @classmethod
    def update_total_time(cls):
        cls.state.total_time = Player.current_duration()
        cls.notify('total_time')

    @classmethod
    def formatted_current_duration(cls) -> str:
        return Player.formatted_current_duration()
    
    @classmethod
    def formatted_total_duration(cls) -> str:
        return Player.formatted_total_duration()

    @classmethod
    def go_to(cls, value: float):
        Player.go_to(value)
        cls.notify('slider_position')

    @classmethod
    def set_volume(cls, volume: float):
        print(f"[REPRODUCTION MANAGER] volume: {volume}")
        cls.state.volume = volume
        Player.set_volume(cls.state.volume)
        cls.notify("volume")

    
    # TRATAMENTO AUTOMÁTICO DA MÚSICA
    @classmethod
    def _on_song_finished(cls, data: dict):
        """
            Recebe a informação de que o audio_main.exe terminou naturalmente a música.

            A decisão sobre a próxima reprodução continua pertencendo ao ReproductionManager.
        """
        print("[REPRODUCTION] Música terminou, avançando...")
        cls.handle_end_of_music()

    @classmethod
    def handle_end_of_music(cls):
        if cls.configuration.repeat:
            cls.play()
        else:
            cls.next()
            
    
    # OUTROS
    @classmethod
    def get_artist(cls) -> str:
        return SongRepository.get_artist(cls.state.current_song.key)
    
    @classmethod
    def get_name(cls) -> str:
        print(f"[REPRODUCTION MANAGER] current song key: {cls.state.current_song.key}")
        return SongRepository.get_song(cls.state.current_song.key)

    @classmethod
    def get_cover(cls) -> str:
        return SongRepository.get_cover(cls.state.current_song.name)