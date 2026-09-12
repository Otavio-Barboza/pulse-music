# imports de back-end
from core.meta.enum.status import SongStatus, ScannerStatus
from core.meta.models.song import SongMetadata
from core.meta.pipeline.phase_1 import Phase1
from core.meta.pipeline.phase2.phase_2 import Phase2
from core.meta.pipeline.phase_3 import Phase3
from core.meta.repository.filtering import Filtering
from core.meta.repository.extract_metadata import ExtractMetadata
from core.meta.repository.metadata_repository import MetadataRepository
from core.meta.repository.tasks import Task
from core.meta.cache.cache_artists import CacheArtists
from core.meta.models.scanner_model import ScannerModel
from core.meta.scanner.scanner import Scanner
from core.meta.controller.scanner_controller import ScannerController
from core.playlists.controller.playlist_state import PlaylistState
from core.services.controllers.grid_state import GridState, GridMode
from core.playlists.enum.playlist_enum import PlaylistLoaded

# imports gerais
from pathlib import Path
import os, asyncio


class Pipeline:

    @classmethod
    async def _async_classificar_presenca(cls, filtered_title : dict[str | None], filtered_artist : str | None):
        if filtered_title is None:
            return SongStatus.INCOMPLETE

        if filtered_title['artist'] is not None and filtered_artist is None:
            return SongStatus.NO_ARTIST_ID3

        if filtered_title['artist'] is None and filtered_artist is not None:
            return SongStatus.NO_ARTIST_FILTERED

        if filtered_title['filtered_title'] is not None:
            return SongStatus.TITLE_ONLY

        return SongStatus.INCOMPLETE

    @classmethod
    def normalize_song(cls, song) -> str:
        if isinstance(song, SongMetadata):
            return song.mp3_file
        return song
    
    @classmethod
    async def save_data(cls, groups: dict):
        await MetadataRepository.data_manager_songs_json(groups = groups)
        await CacheArtists.save()
        await MetadataRepository.load_cache()
    
    @classmethod
    def to_execute_callbacks(cls, path: Path):
        _added_to_page: bool = False

        GridState.notify(
            event = 'actualization_grid', 
            data = GridMode.ARTIST
        )
        GridState.notify(
            event = 'actualization_grid',
            data = GridMode.ALBUM
        )

        if (
            isinstance(PlaylistState.playlist_loaded, dict) 
            and PlaylistState.playlist_loaded['open_or_close'] == PlaylistLoaded.OPEN
        ):
            _added_to_page = True

            print("notificando updates")
            PlaylistState.notify(
                event = 'update_covers_and_names',
                data = None
            )

        PlaylistState.notify(
            event = 'actualization_card_open_playlist',
            data = {
                'id' : id,
                'qtde' : len(os.listdir(path)),
                "added_to_page" : _added_to_page
            }
        )

    @classmethod
    def start_wrapper_sync(
        cls, 
        path: str, 
        object_list: list = list[SongMetadata] | list[str], 
        playlist_id: str | None = None
    ) -> list[SongMetadata]:
        
        ScannerModel.start_task()
        ScannerModel.set_status_prosesses(
            ScannerStatus.ON_PIPELINE_PLAYLIST
        )
        Scanner.manager_status()
        ScannerController.notify(
            'icon_status_scanner',
            None
        )

        try:
            asyncio.run(
                cls.async_process_musics(
                    path = Path(path), 
                    object_list = object_list,
                    id = playlist_id
                )
            )
        except Exception as e:
            import traceback

            print(f"[PIPELINE ERROR]: {e}")
            traceback.print_exc()
        finally:
            ScannerModel.finaly_task()
            
            if not ScannerModel.return_is_busy():
                ScannerModel.set_status_prosesses(
                    None
                )
                ScannerController.notify(
                    'progress_status_scanner',
                    None
                )
                Scanner.manager_status()

            print("pipeline finalizado")
            
    @classmethod
    async def async_process_musics(
        cls, 
        path: Path, 
        object_list: list[SongMetadata] | list[str] = [], 
        id: str | None = None
    ) -> list[SongMetadata]:

        # Músicas que passam pela fase 0, ou seja, já foram alteradas pelo player em algum momento
        list_already_processed: list[SongMetadata] = []

        # músicas novas que não foram alteradas pelo player.
        musics_list: list[SongMetadata] = []

        song: str
        for song in os.listdir(path) if len(object_list) == 0 else object_list:

            filtered_title: dict | None = None
            filtered_artist: dict | None = None

            song = cls.normalize_song(song)
            song = os.path.basename(song)
            destination_file: Path = path / song
            
            if (Path(path) / song).suffix.lower() == ".mp3":

                # print(f"\nMúsica válida: {song}")

                # FASE 0 - verificação da existencia de data já alterados pelo próprio player, assim carregamento dos data já imbutidos.
                if ExtractMetadata.music_already_processed(destination_file):

                    # Extraí todos os dados da música que já foram embutidos.
                    extract_metadata_song: dict[str, str | None] = ExtractMetadata.extract_metadata_player(destination_file)

                    # vindo da variável extract_metadata_song, pega ou cria o ID do artista da música.
                    artist_id: str = CacheArtists.resolve_id(extract_metadata_song.get("artist"))

                    # Extração das imagens e gravação delas
                    extract_images_song: dict[str, Path | None] = await asyncio.to_thread(
                        ExtractMetadata.extact_images_mp3,
                        destination_file, 
                        extract_metadata_song.get("album", "Nome não identificado"), 
                        song.replace(".mp3", ""),
                        artist_id
                    )
                    
                    list_already_processed.append(SongMetadata(
                        song_id = Task.return_track_id(destination_file),
                        playlist_id = id,
                        artist_id = artist_id,
                        song_title_id3_filtered = extract_metadata_song.get("title"),
                        defined_artist = extract_metadata_song.get("artist"),
                        mp3_file = song,
                        song_path = str(path),
                        mp3_file_title = None,
                        mp3_file_artist = None,
                        original_artist_id3 = None,
                        song_artist_id3_filtered = None,
                        consensus = None,
                        gap = None,
                        score = None,
                        sim_1 = None,
                        sim_2 = None,
                        list_of_potential_artists = [],
                        status = SongStatus.HIGH,
                        original_song_title = song,
                        album_metadata = {
                            "id_deezer" : extract_metadata_song.get("album_id"), 
                            "name" : extract_metadata_song.get("album"), 
                            "medium" : str(
                                extract_images_song.get("alb")
                            ), 
                            "big" : {
                                "link" : None,
                                "path" : str(destination_file)
                            }
                        },
                        artist_metadata = {
                            "id_deezer" : extract_metadata_song.get("artist_id"), 
                            "medium" : str(
                                extract_images_song.get("art")
                            ), 
                            "big" : {
                                "link" : None,
                                "path" : str(destination_file)
                            }
                        }
                    ))
                else:
                    # FASE 1 - extração de metadados e classificação + filtragem tradicional

                    # capta os metadados e salva a capa da música
                    data = await ExtractMetadata.async_extract(destination_file)

                    if data["title"] is not None:
                        filtered_title = await Filtering.async_filter_title(name = data["title"])

                    if data["artist"] is not None:
                        filtered_artist = await Filtering.async_filter_artist(artist = data["artist"])
                
                    if (
                        filtered_artist is not None 
                        and filtered_title["artist"] is not None
                    ):
                        musics_list.append(await Phase1.phase_1(
                            mp3_file = song,
                            song_metadata_id3 = filtered_title,
                            original_artist_id3 = filtered_artist,
                            song_path = path,
                            playlist_id = id
                        ))
                    else:
                        musics_list.append(await ExtractMetadata.async_organize_data(
                            mp3_file = song,
                            song_metadata_id3 = filtered_title,
                            original_artist_id3 = filtered_artist,
                            artist_id = '',
                            status = await cls._async_classificar_presenca(
                                filtered_title = filtered_title, 
                                filtered_artist = filtered_artist    
                            ),
                            playlist_id = id,
                            song_path = path
                        ))
            else:
                print(f"\nArquivo incompativel: ({Path(song).suffix})")
                continue

        group_phase_0 = {SongStatus.PHASE_0 : list_already_processed}
        await cls.save_data(groups = group_phase_0)
        cls.to_execute_callbacks(path)

        groups = await Phase2.phase_2(
            list_object = musics_list, 
            path = path
        )
        
        await Phase3.phase_3(
            incomplete_list = groups[SongStatus.INCOMPLETE], 
            path = path
        )

        cls.to_execute_callbacks(path)