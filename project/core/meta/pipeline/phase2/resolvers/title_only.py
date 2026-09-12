from core.meta.pipeline.helpers.analysis import analyze_consensus, calculate_score_title_only, sort_artists_by_title_only
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


async def resolve_title_only(
    title_only_list: list[SongMetadata], 
    path: Path
):
    from core.meta.pipeline.pipeline import Pipeline

    if (
        title_only_list is None
        or len(title_only_list) == 0
    ):
        print(f"[PIPELINE PHASE 2] Lista apenas título é None ou está vaiza: {title_only_list}")
        return
    
    ARTISTS_PATH: Path = AppPaths.ACCOUNT / AccountManager.accounts_cache.get("current_account") / "images" / "artists"
    ALBUMS_PATH: Path = AppPaths.ACCOUNT / AccountManager.accounts_cache.get("current_account") / "images" / "albums"

    async with aiohttp.ClientSession() as session:

        fonts = FontManager(session)

        for song in title_only_list:

            result = await fonts.deezer.get_song(
                title = song.id3_data["filtered_data"].get("title"),
                artist = None
            )


            if not result or not result.get("track"):
                song.set_status(SongStatus.LOW)
                song.set_defined_artist("Artista Desconhecido")
                song.set_artist_id(None)
                song.set_score(0)
                continue


            itens = []


            for item in result['track']:
                score = calculate_score_title_only(song = song, item = item)
                item['score_calculado'] = score
                itens.append(item)

            
            ordered_itens = sorted(
                itens,
                key = lambda x: x['score_calculado'],
                reverse = True
            )

            # itens da deezer
            possibilities = [
                {
                    'id_deezer' : item_ord['artist']['id'], 
                    'name' : item_ord['artist']['name'], 
                    'score' : item_ord['score_calculado']
                } for item_ord in ordered_itens
            ]

            
            song.set_potential_artists(possibilities)

            
            top5 = ordered_itens[:5]
            sim_1 = top5[0]['score_calculado']
            sim_2 = top5[1]['score_calculado'] if len(top5) > 1 else 0
            gap = sim_1 - sim_2
            consensus, dominant_artist = analyze_consensus(top5)
            defined_artist, status_artista_final = await sort_artists_by_title_only(
                gap = gap, sim_1 = sim_1, top5 = top5
            )


            song.set_defined_artist(
                Filtering.clean_feat(defined_artist)
            )
            song.set_artist_id(
                CacheArtists.resolve_id(
                    song.defined_artist
                ) if song.defined_artist is not None else None
            ) 
            song.set_consensus(consensus)
            song.set_gap(gap)
            song.set_sim_1(sim_1)
            song.set_sim_2(sim_2)
            song.set_status(status_artista_final)
            song.set_song_path(path)

            print(f"[PIPELINE PHASE 2 TITLE ONLY] best_item: {top5}\n")

            image_medium_artist_destination = MetadataRepository.download_image(
                url = top5[0]['artist']['picture_medium'],
                destination_path = ARTISTS_PATH / f"{song.artist_id}.jpg"
            )


            song.set_artist_metadata(
                id_deezer = top5[0]['artist']['id'] or None,
                img_m = image_medium_artist_destination,
                img_b = Path(song.song_path) / song.mp3_file,
                img_b_link = top5[0]['artist']['picture_big'] or None
            )

            
            image_medium_album_destination = MetadataRepository.download_image(
                url = top5[0]['album']['cover_medium'],
                destination_path = ALBUMS_PATH / f"{top5[0]['album']['title']}.jpg"
            )


            song.set_album_metadata(
                name = top5[0]['album']['title'] or None,
                id_deezer = top5[0]['album']['id'] or None,
                img_m = image_medium_album_destination or None,
                img_b = Path(song.song_path) / song.mp3_file,
                img_b_link = top5[0]['album']['cover_big'] or None
            )


            ExtractMetadata.register_metadata_player(
                file_path = Path(song.song_path) / song.mp3_file,
                title = song.id3_data["filtered_data"].get("title") if song.id3_data["filtered_data"].get("title") is not None else song.mp3_file_filtered.get("title"),
                artist = song.defined_artist,
                album = song.album_metadata.get('name'),
                url_img_album_medium = top5[0]['album']['cover_medium'],
                url_img_album_big = song.album_metadata.get('big').get('link'),
                url_img_artista_medium = top5[0]['artist']['picture_medium'],
                url_img_artista_big = song.artist_metadata.get('big').get('link'),
                id_alb = song.album_metadata.get('id_deezer'),
                id_art = song.artist_metadata.get('id')
            )
            
    await Pipeline.save_data({
        SongStatus.TITLE_ONLY : title_only_list
    })
    Pipeline.to_execute_callbacks(path)