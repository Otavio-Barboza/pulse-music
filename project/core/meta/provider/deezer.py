# import de back-end
from core.meta.models.base import MetadataSource

# imports gerais
import aiohttp, asyncio


BASE_URL = 'https://api.deezer.com'


class FontManager:
    def __init__(self, session):
        self.deezer = DeezerFont(session)


# Classe é uma fonte de metadados e segue as regras da base
class DeezerFont(MetadataSource):
    def __init__(self, session: aiohttp.ClientSession):
        self.session = session

    async def _get(self, url, params = None):
        try:
            async with self.session.get(
                url, params = params, timeout = aiohttp.ClientTimeout(total = 12)
            ) as resp:
                resp.raise_for_status()
                return await resp.json()
        except asyncio.TimeoutError:
            return None
        except aiohttp.ClientError:
            return None
        
    async def get_song(self, title: str, artist: str | None = None) -> dict:
        query = f"{title} {artist}" if artist else title

        data = await self._get(
            f'{BASE_URL}/search',
            {'q' : query}
        )

        if data is None:
            return None

        print(
            "\n\n[DEEZER]",
            title,
            "-",
            artist,
            "|",
            "resultado:", data is not None,
            "|",
            "tracks:", len(data["data"]) if data["data"] else 0
        )    

        return {
            'track' : data['data'],
            'font' : 'deezer',
        }
    
    async def get_album(self, album_id : int):
        return await self._get(f'{BASE_URL}/album/{album_id}')
    
    async def get_artist(self, artist_id : int):
        return await self._get(f'{BASE_URL}/artist/{artist_id}')