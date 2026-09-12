# mport de back-end
from core.meta.models.song import SongMetadata
from core.services.account_manager import AccountManager
from core.utils.path import AppPaths
from core.meta.repository.tasks import Task

# imports gerais
from mutagen import File, MutagenError
from mutagen.id3 import ID3, TIT2, TPE1, TALB, APIC, TXXX, ID3NoHeaderError
from mutagen.mp3 import MP3
from pathlib import Path
import asyncio, requests, base64


class ExtractMetadata:

    @classmethod
    def async_extract_metadata(cls, path: str | Path) -> dict[str, str | None]:
        """_summary_

        Args:
            path (str | Path): caminho completo da música. Ex.: C:/Users/barbo/Music/sua_musica.mp3

        Returns:
            dict[str, str | None]: Dicionário com o título, artista e capa da música extraída.
        """

        data: dict[str, str | None] = {
            "title" : None,
            "artist" : None,
            "cover" : None
        }

        # Validação de path, se vier como string ou outra forma tentará ser convertido para Path.
        if isinstance(path, str):
            audio_path = Path(path)
        elif not isinstance(path, Path):
            try:
                audio_path = Path(path)
            except (TypeError):
                print(f"Caminho incompatível, não foi possível converter: {path}")
                return data
            except Exception as error:
                print(f"Erro inesperado: {error}")
                return data
        else:
            audio_path = path

        cover_destination: Path = Path(
            AppPaths.ACCOUNT / AccountManager.accounts_cache.get("current_account") / "images" / "covers"
        )

        audio = File(audio_path, easy  = True)

        if audio:
            data["title"] = audio.get("title", [None])[0]
            data["artist"] = audio.get("artist", [None])[0]

        # Extração da cover (principalmente MP3)
        try:
            cover_destination.mkdir(
                parents = True, exist_ok = True
            )

            tags = ID3(audio_path)

            for tag in tags.values():

                if isinstance(tag, APIC):

                    cover_path = cover_destination / f"{audio_path.stem}.jpg"

                    with open(cover_path, "wb") as img:
                        img.write(tag.data)

                    data["cover"] = str(cover_path)
                    break
        except (ID3NoHeaderError, MutagenError):
            print(f"[EXTRACT METADATA] Arquivo não possuí tags ID3 ou não é um MP3 suportado.")
        except PermissionError:
            print(f"Sem permissão para gravar em {cover_destination}")
        except OSError as error:
            print(f"Erro de sistema ao salvar a capa do áudio {audio_path.name}: {error}")
        except Exception as error:
            f"Erro inesperado: {error}"

        return data

    @classmethod
    async def async_organize_data(
        cls, 
        mp3_file: str, 
        song_metadata_id3: dict | None, 
        original_artist_id3: str | None, 
        status: str, 
        song_path: Path,
        artist_id: str = "",
        playlist_id: str | None = None
    ) -> SongMetadata:
        """
            Organiza os dados retornados das filtragens e extrações de metadados
        Args:
            mp3_file (str): Nome integral do arquivo .mp3
            titulo_filtrado (dict | None): Dicionario do title filtrado senão None
            original_artist_id3 (str | None): String do artist filtrado ou None
            status (str): String para denominar as operações seguintes

        Returns:
            dict[str | None]: Dicionário organizados com todas as informações
        """
        return SongMetadata(
            song_id = Task.return_track_id(Path(song_path) / mp3_file),
            playlist_id = playlist_id,
            artist_id = artist_id,

            mp3_file = mp3_file,
            song_path = song_path,

            original_song_title = song_metadata_id3["original_title"] if song_metadata_id3 is not None else None,
            song_title_id3_filtered = song_metadata_id3["filtered_title"] if song_metadata_id3 is not None else None,
            song_artist_id3_filtered = song_metadata_id3["artist"] if song_metadata_id3 is not None else None,
            original_artist_id3 = original_artist_id3,

            status = status,
            mp3_file_title = None,
            mp3_file_artist = None,
            defined_artist = None,
            score = None
        ) 

    @classmethod
    async def async_extract(cls, path: Path) -> dict[str, str | None]:
        return await asyncio.to_thread(
            cls.async_extract_metadata,
            path
        )
    

    #   -----   EDIÇÃO E CAPTAÇÃO DE METADADOS NOVOS    -----
    @classmethod
    def register_metadata_player(
        cls,
        file_path: Path,
        title: str,
        artist: str,
        album: str,
        id_art : str | None = None,
        url_img_artista_medium : str | None = None,
        url_img_artista_big : str | None = None,
        id_alb : str | None = None,
        url_img_album_medium: str | None = None,
        url_img_album_big: str | None = None,
    ):
        """
            Função para registar os dados obtidos do pipeline diretamente em metadados nativos nos arquivos.

        Args:
            file_path (str): caminho completo do arquivo
            title (str): title final da filtragem
            artist (str): artist final atribuído
            album (str): álbum identificado
            url_img_artista_medium (str | None, optional): Imagem do artist identificado, caso exista. Defaults to None.
            url_img_artista_big (str | None, optional): Imagem do artist identificado, caso exista. Defaults to None.
            url_img_album_medium (str | None, optional): imagem do álbum identificado, caso exista. Defaults to None.
            url_img_album_big (str | None, optional): imagem do álbum identificado, caso exista. Defaults to None.
        """

        file_path = str(file_path)

        # abre o arquivo .mp3
        audio = MP3(file_path, ID3 = ID3)

        # Se não tiver tags -> cria elas.
        try:
            audio.add_tags()
        except:
            pass
        
        # acessando as tags
        tags = audio.tags

        # limpar apenas textos antigos
        tags.delall("TIT2")
        tags.delall("TPE1")
        tags.delall("TALB")
        tags.delall("TXXX:PLAYER_PIPELINE")
        tags.delall("TXXX:PLAYER_ARTIST_ID")
        tags.delall("TXXX:PLAYER_ALBUM_ID")

        # limpar imagens do player (matém cover original)
        for tag in list(tags.values()):
            if isinstance(tag, APIC) and tag.desc.startswith("PLAYER_"):
                tags.delall(tag.HashKey)

        print(title, artist, album)

        # escrever novos metadados
        if title is not None:
            tags.add(TIT2(encoding = 3, text = title))
        
        if artist is None:
            tags.add(TPE1(encoding = 3, text = "Artista Desconhecido"))
        else:
            tags.add(TPE1(encoding = 3, text = artist))

        if album is None:
            tags.add(TALB(encoding = 3, text = "Album Desconhecido"))
        else:
            tags.add(TALB(encoding = 3, text = album))

        # -------- função download --------
        def download(url):
            """
                Baixa as imagens da API

            Args:
                url (str): link direcionado da API da Deezer da respectiva imagem

            Returns:
                str: bytes da imagem
            """
            
            try:
                response = requests.get(url, timeout = 10)
                return response.content
            except:
                return None
        
        # _____ inserir imagem artist _____
        if url_img_artista_medium is not None:
            _img_artist_medium = download(url_img_artista_medium)
            
            if _img_artist_medium is not None:
                tags.add(APIC(
                    encoding = 3,
                    mime = "image/jpeg",
                    type = 7,
                    desc = "PLAYER_ARTIST_MEDIUM",
                    data = _img_artist_medium   
                ))
        
        if url_img_artista_big is not None:
            _img_artist_big = download(url_img_artista_big)
            
            if _img_artist_big is not None:
                tags.add(APIC(
                    encoding = 3,
                    mime = "image/jpeg",
                    type = 7,
                    desc = "PLAYER_ARTIST_BIG",
                    data = _img_artist_big
                ))
            

        # _____ inserir imagem album _____
        if url_img_album_medium is not None:
            _img_album_medium = download(url_img_album_medium)
            
            if _img_album_medium is not None:
                tags.add(APIC(
                    encoding = 3,
                    mime = "image/jpeg",
                    type = 4,
                    desc = "PLAYER_ALBUM_MEDIUM",
                    data = _img_album_medium
                ))
                
        if url_img_album_big is not None:
            _img_album_big = download(url_img_album_big)
            
            if _img_album_big is not None:
                tags.add(APIC(
                    encoding = 3,
                    mime = "image/jpeg",
                    type = 4,
                    desc = "PLAYER_ALBUM_BIG",
                    data = _img_album_big
                ))

        if id_art is not None:
            tags.add(TXXX(
                encoding = 3,
                desc = "PLAYER_ARTIST_ID",
                text = str(id_art)
            ))

        if id_alb is not None:
            tags.add(TXXX(
                encoding = 3,
                desc = "PLAYER_ALBUM_ID",
                text = str(id_alb)
            ))

        # campo validador
        tags.add(
            TXXX(
                encoding = 3,
                desc = "PLAYER_PIPELINE",
                text = "PROCESSADO"
            )
        )

        audio.save()

    @classmethod
    def music_already_processed(cls, path: Path) -> bool:
        """
            Verifica se o campo validador adicionado pela def registrar_metadados_player já alterou essa música em algum momento.

        Args:
            path (str): path completo do arquivo MP3

        Returns:
            bool: True | False
        """

        try:
            tags = ID3(str(path))

            if "TXXX:PLAYER_PIPELINE" in tags:
                return True
        except:
            pass

        return False
    
    @classmethod
    def extract_metadata_player(cls, file_path: Path) -> dict[str, str | None]:
        """
            Função para extrair os dados (metadados) que forma atribuídos manualmente pelo player

        Args:
            file_path (Path): caminho completo do arquivo MP3

        Returns:
            dict: dicionário contendo as informações extraídas do arquivo.
        """

        result: dict[str, str | None] = {
            "title": None,

            # nome do álbum e do artista
            "artist": None,
            "album": None,

            "validate_pipeline": False,
            "cover": None,
            
            "artist_id" : None,
            "image_medium_artist": None,
            "image_big_artist": None,

            "album_id" : None,
            "image_medium_album": None,
            "image_big_album": None
        }

        audio = MP3(str(file_path), ID3 = ID3)
        tags = audio.tags

        if not tags:
            return result

        if "TIT2" in tags:
            result["title"] = str(tags["TIT2"])

        if "TPE1" in tags:
            result["artist"] = str(tags["TPE1"])

        if "TALB" in tags:
            result["album"] = str(tags["TALB"])

        if "TXXX:PLAYER_PIPELINE" in tags:
            result["validate_pipeline"] = True

        if "TXXX:PLAYER_ARTIST_ID" in tags:
            tag = tags["TXXX:PLAYER_ARTIST_ID"]

            if tag.text:
                result["artist_id"] = tag.text[0]

        if "TXXX:PLAYER_ALBUM_ID" in tags:
            tag = tags["TXXX:PLAYER_ALBUM_ID"]

            if tag.text:
                result["album_id"] = tag.text[0]
        
        # percorre todas as imagens existentes.
        for tag in tags.values():

            if isinstance(tag, APIC):
                if tag.type == 3:
                    result["cover"] = {
                        "mime": tag.mime,
                        "bytes_size": len(tag.data)
                    }
                    
                # _____ artist _____
                elif tag.desc == "PLAYER_ARTIST_MEDIUM":
                    result["image_medium_artist"] = {
                        "mime": tag.mime,
                        "bytes_size": len(tag.data)
                    }
                elif tag.desc == "PLAYER_ARTIST_BIG":
                    result["image_big_artist"] = {
                        "mime": tag.mime,
                        "bytes_size": len(tag.data)
                    }
                
                # _____ album _____
                elif tag.desc == "PLAYER_ALBUM_MEDIUM":
                    result["image_medium_album"] = {
                        "mime": tag.mime,
                        "bytes_size": len(tag.data)
                    }
                elif tag.desc == "PLAYER_ALBUM_BIG":
                    result["image_big_album"] = {
                        "mime": tag.mime,
                        "bytes_size": len(tag.data)
                    }

        return result
    
    @classmethod
    def extact_images_mp3(
        cls, 
        file_path: str, 
        album_name: dict, 
        cover_name: str, 
        artist_id : str | None = None
    ) -> dict[str, Path | None]:
        """
            Extrai as imagens do arquivo MP3

        Args:
            file_path (str): caminho completo do MP3
            destination_path (str): Pasta destinada a salvar as imagens
        """

        audio = MP3(file_path, ID3 = ID3)
        tags = audio.tags

        if not tags:
            return

        dic: dict[str, Path | None] = {
            "cover" : None,
            "art" : None,
            "alb" : None
        }

        # percorre todas as imagens imbutidas no arquivo 
        for tag in tags.values():

            destination_path = None

            if isinstance(tag, APIC):
                # definir name do arquivo

                if tag.type == 3:
                    destination_path = AppPaths.ACCOUNT / AccountManager.accounts_cache.get("current_account") / "images" / "covers" / f"{cover_name}.jpg"
                    dic["cover"] = destination_path
                elif tag.desc == "PLAYER_ARTIST_MEDIUM":
                    destination_path = AppPaths.ACCOUNT / AccountManager.accounts_cache.get("current_account") / "images" / "artists" / f"{artist_id}.jpg"
                    dic["art"] = destination_path
                elif tag.desc == "PLAYER_ALBUM_MEDIUM":
                    destination_path = AppPaths.ACCOUNT / AccountManager.accounts_cache.get("current_account") / "images" / "albums" / f"{album_name}.jpg"
                    dic["alb"] = destination_path
                else:
                    continue

                # grava a imagem no diretório
                if destination_path is not None:
                    with open(destination_path, "wb") as img:
                        img.write(tag.data)
                else:
                    raise(
                        f"Imágem inválida para ser salva: {destination_path}"
                    )

        return dic
    
    @classmethod
    def load_image_big_base64(cls, file_path: str, type: str):        
        """
            Função para carregar as imagens do type big sem salvá-las fisicamente em algum diretório do dispositivo.

        Args:
            file_path (str): _description_
            type (str): _description_
        """
        
        audio = MP3(file_path, ID3 = ID3)
        tags = audio.tags
        
        if not tags:
            return None
        
        alvo = {
            "artist" : "PLAYER_ARTIST_BIG",
            "album" : "PLAYER_ALBUM_BIG"
        }.get(type)
        
        for tag in tags.values():
            if isinstance(tag, APIC) and tag.desc == alvo:
                base64_str = base64.b64encode(tag.data).decode("utf-8")
                return base64_str
        return None