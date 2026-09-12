# imports de back-end
from core.song.model.song import Song
from core.song.enum.song_enum import ReproductionMode
from core.meta.repository.tasks import Task
from core.meta.cache.global_cache import cache_metadata
from core.services.account_manager import AccountManager
from core.utils.utils import Utils
from core.utils.path import AppPaths

# imports gerais
from pathlib import Path
import os


class SongRepository:

    @classmethod
    def load_songs(cls, path: Path, mode: ReproductionMode) -> list[Song]:
        if isinstance(path, str):
            path = Path(path)
        
        music_list_path: list[str] = [
            str(path / song)
            for song in os.listdir(path)
            if (path / song).suffix.lower() == ".mp3"
        ]
        music_list_json: list[str] = [
            key
            for key, value in cache_metadata.tracks.items()
            if value.get("song_path") == str(path)
        ]

        if len(music_list_path) > len(music_list_json):
            return [
                Song(
                    name = song.removesuffix('.mp3'),
                    path = path / song,
                    key = Task.return_track_id(path / song),
                    mode = mode
                ) for song in sorted(
                    os.listdir(path), key = str.casefold
                ) 
            ]
        else:
            return [
                Song(
                    name = value.get("mp3_file").removesuffix(".mp3"),
                    path = str(value.get("song_path")),
                    key = key,
                    mode = mode
                ) for key, value in sorted(
                    cache_metadata.tracks.items(), 
                    key = lambda item: item[1].get("mp3_file").casefold()
                ) if value.get("song_path") == str(path)
            ]


    @classmethod
    def get_artist(cls, key_song : str):
        song_json: dict = Utils.sync_load_json(
            AppPaths.ACCOUNT / AccountManager.accounts_cache.get("current_account") / "music" /"songs.json"
        )
        
        key: str
        item: dict
        for key, item in song_json.items():
            if key == key_song:
                artista = item.get('defined_artist')
                return artista if artista is not None else 'Artista Desconhecido'

    @classmethod
    def get_cover(cls, song: str):
        cover_destination: Path = AppPaths.ACCOUNT / AccountManager.accounts_cache.get("current_account") / "images" / "covers"

        cover: str
        for cover in os.listdir(cover_destination):
            if cover.removesuffix('.jpg') == song:
                return cover_destination / cover
        else:
            return r'images\placeholders\capa_musicas_desconhecidas.png'
    
    @classmethod
    def get_song(cls, key_song: str):
        song_json: dict = Utils.sync_load_json(
            AppPaths.ACCOUNT / AccountManager.accounts_cache.get("current_account") / "music" /"songs.json"
        )

        _song = None

        key: str
        item: dict
        for key, item in song_json.items():
            if key == key_song:
                _song = item
                break

        if _song is None:
            return "Título não Identificado"

        elif _song["id3_data"]["filtered_data"].get("title") is not None:
            return _song["id3_data"]["filtered_data"].get("title")

        elif _song["mp3_file_filtered"].get("title") is not None:
            return _song["mp3_file_filtered"].get("title")

        elif _song["id3_data"]["original_data"].get("title") is not None:
            return _song["id3_data"]["original_data"].get("title")

        else:
            _song["mp3_file_filtered"].get("title")