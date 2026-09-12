# imports de back-end
from core.meta.pipeline.helpers.strategy import artist_filtered_strategy, artist_id3_strategy
from core.meta.pipeline.helpers.analysis import choose_artist
from core.meta.pipeline.phase2.resolvers.resolver import resolve_song
from core.meta.repository.filtering import Filtering
from core.meta.enum.status import SongStatus
from core.meta.provider.deezer import FontManager
from core.meta.models.song import SongMetadata
from core.meta.repository.extract_metadata import ExtractMetadata
from core.meta.cache.cache_artists import CacheArtists
from core.meta.repository.metadata_repository import MetadataRepository
from core.services.account_manager import AccountManager   
from core.utils.path import AppPaths 

# imports gerais
from pathlib import Path
import aiohttp


async def resolve_no_artist_filtered_or_no_id3(
    id3_only_list : list[SongMetadata], 
    filtered_only_list : list[SongMetadata], 
    path : str
):
    from core.meta.pipeline.pipeline import Pipeline

    if (
        (
            id3_only_list is None and filtered_only_list is None
        ) or (
            len(filtered_only_list) == 0 and len(id3_only_list) == 0
        )
    ):
        print(f"[PIPELINE PHASE 2] Lista id3_only_list/filtered_only_list são None ou estão vazias. \nmedium: {id3_only_list} \niconsistente: {filtered_only_list}\n")
        return
    
    ARTISTS_PATH: Path = AppPaths.ACCOUNT / AccountManager.accounts_cache.get("current_account") / "images" / "artists"
    ALBUMS_PATH: Path = AppPaths.ACCOUNT / AccountManager.accounts_cache.get("current_account") / "images" / "albums"

    async with aiohttp.ClientSession() as session:

        fonts = FontManager(session)

        for song in filtered_only_list:

            best_item, best_score = await resolve_song(
                fonts = fonts,
                song = song,
                strategy = artist_filtered_strategy()
            )
            defined_artist: str = await choose_artist(
                score = best_score,
                best_item = best_item,
                song = song
            )


            song.set_defined_artist(
                Filtering.clean_feat(defined_artist)
            )
            song.set_artist_id(
                CacheArtists.resolve_id(
                    song.defined_artist
                ) if song.defined_artist is not None else None
            )
            song.set_score(best_score)
            song.set_potential_artists(
                [
                    best_item['artist']['name'] if best_item is not None else 'Desconhecido', 
                    song.id3_data["original_data"].get("artist_id3")
                ]
            )  
            song.set_song_path(path)

            
            if best_score >= 0.85:
                song.set_status(SongStatus.HIGH)
            elif 0.85 > best_score > 0.65:
                song.set_status(SongStatus.MEDIUM)
            else:
                song.set_status(SongStatus.LOW)

            print(f"[PIPELINE PHASE 2 FILTERED ONLY LIST] best_item: {best_item}\n")

            if best_item is not None:
                
                image_medium_artist_destination = MetadataRepository.download_image(
                    url = best_item['artist']['picture_medium'],
                    destination_path = ARTISTS_PATH / f"{song.artist_id}.jpg"
                )


                song.set_artist_metadata(
                    id_deezer = best_item['artist']['id'] or None,
                    img_m = image_medium_artist_destination,
                    img_b = Path(song.song_path) / song.mp3_file,
                    img_b_link = best_item['artist']['picture_big'] or None
                )
                

                image_medium_album_destination = MetadataRepository.download_image(
                    url = best_item['album']['cover_medium'],
                    destination_path = ALBUMS_PATH / f"{best_item['album']['title']}.jpg"
                )


                song.set_album_metadata(
                    name = best_item['album']['title'] or None,
                    id_deezer = best_item['album']['id'] or None,
                    img_m = image_medium_album_destination or None,
                    img_b = Path(song.song_path) / song.mp3_file,
                    img_b_link = best_item['album']['cover_big'] or None
                )


            ExtractMetadata.register_metadata_player(
                file_path = Path(song.song_path) / song.mp3_file,
                title = song.id3_data["filtered_data"].get("title") if song.id3_data["filtered_data"].get("title") is not None else song.mp3_file_filtered.get("title"),
                artist = song.defined_artist,
                album = song.album_metadata.get('name'),
                url_img_album_medium = None if best_item is None else best_item['album']['cover_medium'],
                url_img_album_big = song.album_metadata.get('big').get('link'),
                url_img_artista_medium = None if best_item is None else best_item['artist']['picture_medium'],
                url_img_artista_big = song.artist_metadata.get('big').get('link'),
                id_alb = song.album_metadata.get('id_deezer'),
                id_art = song.artist_metadata.get('id')
            )

        for song in id3_only_list:

            best_item, best_score = await resolve_song(
                fonts = fonts,
                song = song,
                strategy = artist_id3_strategy()
            )
            defined_artist = await choose_artist(
                score = best_score,
                best_item = best_item,
                song = song
            )


            song.set_defined_artist(
                Filtering.clean_feat(defined_artist)
            )
            song.set_artist_id(
                CacheArtists.resolve_id(
                    song.defined_artist
                ) if song.defined_artist is not None else None
            )
            song.set_score(best_score)
            song.set_potential_artists(
                [
                    best_item['artist']['name'] if best_item is not None else 'Desconhecido', 
                    song.id3_data["filtered_data"].get("artist_id3")
                ]
            )  
            song.set_song_path(path)

            
            if best_score >= 0.85:
                song.set_status(SongStatus.HIGH)
            elif 0.85 > best_score > 0.65:
                song.set_status(SongStatus.MEDIUM)
            else:
                song.set_status(SongStatus.LOW)

            print(f"[PIPELINE PHASE 2 ID3 ONLY LIST] best_item: {best_item}\n")

            if best_item is not None:
                
                image_medium_artist_destination = MetadataRepository.download_image(
                    url = best_item['artist']['picture_medium'],
                    destination_path = ARTISTS_PATH / f"{song.artist_id}.jpg"
                )


                song.set_artist_metadata(
                    id_deezer = best_item['artist']['id'] or None,
                    img_m = image_medium_artist_destination,
                    img_b = Path(song.song_path) / song.mp3_file,
                    img_b_link = best_item['artist']['picture_big'] or None
                )
                
                image_medium_album_destination = MetadataRepository.download_image(
                    url = best_item['album']['cover_medium'],
                    destination_path = ALBUMS_PATH / f"{best_item['album']['title']}.jpg"
                )


                song.set_album_metadata(
                    name = best_item['album']['title'] or None,
                    id_deezer = best_item['album']['id'] or None,
                    img_m = image_medium_album_destination or None,
                    img_b = Path(song.song_path) / song.mp3_file,
                    img_b_link = best_item['album']['cover_big'] or None
                )


                ExtractMetadata.register_metadata_player(
                    file_path = Path(song.song_path) / song.mp3_file,
                    title = song.id3_data["filtered_data"].get("title") if song.id3_data["filtered_data"].get("title") is not None else song.mp3_file_filtered.get("title"),
                    artist = song.defined_artist,
                    album = song.album_metadata.get('name'),
                    url_img_album_medium = best_item['album']['cover_medium'],
                    url_img_album_big = song.album_metadata.get('big').get('link'),
                    url_img_artista_medium = best_item['artist']['picture_medium'],
                    url_img_artista_big = song.artist_metadata.get('big').get('link'),
                    id_alb = song.album_metadata.get('id_deezer'),
                    id_art = song.artist_metadata.get('id')
                )


    await Pipeline.save_data({
        SongStatus.NO_ARTIST_FILTERED : id3_only_list,
        SongStatus.NO_ARTIST_ID3 : filtered_only_list
    })
    Pipeline.to_execute_callbacks(path)