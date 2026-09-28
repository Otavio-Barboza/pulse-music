# imports de back-end
from core.lyrics.translate.translator import Translator
from core.lyrics.cache.cache_lyrics import CacheLyrics
from core.lyrics.translate.language_detect import language_detect
from core.services.account_manager import AccountManager
from core.utils.utils import Utils
from core.utils.path import AppPaths
from core.information.service.information_service import InformationService

# import geral
from deep_translator.exceptions import TranslationNotFound, TooManyRequests
import requests, asyncio, lyricsgenius


class LyricsServices:

    expanded_screen: bool = False
    
    genius = None
    translator = Translator()

    AVAILABLE_LANGUAGES: dict[str, str] = translator.get_supported_languages(as_dict = True)

    callbacks = {}

    # callbacks, registros e chamadas
    @classmethod
    def register_callback(cls, event: str, callback: callable):
        if event not in cls.callbacks:
            cls.callbacks[event] = []
        cls.callbacks[event].append(callback)

    @classmethod
    def notify(cls, data, event: str):
        for callback in cls.callbacks.get(event, []):
            callback(data)

    @classmethod
    def initializate_genius(cls) -> str:
        cls.genius = lyricsgenius.Genius(
            access_token = InformationService.get("GENIUS"),
            response_format = "plain",
            timeout = 15,
            sleep_time = 0.2,
            remove_section_headers = True,
            skip_non_songs = True,
            excluded_terms = ["(Remix)", "(Live)"],
            replace_default_terms = False,
            retries = 0,
            user_agent = "",
            proxy = None
        )
        print(f"[LYRICS SERVICE]: genius inicializado: {cls.genius}")
    
    @classmethod
    async def notify_callback_lyrics(cls, data, event: str):
        for callback in cls.callbacks.get(event, []):
            result = callback(data)

            if asyncio.iscoroutine(result):
                await result


    # setters
    @classmethod
    def set_expanded_screen(cls, valor: bool):
        cls.expanded_screen = valor

    @classmethod
    def set_language_target(cls, target: str):
        cls.translator.target = target
            
            
    # Operações, gets e splits
    def split_lyric(lyric: str, max_length: int = 500) -> list[str]:
        lines = lyric.splitlines()

        chunks = []
        current_chunk = ""

        for line in lines:
            separator = "\n" if current_chunk else ""
            new_chunk = current_chunk + separator + line

            if len(new_chunk) <= max_length:
                current_chunk = new_chunk
                continue

            if current_chunk:
                chunks.append(current_chunk)

            # Caso uma linha sozinha ultrapasse o limite
            while len(line) > max_length:
                chunks.append(line[:max_length])
                line = line[max_length:]

            current_chunk = line

        if current_chunk:
            chunks.append(current_chunk)

        return chunks
    
    @classmethod
    async def get_lyric(cls, data: dict) -> str | None:
        try:    
            if data.get("key") in CacheLyrics.lyric:
                return
            
            song = await asyncio.to_thread(
                cls.genius.search_song,
                title = data.get("name"),
                artist = data.get("artist")
            )
            
            if not song:
                return

            original_lyric = await asyncio.to_thread(
                language_detect,
                song.lyrics
            )
            
            await cls.save_lyric(
                key_song = data.get("key"),
                lyric = song.lyrics,
                original_lyric = language_detect(song.lyrics)
            )

            CacheLyrics.load_cache()

            if cls.expanded_screen:
                cls.notify(
                    event = "actualization_lyric",
                    data = None
                )

        except requests.exceptions.Timeout:
            print("Timeout ao buscar lyric.")
            return
        except Exception as erro:
            print(f"Erro: {erro}")
            return 
    
    @classmethod
    async def translate(cls, lyric: str) -> str | None:
        """
        _summary_: Realiza a tradução de forma assíncrona.
        
        O deep_translator continua sendo síncrono internamente, portanto sua execução é tranferida para uma thread.

        Args:
            lyric (str): letra da música completa para tradução

        Returns:
            str | None: Retorna a letra (str) se sucedida a tradução, caso contrário retornará None, como um identificador de falha.
        """
        
        # Identificação do idioma
        _source: str = await asyncio.to_thread(
            language_detect,
            lyric
        )
        
        if (    
            _source is None
            or cls.translator.target is None
        ):
            return
        
        cls.translator.source = _source


        # tratamento das tentativas de busca pela letra da música.
        max_attempts: int = 5
        timeout: int = 15
        retry_delay: int = 5

        chunks = cls.split_lyric(lyric)

        for attempt in range(1, max_attempts + 1):
            
            try:       
                translated_chunks: list[str] = []

                for chunk in chunks:        
                    # informar que a tradução está sendo realizada.
                    translated_lyric: str | None = await asyncio.wait_for(
                        asyncio.to_thread(
                            cls.translator.translate,
                            chunk
                        ),
                        timeout = timeout
                    ) 
                    
                    if (
                        translated_lyric is None
                        or translated_lyric.startswith("Error ")
                    ):
                        raise TranslationNotFound(lyric)
                    
                    translated_chunks.append(translated_lyric)

                return "\n".join(translated_chunks)
            except (
                TranslationNotFound, 
                asyncio.TimeoutError
            ):
                if attempt >= max_attempts:
                    return 
            except TooManyRequests:
                print("Limite de requisições atingido. Aguardando...")
                await asyncio.sleep(10)
                
            await asyncio.sleep(retry_delay)
        else:
            return None


    # Armazenamento da letra musical
    @classmethod
    async def save_lyric(cls, lyric: str, key_song: str, original_lyric: str):
        existing_letters = await Utils.async_load_json(
            AppPaths.ACCOUNT / AccountManager.accounts_cache.get("current_account") / "music" / "lyrics.json"
        )

        existing_letters[key_song] = {
            "original_lyric" : lyric,
            "original_language" : original_lyric,
            "translations" : []
        }

        await Utils.async_update_json(
            data = existing_letters, 
            path =  AppPaths.ACCOUNT / AccountManager.accounts_cache.get("current_account") / "music" / "lyrics.json"
        )

    @classmethod
    def update_translations(cls, key_song: str, new_language: str, new_lyric: str):
        existing_letters = Utils.sync_load_json(
            AppPaths.ACCOUNT / AccountManager.accounts_cache.get("current_account") / "music" / "lyrics.json"
        )

        if not any(
            translation["language"] == new_language
            for translation in existing_letters[key_song]["translations"]
        ):
            existing_letters[key_song]["translations"].append({
                "language" : new_language,
                "lyric" : new_lyric
            })
        
        Utils.sync_update_json(
            data = existing_letters, 
            path = AppPaths.ACCOUNT / AccountManager.accounts_cache.get("current_account") / "music" / "lyrics.json"
        )


    # start da tradução da letra
    @classmethod
    async def start_translation(cls, language: str):
        from core.song.controller.reproduction_manager import ReproductionManager

        # Parte 1: Se existir a letra já traduzida para o idioma definido, obtém ela e a retorna. 
        
        # Senão tiver nenhuma música definida, não tem nada para traduzir
        if ReproductionManager.state.current_song is None:
            return "Nenhuma letra carregada para tradução"


        # Tenta buscar a letra com base na linguagem definida.
        existing_translated_lyric = CacheLyrics.return_translated_lyric(language)

        # Se existir a letra, retorna ela.
        if existing_translated_lyric is not None:
            return existing_translated_lyric


        # Parte 2: senão é efetuada a tentativa de tradução da letra.

        # pega a letra original
        lyric = CacheLyrics.return_lyric()

        # Senão houver diz que não encontrou
        if not lyric:
            return "A letra musical não foi encontrada. Portanto, não é possível traduzir!"

        cls.notify(
            event = "actualization_status_translation_lyric",
            data = "Traduzindo a letra, aguarde..."
        )
        
        # traduz a letra
        translated_lyric = await cls.translate(lyric)

        # se der erro na tradução, retorna que não foi possível
        if not translated_lyric:
            cls.notify(
                event = "actualization_status_translation_lyric",
                data = "Falha na tradução, tente novamente!"
            )
            return "Falha na tradução, tente novamente!"


        # Atualiza o json com as letras
        cls.update_translations(
            key_song = ReproductionManager.state.current_song.key,
            new_language = language,
            new_lyric = translated_lyric
        )


        # atualiza o cache, notificação e retorno da letra.
        CacheLyrics.load_cache()

        # cls.notify(
        #     event = "actualization_status_translation_lyric",
        #     data = ""
        # )
        
        # retorna a letra traduzida
        return translated_lyric


InformationService.register_callback_event(
    event = "initializate_genius",
    callback = LyricsServices.initializate_genius
)