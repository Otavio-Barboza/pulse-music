# import de interface
from ui.others.colors import color
from ui.playlist.base.music_list import ListViewMusic

# import de back-end
from core.services.controllers.grid_state import GridMode, OpenGrid, GridState
from core.services.controllers.resize_manager import ResizeManager
from core.playlists.controller.playlist_state import PlaylistState
from core.playlists.enum.playlist_enum import PlaylistLoaded

# import geral
import flet as ft


class OverlayImages(ft.Container):
    def __init__(
        self,
        playlist_mode,
        page: ft.Page,
        mode: GridMode, 
        image_big: str, 
        music: list, 
        name: str,
    ):
        super().__init__(
            height = 700,
            width = 1920,
            alignment = ft.alignment.center,
            padding = ft.padding.all(15),
            bgcolor = color.preto2
        )
        
        self.page = page
        self.playlist_mode = playlist_mode
        self.mode = mode
        self.music = music

        self.content = ft.ResponsiveRow(
            vertical_alignment = ft.CrossAxisAlignment.CENTER,
            alignment = ft.MainAxisAlignment.SPACE_EVENLY,
            run_spacing = 10,
            spacing = 10, 
            # expand = True,

            controls = [
                ft.Container(
                    col = {'md' : 5, 'sm' : 12},
                    # expand = True,

                    content = ft.Column(
                        horizontal_alignment = ft.CrossAxisAlignment.CENTER,
                        alignment = ft.MainAxisAlignment.CENTER,
                        spacing = 50,

                        controls = [
                            ft.Container(
                                alignment = ft.alignment.top_left,

                                content = ft.IconButton(
                                    icon = ft.Icons.CLOSE_OUTLINED,
                                    style = ft.ButtonStyle(
                                        color = color.vermelho,
                                        overlay_color = color.preto4
                                    ),

                                    on_click = self.close_overlay
                                )
                            ),
                            ft.Image(
                                src_base64 = image_big,
                                border_radius = ft.border_radius.all(10) if self.mode == GridMode.ARTIST else ft.border_radius.all(10),
                                fit = ft.ImageFit.COVER
                            ),
                            ft.Text(
                                value = name,
                                text_align = ft.TextAlign.CENTER,
                                size = 20,
                                weight = ft.FontWeight.BOLD
                            )
                        ]
                    )
                ),

                ft.Container(
                    col = {'md' : 7, 'sm' : 12},
                    bgcolor = color.preto8,
                    padding = ft.padding.only(
                        top = 15,
                        bottom = 15,
                        left = 10,
                        right = 10
                    ),
                    border_radius = ft.border_radius.all(20) if self.mode == GridMode.ARTIST else ft.border_radius.all(10),
                    alignment = ft.alignment.top_center,

                    content = ft.Column(
                        horizontal_alignment = ft.CrossAxisAlignment.CENTER,
                        alignment = ft.MainAxisAlignment.START,

                        controls = [
                            ft.Text(
                                value = f'Músicas do{"(a)" if self.mode == GridMode.ARTIST else ""} {"artista" if self.mode == GridMode.ARTIST else "álbum"}',
                                size = 18,
                                weight = ft.FontWeight.W_500,
                                text_align = ft.TextAlign.CENTER
                            ),

                            ft.Container(
                                content = ListViewMusic(
                                    page = self.page,
                                    musics = self.music,
                                    favorite_mode = None
                                )
                            )
                        ]
                    )
                )
            ]
        )


    def close_overlay(self, event):
        GridState.set_current_mode(self.mode)
        GridState.set_open_grid(OpenGrid.CLOSE)

        GridState.notify(
            event = "alter_grid_content",
            data = None
        )