# imports de back-end
from core.utils.utils import Utils
from core.services.account_manager import AccountManager
from core.playlists.models.playlist import Playlist
from core.playlists.models.playlist_config import PlaylistConfig
from core.playlists.models.playlist_card import PlaylistCard
from core.playlists.repository.path import CreatePlaylist
from core.utils.path import AppPaths
from core.meta.cache.global_cache import cache_metadata

# imports gerais
from pathlib import Path
import os, asyncio


class PlaylistRepository:

    @classmethod
    def load_itens(cls) -> list[Playlist]:
        """
            Retorna uma lista com objetos Playlist() para auxiliar no carregamento das playlist ao rodar o app.
        Returns:
            list[Playlist]: lista com objetos Playlist().
        """
        
        set_playlists: set = set()
        playlists = Utils.sync_load_json(AppPaths.ACCOUNT / AccountManager.accounts_cache.get("current_account") / "playlists.json")

        for key, value in playlists.get("playlists").items():
            set_playlists.add(Playlist(
                id = key,
                name = value.get("name"),
                path = value.get("path")
            ))
        
        return list(set_playlists)
    
    @classmethod
    def load_cards(cls) -> list[PlaylistCard]:
        """
            Com auxílio do cls.carregar_itens utiliza-se dos objetos Playlist() e com eles carrega os detalhes de cada playlist, armazenando-os na lista cards os objetos PlaylistCard().
        Returns:
            list[PlaylistCard]: Lista com objetos PlaylistCard()
        """
        playlists: list[Playlist] = cls.load_itens()
        cards: set[PlaylistCard] = set()

        for playlist in playlists:
            playlist_config = Utils.sync_load_json(
                AppPaths.ACCOUNT / AccountManager.accounts_cache["current_account"] / "playlists" / playlist.id / "config_play.json"
            )
            
            path = playlist_config["music"].get("music_path")
            qtde = CreatePlaylist.count_number_of_songs(Path(path))

            cards.add(PlaylistCard(
                id = playlist.id,
                name = playlist_config["name"],
                image_path = playlist_config["style"]["image_path"],
                color = playlist_config["style"]["color"],
                opacity = playlist_config["style"]["opacity"],
                playlist_path = path,
                number_of_songs = qtde
            ))
        
        return list(cards)
    
    @classmethod
    def list_playlists(cls) -> list[PlaylistCard]:
        """
            Chama cls.load_cards para intermediar o retorno das playlists ao EstadoPlaylist
        Returns:
            list[PlaylistCard]: lista com objetos PlaylistCard()
        """
        return cls.load_cards()
    
    @classmethod
    def count_number_of_songs(cls, path: str) -> int:
        """
            Intermédio para EstadoPlaylist e outras chamadas do contador da quantidade de músicas da playlist.
        Args:
            path (str): caminho da pasta

        Returns:
            int: N° int da quantidade de músicas da playlist
        """
        return CreatePlaylist.count_number_of_songs(Path(path))

    @classmethod
    def create_playlist(
        cls, 
        name : str, 
        music_path : str,
        image_path : str,
        color : str,
        opacity : float

    ) -> Playlist:
        """
            Cria o objeto Playlist, a pasta, json da playlist e adição ao json playlists da existencia da playlist nova
        Args:
            name (str): Nome da Plalist
            tipo (str): tipo (pasta ou fav)
            music_path (str): caminho da pasta das musicas
            origem_mus (str): origem das musicas (pasta ou dinamica das favoritas)
            image_path (str): caminho da imagem
            color (str): color do bgcolor do card
            opacity (float): valor da opacity da color

        Returns:
            Playlist: Objeto Playlist()
        """
  
        # Salvando dados do playlists.json
        dados = Utils.sync_load_json(
            path = AppPaths.ACCOUNT / AccountManager.accounts_cache["current_account"] / "playlists.json"
        )

        new_id, id_num = CreatePlaylist.generate_id(data = dados)

        PLAYLIST_PATH = AppPaths.ACCOUNT / AccountManager.accounts_cache["current_account"] / "playlists" / new_id
        Utils.create_path(PLAYLIST_PATH)

        dados["latest_id"] = id_num

        dados["playlists"][new_id] = {
            "name" : name,
            "path" : str(PLAYLIST_PATH)
        }
        dados["latest_actualization"] = CreatePlaylist.generate_date()

        Utils.sync_update_json(
            path = AppPaths.ACCOUNT / AccountManager.accounts_cache["current_account"] / "playlists.json",
            data = dados
        )

        # salvando os dados do config_json
        qtde = CreatePlaylist.count_number_of_songs(Path(music_path))

        json_config = CreatePlaylist.return_content_data_playlits(
            id = new_id,
            music_path = music_path,
            image_path = image_path,
            color = color,
            opacity = opacity,
            name = name,
            number_of_songs = qtde
        )

        Utils.sync_update_json(
            path = AppPaths.ACCOUNT / AccountManager.accounts_cache["current_account"] / "playlists" / new_id / "config_play.json",
            data = json_config
        )

        return Playlist(
            id = new_id,
            name = name,
            path = PLAYLIST_PATH
        )

    @classmethod
    def return_images(cls) -> list[str] | tuple[str, str]:
        """
            Intermedio ao EstadoPlaylist para a listagem de imagens 
        Returns:
            list[str] | tuple[str, str]: Lista das imagens e tupla com os caminhos dos albuns e capas
        """
        return CreatePlaylist.return_selection_images()
    
    @classmethod
    def save_config(cls, playlist: PlaylistConfig):
        """
            Salva os dados do UPDATE da playlist em ambos JSONs
        Args:
            playlist (PlaylistConfig): Objeto PlaylistConfig para uso na inserção dos dados
        """
        config_play_json_destination = AppPaths.ACCOUNT / AccountManager.accounts_cache.get("current_account") / "playlists" / playlist.id / "config_play.json"
        playlist_json_destination = AppPaths.ACCOUNT / AccountManager.accounts_cache.get("current_account") / "playlists.json"
 
        json_config = Utils.sync_load_json(config_play_json_destination)
        json_play = Utils.sync_load_json(playlist_json_destination)

        json_play["playlists"][playlist.id]["name"] = playlist.name
        json_play["latest_actualization"] = CreatePlaylist.generate_date()

        json_config["name"] = playlist.name
        json_config["style"]["image_path"] = playlist.style["image_path"]
        json_config["style"]["color"] = playlist.style["color"]
        json_config["style"]["opacity"] = playlist.style["opacity"]
        json_config["music"]["path"] = playlist.music["music_path"]
        json_config["music"]["number_of_songs"] = CreatePlaylist.count_number_of_songs(
            Path(playlist.music["music_path"])
        )
        json_config["date"]["latest_actualization"] = CreatePlaylist.generate_date()

        Utils.sync_update_json(path = playlist_json_destination, data = json_play)
        Utils.sync_update_json(path = config_play_json_destination, data = json_config)
    
    @classmethod
    def remove_playlist_json(cls, id: str):
        """
            Remove a playlist do indice no JSON playlists
        Args:
            id (str): ID da playlist
        """
        
        path: Path = AppPaths.ACCOUNT / AccountManager.accounts_cache.get("current_account") / "playlists.json"
        data: dict[str, str | int | dict[str, dict[str, str]]] = Utils.sync_load_json(path)

        data["playlists"].pop(id, None)
        data["latest_actualization"] = CreatePlaylist.generate_date()

        Utils.sync_update_json(path = path, data = data)
        

    @classmethod
    def delete_playlist(cls, id: str):
        """
            Função para executar a exclusão dos elementos da playlist
        Args:
            id (str): ID da Playlist
        """
        from core.meta.scanner.scanner import Scanner
        
        path: Path = AppPaths.ACCOUNT / AccountManager.accounts_cache.get("current_account") / "playlists" / id
        # config_play_json: dict = Utils.sync_load_json(path / "config_play.json")
        
        # obtendo as chaves para remover
        keys_to_remove: set[str] = cls.recognize_song_keys(id)

        # chamada ao scanner para remover os conteúdos
        asyncio.run(
            Scanner.identify_artists_albums_existings(
                keys_to_remove = keys_to_remove
            )
        )

        CreatePlaylist.remove_path(path)
        cls.remove_playlist_json(id = id)
        
    @classmethod
    def recognize_song_keys(cls, id: str) -> set[str]:
        """
        _summary_: Função para selecionar as músicas conforme o ID da playlist salva.

        Args:
            id (str): ID da playlist para remover.

        Returns:
            set[str]: Conjunto (set) com as strings (IDs das músicas da respectiva playlist).
        """

        songs_json: dict = Utils.sync_load_json(
            AppPaths.ACCOUNT / AccountManager.accounts_cache.get("current_account") / "music" / "songs.json"
        )
        
        return {
            key for key, value in songs_json.items()
            if value.get('playlist_id') == id
        }
    
    @classmethod
    def remove_dead_content(cls, id: str, path: Path):
        from core.meta.scanner.scanner import Scanner

        keys_to_remove: set[str] = set()

        for key, value in cache_metadata.tracks.items():
            if (
                value.get('id_playlist') == id and
                value.get('caminho') != path
            ):
                keys_to_remove.add(key)

        asyncio.run(
            Scanner.identify_artists_albums_existings(
                keys_to_remove = keys_to_remove
            )
        )

    @classmethod
    def check_playlist_names(cls) -> list[str]:
        existing_names_playlists: set[str] = set()
        
        playlists_json: dict = Utils.sync_load_json(
            AppPaths.ACCOUNT / AccountManager.accounts_cache.get("current_account") / "playlists.json"
        )
        
        for _, value in playlists_json.get("playlists").items():
            existing_names_playlists.add(value.get("name"))

        return list(existing_names_playlists)
    
    @classmethod
    def check_existing_folders(cls) -> list[str]:

        base_path = AppPaths.ACCOUNT / AccountManager.accounts_cache.get("current_account") / "playlists"
        
        existing_paths = list()

        for playlist in os.listdir(
            base_path
        ):
            config_play_json = Utils.sync_load_json(
                AppPaths.ACCOUNT / AccountManager.accounts_cache.get("current_account") / "playlists" / playlist / "config_play.json"
            )

            caminho_pasta = config_play_json['music'].get('music_path')

            if caminho_pasta not in existing_paths:
                existing_paths.append(caminho_pasta)

        return existing_paths
    
    @classmethod
    def identify_music_artist(cls, song_id: str) -> str:
        for key, value in cache_metadata.tracks.items():
            if key == song_id:
                return value.get("defined_artist", "Artista Desconhedido")
        else:
            return "Artista Desconhedido"
        
    @classmethod
    def return_cover(cls, music_name: str) -> Path:
        covers_list: list[str] = os.listdir(
            AppPaths.ACCOUNT / AccountManager.accounts_cache.get("current_account") / "images" / "covers"
        )

        for cover in covers_list:
            if cover == music_name + '.jpg':
                return AppPaths.ACCOUNT / AccountManager.accounts_cache.get("current_account") / "images" / "covers" / cover
        return r'assets\images\placeholders\capa_musicas_desconhecidas.png'