# import de interface
from ui.others.overlay_images import OverlayImages

# imports de back-end
from core.services.controllers.grid_state import GridMode, GridState, OpenGrid
from core.song.enum.song_enum import ReproductionMode
from core.meta.cache.global_cache import cache_metadata
from core.meta.repository.extract_metadata import ExtractMetadata
from core.services.account_manager import AccountManager
from core.utils.path import AppPaths
from core.song.model.song import Song


# imports gerais
from pathlib import Path
import flet as ft
import os


class GridImages(ft.GridView):
    def __init__(self, mode: GridMode, page: ft.Page):
        super().__init__(
            max_extent = 200 if mode == GridMode.ARTIST else 250,
            expand = True,
            spacing = 65,
            run_spacing = 15,
            padding = ft.padding.all(15)
        )
        self.page = page
        self.mode = mode

        self.controls = []


    # CRIAÇÃO DE COMPONENTES
    def _build_class(self, mode: GridMode):    
        if mode != self.mode:
            return

        # Definindo a pasta de listagem das imagens conforme o modo definido na grid.
        if mode == GridMode.ARTIST:
            path: Path = AppPaths.ACCOUNT / str(AccountManager.accounts_cache.get("current_account")) / "images" / "artists"
        elif mode == GridMode.ALBUM:
            path: Path = AppPaths.ACCOUNT / str(AccountManager.accounts_cache.get("current_account")) / "images" / "albums"
        else:
            print(f"ERRO: {self.mode} ; {mode}")
            
        self.controls.clear()
        
        for img in os.listdir(path):

            # validação do arquivo de imagem, se realmente é uma imagem, se não for, automaticamente é descartado.
            if img.endswith((".jpg", ".jpeg", ".png")):

                # remoção do sufixo de imagem
                image_key = img.removesuffix(".jpg")

                # organização do nome de acordo com o modo da grid.
                if self.mode == GridMode.ARTIST:
                    name = cache_metadata.artists.to_dict()[image_key]["defined_artist"]
                    # name = image_key
                elif self.mode == GridMode.ALBUM:
                    name = image_key
                else:
                    name = None

                # Caso ocorra algum erro inesperado em alguma imagem, o name recebe None se caído no else da organização. Se for None é automaticamente descatado também.
                if name is not None:  
                    self.controls.extend([
                        ft.Container(
                            data = image_key,
                            on_click = self.click,

                            content = ft.Column(
                                horizontal_alignment = ft.CrossAxisAlignment.CENTER,
                                alignment = ft.MainAxisAlignment.START,

                                controls = [
                                    Imagem(
                                        src = f'{path}/{img}', 
                                        mode = self.mode
                                    ),
                                    ft.Text(
                                        value = name,
                                        text_align = ft.TextAlign.CENTER,
                                        size = 16,
                                        weight = ft.FontWeight.W_300,
                                        max_lines = 2,
                                        overflow = ft.TextOverflow.FADE
                                    )
                                ]
                            )
                        )
                    ])
            else:
                print(f"CARREGAMENTO DA GRID {self.mode.value}; imagem inválida: {img}")


    # INICIALIZAÇÃO DA CLASSE
    def load(self):
        self._build_class(self.mode)

    def reload(self, mode: GridMode):
        self._build_class(mode)
        self.update()

    def connect(self):
        GridState.register_callback(
            event = 'actualization_grid',
            func = self.reload
        )

    def _return_song_list(
        self, 
        event, 
        playlist_mode: ReproductionMode,
        data: dict
    ) -> list[Song]:
        
        song_list: list[Song] = []

        if self.mode == GridMode.ARTIST:
            for key, song in data.get(event.control.data).items():
                if key == 'songs':
                    for music in song:

                        song_list.append(
                            Song(
                                mode = playlist_mode,
                                name = os.path.basename(str(
                                    music.get("artist_path")
                                )),
                                path = str(music.get('artist_path')),
                                key = music.get('key')
                            )
                        )
        elif self.mode == GridMode.ALBUM:   
            for song in data.get(event.control.data).values():
                for song_path in song:
                    song_list.append(
                        Song(
                            mode = ReproductionMode.ALBUM,
                            name = os.path.basename(
                                str(
                                    song_path.get('destination_song')
                                ).replace('.mp3', '')
                            ),
                            path = str(song_path.get('destination_song')),
                            key = song_path.get('key_song')
                        ) 
                    )

        return song_list

    def click(self, e):
        from core.song.model.reproduction import Reproduction
        
        song_list: list[Song]
        
        if self.mode == GridMode.ARTIST:
            playlist_mode = ReproductionMode.ARTIST
            data = cache_metadata.artists.to_dict()

            song_list = self._return_song_list(
                event = e,
                playlist_mode = playlist_mode,
                data = data
            )

            path = data.get(e.control.data).get('songs')[0].get('artist_path')
            img = ExtractMetadata.load_image_big_base64(
                file_path = path, 
                type = 'artist'
            )

            name = data.get(e.control.data).get('defined_artist')
        else:
            playlist_mode = ReproductionMode.ALBUM
            data = cache_metadata.albums.to_dict()

            song_list = self._return_song_list(
                event = e,
                playlist_mode = playlist_mode,
                data = data
            )

            for song in song_list:
                if song.path is not None:
                    path = song.path
                    break
                
            img = ExtractMetadata.load_image_big_base64(
                file_path = path, 
                type = 'album'
            )

            name = e.control.data

        GridState.set_current_mode(self.mode)
        GridState.set_open_grid(OpenGrid.OPEN)

        GridState.notify(
            event = "alter_grid_content",
            data = OverlayImages(
                image_big = img,
                music = sorted(
                    song_list, 
                    key = lambda song: song.name.casefold()
                ),
                mode = self.mode,
                name = name,
                playlist_mode = playlist_mode,
                page = self.page
            ) 
        )

        from core.services.controllers.state_app import StateApp

        StateApp.notify(
            event = "set_min_width",
            data = 860
        )
        
        Reproduction.load_songs_from_mode(
            mode = playlist_mode,
            list = song_list
        )


class Imagem(ft.Image):
    def __init__(self, src : str, mode : GridMode):
        super().__init__(
            src = src if src else r'',
            border_radius = ft.border_radius.all(100) if mode == GridMode.ARTIST else ft.border_radius.all(7.5),
            filter_quality = ft.FilterQuality.HIGH,
            fit = ft.ImageFit.COVER
        )