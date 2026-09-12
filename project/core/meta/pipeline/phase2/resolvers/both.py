# imports de back-end
from core.meta.models.song import SongMetadata
from core.services.account_manager import AccountManager
from core.utils.path import AppPaths
from core.meta.repository.filtering import Filtering
from core.meta.repository.metadata_repository import MetadataRepository
from core.meta.enum.status import SongStatus
from core.meta.cache.cache_artists import CacheArtists
from core.meta.repository.extract_metadata import ExtractMetadata
from core.meta.provider.deezer import FontManager

# imports gerais
from pathlib import Path
import aiohttp


async def resolve_both(
    both_list : list[SongMetadata], 
    path: str
):
    from core.meta.pipeline.pipeline import Pipeline

    if (
        both_list is None
        or len(both_list) == 0
    ):
        print(f"[PIPELINE PHASE 2] Lista de ambos está vazia ou é None: {both_list}")
        return

    ARTISTS_PATH: Path = AppPaths.ACCOUNT / AccountManager.accounts_cache.get("current_account") / "images" / "artists"
    ALBUMS_PATH: Path = AppPaths.ACCOUNT / AccountManager.accounts_cache.get("current_account") / "images" / "albums"
    
    async with aiohttp.ClientSession() as session:

        fonts = FontManager(session)
        
        for song in both_list:

            song.set_defined_artist(
                Filtering.clean_feat(
                    song.id3_data["filtered_data"].get("artist")
                )
            )
            song.set_artist_id(
                CacheArtists.resolve_id(
                    song.defined_artist
                ) if song.defined_artist is not None else None
            )
            song.set_potential_artists([song.id3_data["original_data"].get("artist_id3")])
            song.set_status(SongStatus.HIGH)
            song.set_score(1.0)
            song.set_song_path(path)

            deezer_data: dict = await fonts.deezer.get_song(
                title = song.id3_data["filtered_data"].get("title"), artist = song.defined_artist
            )

            _tracks: list = deezer_data.get("track") if deezer_data else None

            # validando caso a lista (track) retornado pela API da Deezer seja vazia.
            if not _tracks:
                print(f"[PHASE 2 BOTH]: _tracks é vazia: {song.mp3_file}")
                ExtractMetadata.register_metadata_player(
                    file_path = Path(song.song_path) / song.mp3_file,
                    title = song.id3_data["filtered_data"].get("title") if song.id3_data["filtered_data"].get("title") is not None else song.mp3_file_filtered.get("title"),
                    artist = song.defined_artist,
                    album = song.album_metadata.get("name"),
                    url_img_album_medium = None,
                    url_img_album_big = song.album_metadata.get("big").get("link"),
                    url_img_artista_medium = None,
                    url_img_artista_big = song.artist_metadata.get("big").get("link"),
                    id_alb = song.album_metadata.get("id_deezer"),
                    id_art = song.artist_metadata.get("id")
                )
                continue

            _track = _tracks[0]

            image_medium_artist_destination = MetadataRepository.download_image(
                url = _track['artist']['picture_medium'] or None,
                destination_path = ARTISTS_PATH / f"{song.artist_id}.jpg"
            )


            song.set_artist_metadata(
                id_deezer = _track['artist']['id'] or None,
                img_m = image_medium_artist_destination,
                img_b = Path(song.song_path) / song.mp3_file,
                img_b_link = _track['artist']['picture_big'] or None
            )


            image_medium_album_destination = MetadataRepository.download_image(
                url = _track['album']['cover_medium'] or None,
                destination_path = ALBUMS_PATH / f"{_track['album']['title']}.jpg"
            )


            song.set_album_metadata(
                name = _track['album']['title'] or None,
                id_deezer = _track['album']['id'] or None,
                img_m = image_medium_album_destination or None,
                img_b = Path(song.song_path) / song.mp3_file,
                img_b_link = _track['album']['cover_big'] or None
            )


            ExtractMetadata.register_metadata_player(
                file_path = Path(song.song_path) / song.mp3_file,
                title = song.id3_data["filtered_data"].get("title") if song.id3_data["filtered_data"].get("title") is not None else song.mp3_file_filtered.get("title"),
                artist = song.defined_artist,
                album = song.album_metadata.get('name'),
                url_img_album_medium = _track['album']['cover_medium'] or None,
                url_img_album_big = song.album_metadata.get('big').get('link'),
                url_img_artista_medium = _track['artist']['picture_medium'] or None,
                url_img_artista_big = song.artist_metadata.get('big').get('link'),
                id_alb = song.album_metadata.get('id_deezer'),
                id_art = song.artist_metadata.get('id')
            )

    await Pipeline.save_data({SongStatus.BOTH : both_list})
    Pipeline.to_execute_callbacks(path)