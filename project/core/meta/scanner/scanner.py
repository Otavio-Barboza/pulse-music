# imports de back-end
from core.services.account_manager import AccountManager
from core.services.controllers.grid_state import GridState, GridMode
from core.playlists.controller.playlist_state import PlaylistState
from core.playlists.enum.playlist_enum import PlaylistLoaded
from core.playlists.repository.path import CreatePlaylist
from core.meta.enum.status import ScannerStatus
from core.meta.controller.scanner_controller import ScannerController
from core.meta.repository.metadata_repository import MetadataRepository
from core.utils.path import AppPaths
from core.utils.utils import Utils
from core.favorite.controller.favoritas_controller import FavoriteState

# imports gerais
from pathlib import Path
from collections import defaultdict
import os, asyncio


class Scanner:

    _is_running = False


    @classmethod
    async def validate_data_json(cls, data: dict):
        """
        _summary_: Função base e linear do fluxo de execução para identificação de novas músicas ou músicas removidas + execução de recarregamento de cache e notificação de callbacks.

        Args:
            data (dict): dados do config_play.json
        """

        from core.meta.models.scanner_model import ScannerModel

        _changed: bool = False

        # pasta da playlist com as músicas
        path: str = data.get('music').get('music_path')
        len_path: int = len(os.listdir(path))

        if (
            path is None
            or len_path is None
        ):
            print(f"[SCANNER] values - path: {path}; len_path: {len_path}")
            return
        
        # atualizando quantidade de músicas na playlist
        data['music']['number_of_songs'] = len_path

        # verificando músicas adicionadas e removidas
        new_songs: list[str] | None = await cls.identify_songs(
            path = path, validate = True
        )
        removed_songs: list[str] | None = await cls.identify_songs(
            path = path, validate = False
        )


        # remoção de músicas e tarefas
        if removed_songs is not None:

            _changed = True

            # chaves para remover
            keys: set[str] = await cls.get_key_for_path(removed_songs)

            # validação de que se está rodando ainda alguma tarefa.
            if ScannerModel.return_is_busy():
                return

            # deletando as músicas conforme o conjunto de chaves definido e carregamento de memória
            await cls.delete_music(
                keys = keys
            )
            await MetadataRepository.load_cache()
            
            await asyncio.sleep(1)

        # adição de músicas e tarefas
        if new_songs is not None:   

            _changed = True

            # validando operação do scanner
            if ScannerModel.return_is_busy():
                return

            # resolução das operações de adição das novas músicas e carregamento do cache.
            await cls.new_song(
                path = path,
                list = new_songs
            )
            await MetadataRepository.load_cache()
            
            await asyncio.sleep(1)


        if _changed:
            data["date"]["latest_actualization"] = CreatePlaylist.generate_date()

            # Atualizando dados do config_play.json
            await Utils.async_update_json(
                path = AppPaths.ACCOUNT / AccountManager.accounts_cache.get("current_account") / "playlists" / data.get("id") / "config_play.json",
                data = data
            )

            # callback caso a playlist esteja aberta será executada.
            if (
                isinstance(PlaylistState.playlist_loaded, dict) and
                PlaylistState.playlist_loaded['open_or_close'] == PlaylistLoaded.OPEN
            ):
                PlaylistState.notify(
                    event = 'update_displayed_musics',
                    data = path
                )

            # Callback da quantidade de músicas da playlist
            if data.get("id") is not None:
                PlaylistState.notify(
                    event = "actualization_card_open_playlist",
                    data = {
                        "id": data.get("id"), 
                        "qtde": len_path,
                        "added_to_page" : True
                    }
                )

            _changed = False

        await asyncio.sleep(1)


    @classmethod
    async def verify_json(cls):
        """
        _summary_: Função para realizar intermediar a validação dos dados novos, excluídos ou não.
        """

        if cls._is_running:
            return
        
        cls._is_running = True
        
        try:
            # validando caminho de playlists
            if path_validation := not Path(AppPaths.ACCOUNT / AccountManager.accounts_cache["current_account"] / "playlists").exists():
                print(f"Pasta inválida: {path_validation}")
                return

            # listagem das playlists existentes dentro da pasta de playlists
            available_playlists: list[str] = os.listdir(AppPaths.ACCOUNT / AccountManager.accounts_cache["current_account"] / "playlists")

            # for para cada playlist listada sendo verificada individualmente os seus dados
            for playlist in available_playlists:
                data_playlist = await Utils.async_load_json(
                    path = AppPaths.ACCOUNT / AccountManager.accounts_cache.get("current_account") / "playlists" / str(playlist) / "config_play.json"
                )

                await cls.validate_data_json(data = data_playlist)
        finally:
            cls._is_running = False

    @classmethod
    async def identify_songs(cls, path: str, validate: bool) -> list[str] | None:
        """
        _summary_: Função para identificar músicas novas ou removidas. Por meio dos sets ela retorna a diferença entre um e outro o conforme o validate.

        Args:
            path (str): Caminho da pasta com as músicas.
            validate (bool): Se True (novas músicas) Senão (músicas removidas)

        Returns:
            list[str] | None: Lista quando conter mais de um valor, senão retorna None como um valor nulo. 
        """

        paths_json: set[str] = set()
        path_files: set[str] = set()

        song_json: dict = await Utils.async_load_json(
            path = AppPaths.ACCOUNT / AccountManager.accounts_cache.get("current_account") / "music" / "songs.json"
        )

        # adicionando os caminhos ao conjunto pelos dados do arquivo JSON
        for _, value in song_json.items():
            if value.get("song_path") == path:
                destination_path: Path = Path(value.get("song_path")) / value.get("mp3_file")
                paths_json.add(str(destination_path))

        # adicionando os caminhos ao conjunto da listagem de músicas da pasta
        file: str
        for file in os.listdir(path):

            destination_path: Path = Path(path) / file

            if (
                destination_path.exists()
                and file.lower().endswith(".mp3")
            ):
                path_files.add(str(destination_path))

        # diferença dos conjuntos convertidos em lista.

        # Se True o validate: diferença dos caminhos que restaram da pasta (para músicas novas)
        # Se False o validate: diferença dos caminhos que restaram do JSON (para músicas removidas)
        list_to_return: list[str] = list(path_files - paths_json) if validate else list(paths_json - path_files)

        # print(list(path_files - paths_json))
        # print(list(paths_json - path_files))

        # retorno da lista, se for zerada retorna None
        return list_to_return if len(list_to_return) != 0 else None
    
    @classmethod
    async def get_key_for_path(cls, paths: list[str]) -> set[str]:
        """
        _summary_: Função para retornar as chaves de cada músicas para remoção.

        Args:
            paths (list[str]): Lista com os caminhos para validação.

        Returns:
            set[str]: Conjunto com as chaves de cada música a ser removida.
        """

        set_to_return: set[str] = set()
        songs_json: dict = await Utils.async_load_json(
            AppPaths.ACCOUNT / AccountManager.accounts_cache.get("current_account") / "music" / "songs.json"
        )

        # adicionando as chaves para remoção
        for key, value in songs_json.items():
            destination_song: Path = Path(value.get("song_path")) / value.get("mp3_file")

            if str(destination_song) in paths:
                set_to_return.add(key)

        return set_to_return
    
    @classmethod
    async def identify_artists_albums_existings(cls, keys_to_remove: set[str]):
        """
            1 - Acessar o JSON songs.
            2 - Pegar as Imagens das músicas em referência e atribuir em set().
            3 - Analisar o JSON songs inteiro e analisar se em alguma música existe aquele artist ou álbum.
                3.1 - SE EXISTIR: Não excluir a imagem do artist/álbum;
                3.2 - SENÃO: Excluir a imagem.
            4 - Excluir a música em si do músicas.json            
        """

        """  parte 0  """

        # imagens de referência para exlusão
        # dicionário cuja chave é o nome do artista (defined_artist), e seus valores são um conjunto de chaves da música (key / chave da música de songs.json)
        artists = defaultdict(set)        

        # dicionário cuja chave é o nome do álbum (album_metadata - name), e seus valores são um conjunto de chaves da música (key / chave da música de songs.json)
        albums = defaultdict(set)

        # set final de músicas para remover
        keys_for_remove = set()


        """  parte 1  """

        # songs.json
        song_json: dict = await Utils.async_load_json(
            AppPaths.ACCOUNT / AccountManager.accounts_cache.get("current_account") / "music" / "songs.json"
        )
        lyrics_json: dict = await Utils.async_load_json(
            AppPaths.ACCOUNT / AccountManager.accounts_cache.get("current_account") / "music" / "lyrics.json"
        )
        favorites_json: dict = await Utils.async_load_json(
            AppPaths.ACCOUNT / AccountManager.accounts_cache.get("current_account") / "music" / "favorites.json"
        )

        """  parte 2  """

        key: str 
        value: dict
        # pegar as imagens
        for key, value in song_json.items():

            # artist + chaves da música
            artist = value.get("defined_artist")
            artists[artist].add(key)           
           
            # albums + chaves da música
            album = value.get("album_metadata").get("name")            
            albums[album].add(key)

                            
        """  parte 3  """

        key: str 
        value: dict
        for key, value in song_json.items():

            # Nome do artista e álbum
            artist: str = value.get("defined_artist")
            album: str = value.get("album_metadata").get("name")

            # Caminho da imagem medium para exclusão do artista e álbum
            destination_path_artist: str = value.get("artist_metadata").get("medium")
            destination_path_album: str = value.get("album_metadata").get("medium")
            
            # verificando se a chave atual do for está no set de chaves para remover repassado como argumento
            if key in keys_to_remove:

                # remaining_alb/art são variáveis auxiliares para pegar a diferença de do set se chaves, ou seja, as chaves restantes, remanescentes da diferença
                remaining_alb = albums[album] - keys_to_remove
                remaining_art = artists[artist] - keys_to_remove

                cover_name, _ = os.path.splitext(
                    value.get('mp3_file')
                )
                cover_path: Path = AppPaths.ACCOUNT / AccountManager.accounts_cache.get("current_account") / "images" / "covers" / f"{cover_name}.jpg"

                """  parte 3.1 - exclusão de imagens  """

                # Se a quantidade de albuns restantes for igual a 0, considera-se que não existem músicas com aquele álbum mais. Assim excluindo sua imagem.
                if len(remaining_alb) == 0:
                    """  parte 3.2  """
                    MetadataRepository.delete_image(destination_path_album)
                
                # Se a quantidade de artistas restantes for igual a 0, considera-se que não existem músicas com aquele artista mais. Assim excluindo sua imagem.
                if len(remaining_art) == 0:
                    """  parte 3.2  """
                    MetadataRepository.delete_image(destination_path_artist)

                # Capas de música por serem únicas de cada música, são todas excluídas sem restrições
                if os.path.isfile(cover_path):
                    MetadataRepository.delete_image(cover_path)
                    
                keys_for_remove.add(key)


        """  parte 4  """

        for key in keys_for_remove:

            if song_json.get(key, None) is not None:
                del song_json[key]

            if lyrics_json.get(key, None) is not None:
                del lyrics_json[key]

            if favorites_json.get(key, None) is not None:
                del favorites_json[key]


        """  Restante da execução  """

        await Utils.async_update_json(
            path = AppPaths.ACCOUNT / AccountManager.accounts_cache.get("current_account") / "music" / "songs.json",
            data = song_json
        )            
        await Utils.async_update_json(
            path = AppPaths.ACCOUNT / AccountManager.accounts_cache.get("current_account") / "music" / "lyrics.json",
            data = lyrics_json
        )            
        await Utils.async_update_json(
            path = AppPaths.ACCOUNT / AccountManager.accounts_cache.get("current_account") / "music" / "favorites.json",
            data = favorites_json
        )            

        GridState.notify(
            event = 'actualization_grid', 
            data = GridMode.ARTIST
        )
        GridState.notify(
            event = 'actualization_grid',
            data = GridMode.ALBUM
        )
        FavoriteState.notify(
            event = "actualization_favorites",
            data = None
        )

        
    @classmethod
    async def new_song(cls, path: str, list: list[str]):
        """
        _summary_: Função intermediaria do scanner com o pipeline.

        Args:
            path (str): caminho da pasta com as músicas.
            list (list[str]): lista de músicas para serem adicionadas.
        """

        from core.meta.pipeline.pipeline import Pipeline

        playlist: str
        for playlist in os.listdir(
            AppPaths.ACCOUNT / AccountManager.accounts_cache.get("current_account") / "playlists"
        ):
            json_config_play: dict = await Utils.async_load_json(
                AppPaths.ACCOUNT / AccountManager.accounts_cache.get("current_account") / "playlists" / playlist / "config_play.json"
            )

            if json_config_play["music"].get("music_path") == path:
                playlist_id: str = playlist
                break

        asyncio.create_task(
            asyncio.to_thread(
                Pipeline.start_wrapper_sync,
                path,
                list,
                playlist_id
            )
        )

    @classmethod
    async def delete_music(cls, keys: set[str]):
        """
        _summary_: Função para gerenciar o processo de exclusão de músicas.

        Args:
            keys (set[str]): conjunto com as chaves para serem removidas.
        """

        from core.meta.models.scanner_model import ScannerModel

        # definição de status e quantidade de tarefas ativas do scanner
        ScannerModel.start_task()
        ScannerModel.set_status_prosesses(ScannerStatus.ON_SCANNER)
        cls.manager_status()

        # Notificando conteúdo do drawer do scanner
        ScannerController.notify(
            event = 'icon_status_scanner',
            data = None
        )
        
        await asyncio.sleep(1)

        try:
            # resolução da esclusão do conteúdo
            await cls.identify_artists_albums_existings(
                keys_to_remove = keys
            )
        finally:
            ScannerModel.finaly_task()

            await asyncio.sleep(1)

            if not ScannerModel.return_is_busy():
                ScannerModel.set_status_prosesses(None)
                ScannerController.notify(
                    event = 'progress_status_scanner',
                    data = None
                )
                cls.manager_status()

    @classmethod
    def manager_status(cls):
        """
        _summary_: Função para notificar a informação do scanner conforma sua atividade.
        """

        from core.meta.models.scanner_model import ScannerModel

        if ScannerModel.status_procesesses == ScannerStatus.ON_SCANNER:
            ScannerController.notify(
                event = 'processes_information_scanner',
                data = 'Monitoramento está rodando...\n\n    Poder estar havendo remoção dos conteúdos desnecessários ou alguma atualização das informações exibidas.'
            )
        elif ScannerModel.status_procesesses == ScannerStatus.ON_PIPELINE_PLAYLIST:
            ScannerController.notify(
                event = 'processes_information_scanner',
                data = 'Buscando data...\n\n    O player está buscando os data de artists, álbuns, capas e todos com suas imagens, aguarde o processo acontecer para visualizá-los.'
            )
        elif ScannerModel.status_procesesses == None:
            ScannerController.notify(
                event = 'processes_information_scanner',
                data = 'Monitor das Playlists aguardando alterações...\n\n    Aqui será indicado as alterações de informações que estiverem acontecendo, sejam:\n\n• Adição de músicas em alguma playlist.\n• Remoção de músicas em alguma playlist.\n\n    O monitor gerencia automaticamente o conteúdo, adicionando novos itens e removendo os desnecessários.'
            )