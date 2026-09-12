# imports de back-end
from core.meta.provider.deezer import FontManager
from core.meta.models.song import SongMetadata


async def resolve_song(
    fonts: FontManager, 
    song: SongMetadata, 
    strategy: dict
):
    artist_for_search = strategy['artist_for_search'](song)

    result = await fonts.deezer.get_song(
        title = song.id3_data["filtered_data"].get("title"),
        artist = artist_for_search
    )

    print(f"[RESOLVE_SONG]: {song.id3_data['filtered_data'].get('title')} - {artist_for_search}")

    if not result.get('track'):
        return None, 0
    
    best_item = None
    best_score = 0

    for item in result['track']:
        score = strategy['calculate_score'](song, item)

        if score > best_score:
            best_score = score
            best_item = item
    
    print(f"[RESOLVE_SONG]: pós executar a seleção do melhor: {best_item}")
    return best_item, best_score