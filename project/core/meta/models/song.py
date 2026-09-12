# import de back-end
from core.meta.enum.status import SongStatus

# import geral
from pathlib import Path


class SongMetadata:
    
    def __init__(
        self,

        # IDs a serem salvos
        song_id: str,
        playlist_id: str,
        artist_id: str | None,
        
        # arquivo original e path do arquivo (separados, tem de ser fazer a junção deles)
        mp3_file: str,
        song_path: Path | None,
        
        # metadados do tipo ID3
        original_song_title: str | None,
        original_artist_id3: str | None,
        song_title_id3_filtered: str | None,
        song_artist_id3_filtered: str | None,
        
        # MP3
        mp3_file_title: str | None,
        mp3_file_artist: str | None,

        # artist final, definido
        defined_artist: str | None,
                
        # Classificações do processo (sobretudo em casos que contém apenas o título, sem nenhuma referência de artist)
        score: float | int = 0,
        status: SongStatus = None,
        sim_1: None | float = None,
        sim_2: None | float = None,
        gap: None | float = None,
        consensus: None | float = None,

        list_of_potential_artists: list[dict] = [],

        # Dados artist
        artist_metadata: dict[str, str | Path | None] = {
            "id_deezer" : None,
            "medium" : None, # str do path da img medium salva
            "big" : {
                "link" : None,
                "path" : None # str da musica sendo salva.
            } 
        },

        # Dados álbum
        album_metadata: dict[str, str | Path | None] = {
            "id_deezer" : None, 
            "name" : None, 
            "medium" : None, 
            "big" : {
                "link" : None,
                "path" : None
            }
        }
    ):
        self.song_id = song_id
        self.song_path = song_path
        self.playlist_id = playlist_id
        self.artist_id = artist_id

        # name do .mp3
        self.mp3_file = mp3_file

        self.mp3_file_filtered: dict[str, str | None] = {
            "title" : mp3_file_title,
            "artist" : mp3_file_artist
        }
        # titulo extraído (ID3)
        self.id3_data: dict[str, dict[str, str | None]] = {
            "original_data" : {
                "title" : original_song_title,
                "artist_id3" : original_artist_id3
            },
            "filtered_data" : {
                "title" : song_title_id3_filtered,
                "artist" : song_artist_id3_filtered
            }
        } 
                
        # Operação
        self.defined_artist = defined_artist
        self.score = score
        self.status = status

        # Operações apenas titulo
        self.sim_1 = sim_1
        self.sim_2 = sim_2
        self.gap = gap
        self.consensus = consensus
        self.list_of_potential_artists = list_of_potential_artists

        # Imagens
        self.artist_metadata = artist_metadata
        self.album_metadata = album_metadata

    def set_defined_artist(self, artist: str):
        self.defined_artist = artist
        
    def set_status(self, status: str):
        self.status = status
    
    def set_score(self, score: float | int):
        self.score = score
    
    def set_sim_1(self, sim_1: None | float):
        self.sim_1 = sim_1
    
    def set_sim_2(self, sim_2: None | float):
        self.sim_2 = sim_2
    
    def set_gap(self, gap: None | float):
        self.gap = gap

    def set_consensus(self, consensus: None | float):
        self.consensus = consensus
    
    def set_potential_artists(self, artistas: list):
        self.list_of_potential_artists.extend(artistas)
    
    def set_mp3_file_filtered(self, title: str | None, artist: str | None):
        self.mp3_file_filtered = {
            "title" : title,
            "artist" : artist
        }
    
    def set_artist_metadata(
        self, 
        id_deezer: str | None,
        img_m: Path, # path
        img_b: Path, # caminho_arquivo
        img_b_link: str | None
    ):
        self.artist_metadata = {
            "id" : id_deezer,
            "medium" : str(img_m),
            "big" : {
                "link" : img_b_link,
                "path" : str(img_b)
            }
        }

    def set_album_metadata(
        self, 
        name: str | None,
        id_deezer: str | None,
        img_m: Path,
        img_b: Path,
        img_b_link: str | None
    ):
        self.album_metadata = {
            "id_deezer" : id_deezer,
            "name" : name,
            "medium" : str(img_m),
            "big" : {
                "link" : img_b_link,
                "path" : str(img_b)
            }
        }
        
    def set_song_path(self, path: Path):
        self.path = path

    def set_artist_id(self, id: str):
        self.artist_id = id