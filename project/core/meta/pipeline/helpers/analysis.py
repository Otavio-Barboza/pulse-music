# imports de back-end
from core.meta.models.song import SongMetadata
from core.meta.repository.tasks import Task
from core.meta.repository.filtering import Filtering
from core.meta.enum.status import SongStatus


"""  ANÁLISES DA FASE 2  """

def calculate_score_title_only(song: SongMetadata, item: dict):
    similarity_title = Task.similarity(
        song.id3_data["filtered_data"].get("title").lower().strip(),
        item['title'].lower().strip()
    )            
    popularity = item.get('rank', 0) / 1_000_000

    return (0.75 * similarity_title + 0.15 * popularity)


def analyze_consensus(itens):
    artist = [i['artist']['name'] for i in itens[:5]]
    dominant_artist = max(set(artist), key = artist.count)
    frequency = artist.count(dominant_artist)
    consensus = frequency / len(artist)
    
    return consensus, dominant_artist


async def choose_artist(
    score: float, 
    best_item: dict, 
    song: SongMetadata
):
    if score >= 0.85 and best_item is not None:
        return best_item['artist']['name']
    elif 0.85 > score > 0.65:
        return song.id3_data["filtered_data"].get("artist") or song.id3_data["original_data"].get("artist_id3")
    else:
        return song.id3_data["original_data"].get("artist_id3") or song.id3_data["filtered_data"].get("artist")

    
"""  ANÁLISES DA FASE 3  """

def calculate_phase3_score_with_artist(filter: dict, item: dict) -> float:
    return (
        0.6 * Task.similarity(
            filter["filtered_title"],
            item["title"]
        ) + 0.4 * Task.similarity(
            Filtering.clean_feat(filter["artist"]),
            item["artist"]["name"]
        )
    )


def calculate_score_title_only_phase_3(filter: dict, item: dict):
    title_similarity = Task.similarity(
        filter["filtered_title"].lower().strip(),
        item["title"].lower().strip()
    )
    polarity = item.get("rank", 0) / 1_000_000

    return (0.75 * title_similarity + 0.15 * polarity)


async def sort_artists_by_title_only(gap, sim_1, top5) -> str | SongStatus:
    artist = top5[0]["artist"]["name"]

    if sim_1 >= 0.85 and gap >= 0.05:
        return artist, SongStatus.HIGH
    elif sim_1 >= 0.80 and gap >= 0.02:
        return artist, SongStatus.MEDIUM
    else:
        return artist, SongStatus.LOW