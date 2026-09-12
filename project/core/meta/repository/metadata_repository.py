# import de back-end
from core.services.account_manager import AccountManager
from core.meta.repository.tasks import Task
from core.utils.utils import Utils
from core.meta.models.song import SongMetadata
from core.utils.path import AppPaths

# imports gerais
from pathlib import Path
import requests


class MetadataRepository:
    
    @classmethod
    async def data_manager_songs_json(cls, groups: dict):
        current_song_json: dict = await Utils.async_load_json(
            AppPaths.ACCOUNT / AccountManager.accounts_cache.get("current_account") / "music" / "songs.json"
        )
        
        object_list = [
            musica
            for grupo in groups.values()
            for musica in grupo
        ]
        
        final_data = {}
        
        song: SongMetadata
        for song in object_list:            
            final_data[song.song_id] = Task.return_song_json(song = song)
        
        for id, data in current_song_json.items():
            if id not in final_data:
                final_data[id] = data

        await Utils.async_update_json(
            path = AppPaths.ACCOUNT / AccountManager.accounts_cache.get("current_account") / "music" / "songs.json", 
            data = final_data
        )
    
    @classmethod
    async def load_cache(cls):
        from core.meta.cache.cache_artists import CacheArtists
        from core.meta.cache.global_cache import cache_metadata

        dados = await Utils.async_load_json(
            AppPaths.ACCOUNT / AccountManager.accounts_cache.get("current_account") / "music" / "songs.json"
        )
        cache_metadata.load(dados)
        await CacheArtists.load()

    @classmethod
    def download_image(cls, url: str, destination_path: Path | str) -> Path | None:
        """
        Baixa uma imagem via URL e salva no path especificado.

        Args:
            url (str): URL da imagem
            destination_path (str): path completo (sem extensão ou com)

        Returns:
            str | None: path final salvo ou None se falhar
        """

        if url is None or not url:
            return None

        try:
            path = Path(destination_path)
            path.parent.mkdir(parents = True, exist_ok = True)

            response = requests.get(url, timeout = 20)

            if response.status_code != 200:
                return None

            with open(path, "wb") as f:
                f.write(response.content)

            return path
        except Exception as e:
            print("falha na conexão:", e)
            return None
    
    @classmethod
    def delete_image(cls, path: str | Path):
        if path is None:
            print(f'Arquivo de imagem inválido: {path}')
            return

        if isinstance(path, str):
            path: Path = Path(path)

        if not path.exists():
            print(f'Imagem não encontrada: {path}')
            return

        try:
            path.unlink()
            print(f'Imagem removida: {path}')
        except Exception as erro:
            print(f'Erro ao remover a imagem: {erro}')