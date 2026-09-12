# imports de back-end
from core.meta.repository.filtering import Filtering
from core.meta.enum.status import SongStatus
from core.meta.provider.deezer import FontManager
from core.meta.models.song import SongMetadata
from core.meta.repository.metadata_repository import MetadataRepository
from core.services.account_manager import AccountManager
from core.meta.cache.cache_artists import CacheArtists
from core.meta.repository.extract_metadata import ExtractMetadata
from core.utils.path import AppPaths
from core.meta.pipeline.helpers.analysis import analyze_consensus, calculate_phase3_score_with_artist, calculate_score_title_only_phase_3, sort_artists_by_title_only

# imports gerais
from pathlib import Path
import aiohttp


class Phase3:

    """  RESOLUÇÃO  """
    @classmethod
    async def _resolve_phase_3(cls, fonts: FontManager, filter: dict):
        result = await fonts.deezer.get_song(
            title = filter["filtered_title"],
            artist = filter["artist"]
        )

        if not result or not result.get("track"):
            return None, 0, None

        itens = result["track"]

        # 🔹 CASO 1: TEM ARTISTA NO FILENAME
        if filter["artist"]:
            best_item = None
            best_score = 0

            for item in itens:
                score = calculate_phase3_score_with_artist(filter, item)

                if score > best_score:
                    best_score = score
                    best_item = item

            return best_item, best_score, None

        # 🔹 CASO 2: APENAS TÍTULO
        else:
            from core.meta.pipeline.phase2.phase_2 import Phase2
            
            processed_items = []

            for item in itens:
                score = calculate_score_title_only_phase_3(filter, item)
                item["calculated_score"] = score
                processed_items.append(item)

            itens_ordenados = sorted(
                processed_items,
                key = lambda x: x["calculated_score"],
                reverse = True
            )

            top5 = itens_ordenados[:5]

            sim_1 = top5[0]["calculated_score"]
            sim_2 = top5[1]["calculated_score"] if len(top5) > 1 else 0
            gap = sim_1 - sim_2
            consensus, artista_dominante = analyze_consensus(top5)

            defined_artist, status = await sort_artists_by_title_only(
                gap = gap,
                sim_1 = sim_1,
                top5 = top5
            )

            return top5[0], sim_1, {
                "status": status,
                "gap": gap,
                "sim_1": sim_1,
                "sim_2": sim_2,
                "consensus": consensus,
                "defined_artist": defined_artist
            }


    """  CHAMADA DA FASE 3  """
    @classmethod
    async def phase_3(cls, incomplete_list: list[SongMetadata], path: str):
        from core.meta.pipeline.pipeline import Pipeline

        ARTISTS_PATH: Path = AppPaths.ACCOUNT / AccountManager.accounts_cache.get("current_account") / "images" / "artists"
        ALBUMS_PATH: Path = AppPaths.ACCOUNT / AccountManager.accounts_cache.get("current_account") / "images" / "albums"
        
        async with aiohttp.ClientSession() as session:
            fonts = FontManager(session)

            for song in incomplete_list:

                song.set_song_path(path)

                filter = await Filtering.async_filter_title(song.mp3_file)

                song.set_mp3_file_filtered(
                    title = filter["filtered_title"],
                    artist = filter["artist"]
                )

                best_item, best_score, title_only_data = await cls._resolve_phase_3(fonts, filter)

                print(f"[PIPELINE PHASE 3] best_item: {best_item}\n")
                
                if best_item is None:
                    song.set_status(SongStatus.LOW)
                    song.set_score(0)
                    song.set_defined_artist(
                        Filtering.clean_feat(
                            filter["artist"]
                        ) or "Artista Desconhecido"
                    )  
                    song.set_artist_id(
                        CacheArtists.resolve_id(
                            song.defined_artist
                        ) if song.defined_artist is not None else None
                    )
                    continue

                # 🔹 CASO APENAS TÍTULO
                if title_only_data:
                    song.set_defined_artist(
                        Filtering.clean_feat(
                            best_item["artist"]["name"]
                        ) or "Artista Desconhecido"
                    )  
                    song.set_artist_id(
                        CacheArtists.resolve_id(
                            song.defined_artist
                        ) if song.defined_artist is not None else None
                    )
                    song.set_status(title_only_data["status"])
                    song.set_score(title_only_data["sim_1"])
                    song.set_gap(title_only_data["gap"])
                    song.set_sim_1(title_only_data["sim_1"])
                    song.set_sim_2(title_only_data["sim_2"])
                    song.set_consensus(title_only_data["consensus"])

                    
                    artist_image_medium_destination = MetadataRepository.download_image(
                        url = best_item["artist"]["picture_medium"],
                        destination_path = ARTISTS_PATH / f"{song.artist_id}.jpg"
                    )
                    song.set_artist_metadata(
                        id_deezer = best_item["artist"]["id"] or None,
                        img_m = artist_image_medium_destination,
                        img_b = Path(song.song_path) / song.mp3_file,
                        img_b_link = best_item["artist"]["picture_big"] or None
                    )
                    
                    album_image_medium_destination = MetadataRepository.download_image(
                        url = best_item["album"]["cover_medium"],
                        destination_path = ALBUMS_PATH / f"{best_item['album']['title']}.jpg"
                    )
                    song.set_album_metadata(
                        name = best_item["album"]["title"] or None,
                        id_deezer = best_item["album"]["id"] or None,
                        img_m = album_image_medium_destination or None,
                        img_b = Path(song.song_path) / song.mp3_file,
                        img_b_link = best_item["album"]["cover_big"] or None
                    )

                    ExtractMetadata.register_metadata_player(
                        file_path = Path(song.song_path) / song.mp3_file,
                        title = song.id3_data["filtered_data"].get("title") if song.id3_data is not None else song.mp3_file_filtered.get("title"),
                        artist = song.defined_artist,
                        album = song.album_metadata.get("name"),
                        url_img_album_medium = best_item["album"]["cover_medium"],
                        url_img_album_big = song.album_metadata.get("big").get("link"),
                        url_img_artista_medium = best_item["artist"]["picture_medium"],
                        url_img_artista_big = song.artist_metadata.get("big").get("link"),
                        id_alb = song.album_metadata.get("id_deezer"),
                        id_art = song.artist_metadata.get("id")
                    )
                # 🔹 CASO COM ARTISTA
                else:

                    song.set_defined_artist(
                        Filtering.clean_feat(
                            best_item["artist"]["name"]
                        ) or "Artista Desconhecido"
                    )  
                    song.set_artist_id(
                        CacheArtists.resolve_id(
                            song.defined_artist
                        ) if song.defined_artist is not None else None
                    )

                    song.set_score(best_score)

                    if best_score >= 0.85:
                        song.set_status(SongStatus.HIGH)
                    elif 0.85 > best_score > 0.65:
                        song.set_status(SongStatus.MEDIUM)
                    else:
                        song.set_status(SongStatus.LOW)       

                    print(f"[PIPELINE PHASE 3] best_item: {best_item}\n")

                    artist_image_medium_destination = MetadataRepository.download_image(
                        url = best_item["artist"]["picture_medium"],
                        destination_path = ARTISTS_PATH / f"{song.artist_id}.jpg"
                    )
                    song.set_artist_metadata(
                        id_deezer = best_item["artist"]["id"] or None,
                        img_m = artist_image_medium_destination,
                        img_b = Path(song.song_path) / song.mp3_file,
                        img_b_link = best_item["artist"]["picture_big"] or None
                    )
                    
                    album_image_medium_destination = MetadataRepository.download_image(
                        url = best_item["album"]["cover_medium"],
                        destination_path = ALBUMS_PATH / f"{best_item['album']['title']}.jpg"
                    )
                    song.set_album_metadata(
                        name = best_item["album"]["title"] or None,
                        id_deezer = best_item["album"]["id"] or None,
                        img_m = album_image_medium_destination or None,
                        img_b = Path(song.song_path) / song.mp3_file,
                        img_b_link = best_item["album"]["cover_big"] or None
                    )

                    ExtractMetadata.register_metadata_player(
                        file_path = Path(song.song_path) / song.mp3_file,
                        title = song.id3_data["filtered_data"].get("title") if song.id3_data is not None else song.mp3_file_filtered.get("title"),
                        artist = song.defined_artist,
                        album = song.album_metadata.get("name"),
                        url_img_album_medium = best_item["album"]["cover_medium"],
                        url_img_album_big = song.album_metadata.get("big").get("link"),
                        url_img_artista_medium = best_item["artist"]["picture_medium"],
                        url_img_artista_big = song.artist_metadata.get("big").get("link"),
                        id_alb = song.album_metadata.get("id_deezer"),
                        id_art = song.artist_metadata.get("id")
                    )

        await Pipeline.save_data({
            SongStatus.INCOMPLETE : incomplete_list
        })
        Pipeline.to_execute_callbacks(path)