# import de back-end
from core.song.model.song import Song
from core.song.enum.song_enum import ReproductionMode


class Reproduction:

    _lists_modes_playbacks: dict[ReproductionMode, list[Song]] = {
        ReproductionMode.PLAYLIST : [],
        ReproductionMode.FAVORITE : [],
        ReproductionMode.ARTIST : [],
        ReproductionMode.ALBUM : []
    }
    current_reproduction: ReproductionMode = ReproductionMode.NOT_REPRODUCE

    @classmethod
    def set_current_reproduction(cls, new_mode: ReproductionMode):
        cls.current_reproduction = new_mode

    @classmethod
    def return_current_reproduction(cls) -> ReproductionMode:
        return cls.current_reproduction
    
    @classmethod
    def load_songs_from_mode(cls, mode: ReproductionMode, list: list[Song]):
        if not list: return
        
        cls._lists_modes_playbacks[mode].clear()
        print(
            "[REPRODUCTION]: Limpando a lista: \n"
            f"{cls._lists_modes_playbacks[mode]}"
        )
        cls._lists_modes_playbacks[mode].extend(list)
        print(
            "[REPRODUCTION]: Adicicionando músicas à lista: \n"
            f"{[song.name for song in (cls._lists_modes_playbacks[mode] or [])]}"
        )

    @classmethod
    def return_songs_for_mode(cls) -> list[Song] | None:
        if cls.current_reproduction != ReproductionMode.NOT_REPRODUCE:
            # print(f"Retornando lista de músicas do modo: {cls.current_reproduction}")
            return cls._lists_modes_playbacks[cls.current_reproduction]
        # print(f"Retornando none para as músicas do modo: {cls.current_reproduction}")
        return None

    # FUNÇÕES APENAS PARA AS FAVORITAS
    @classmethod
    def add_song(cls, song: Song):
        if song not in cls._lists_modes_playbacks[ReproductionMode.FAVORITE]:
            cls._lists_modes_playbacks[ReproductionMode.FAVORITE].append(song)
    
    @classmethod
    def remove_song(cls, song: Song):
        favorited_song: Song

        for favorited_song in cls._lists_modes_playbacks[ReproductionMode.FAVORITE]:
            if favorited_song.key == song.key:
                song_to_remove = favorited_song
                break

        cls._lists_modes_playbacks[ReproductionMode.FAVORITE].remove(song_to_remove)