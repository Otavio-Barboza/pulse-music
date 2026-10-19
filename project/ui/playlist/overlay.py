# import de interface
from ui.others.colors import color
from ui.utils.utils_ui import UtilsUi

# imports de back-end
from core.playlists.enum.playlist_enum import PlalistOverlayMode
from core.meta.pipeline.pipeline import Pipeline
from core.services.controllers.state_app import StateApp
        
# imports gerais
from pathlib import Path
import flet as ft
import asyncio


class ContainerOverlay(ft.Container):
    def __init__(self, state, mode: PlalistOverlayMode, page: ft.Page):
        super().__init__(
            alignment = ft.alignment.center,
            expand = True
        )   
        self.page = page
        self.state = state # PlaylistManager
        self.mode = mode

        self.albums, self.covers, self.paths = self.state.return_images()
        self.cards = []
        self.colors = []

        self.picker = ft.FilePicker(
            on_result = self.on_directory_selected
        )

        self.page.overlay.append(self.picker)

        self.container_color_opacity = ft.Container(
            col = 5,
            height = 75,
            width = 100,
            border_radius = ft.border_radius.all(20),
            bgcolor = ft.Colors.BLACK12
        )

        self.opacity_slider = ft.Slider(
            col = 6,
            on_change = self._change_slider,
            value = 1.0,
            max = 1.0,
            min = 0,
            thumb_color = color.amarelo,
            active_color = color.amarelo,
            inactive_color = color.preto2,
            overlay_color = color.amarelo_opaco2
        )

        self.path_text = ft.Text(
            col = 6,
            value = "Nenhuma pasta de musicas selecionada",
            size = 16,
            max_lines = 1,
            text_align = ft.TextAlign.CENTER
        )

        self.text_name = ft.Text(
            col = 6,
            value = "Adicione o name da sua playlist",
            size = 18,
            max_lines = 2,
            text_align = ft.TextAlign.CENTER
        )

        self.text_field = ft.TextField(
            hint_text = "Digite o nome da sua playlist...",
            hint_style = ft.TextStyle(
                color = color.cinza3,
                size = 16
            ),

            border_radius = ft.border_radius.all(12),
            max_length = 500,
            min_lines = 1,
            max_lines = 1,
            multiline = False,
            filled = True,
            fill_color = color.preto9,
            border_color = ft.Colors.TRANSPARENT,
            col = 8,
            
            label_style = ft.TextStyle(
                color = color.branco
            ),
            
            text_style = ft.TextStyle(
                color = color.branco,
                size = 16
            ),

            cursor_color = color.amarelo,
            content_padding = ft.Padding(16, 10, 16, 10),

            on_submit = self._submit_name,
            on_change = self._change
        )

        self.content = ft.Container(
            alignment = ft.alignment.center,
            bgcolor = color.preto8,
            expand = True,
            border_radius = ft.border_radius.all(15),
            margin = ft.margin.all(10),

            content = ft.ResponsiveRow(
                vertical_alignment = ft.CrossAxisAlignment.CENTER,
                alignment = ft.MainAxisAlignment.CENTER,
                spacing = 0,

                controls = [
                    # cores, nomes etc
                    ft.Container(
                        col = 6,
                        padding = ft.padding.all(35),

                        content = ft.Column(
                            horizontal_alignment = ft.CrossAxisAlignment.START,
                            alignment = ft.MainAxisAlignment.CENTER,
                            spacing = 5,

                            controls = [
                                # Campo de texto do nome da playlist
                                self.text_field,
                                
                                # nome da playlist em texto
                                ft.Container(
                                    height = 25,
                                    padding = ft.padding.only(
                                        left = 15
                                    ),

                                    content = self.text_name
                                ),
                                
                                # button de selecionar a pasta | # caminho selecionado
                                ft.Container(
                                    height = 75,
                                    alignment = ft.alignment.center,
                                    margin = ft.margin.only(
                                        top = 20
                                    ),

                                    content = ft.ResponsiveRow(
                                        alignment = ft.MainAxisAlignment.CENTER,
                                        vertical_alignment = ft.CrossAxisAlignment.CENTER,

                                        controls = [
                                            self._create_button(
                                                click = "path",
                                                col = 5,
                                                text = "Selecionar Pasta",
                                                text_color = color.branco_puro,
                                                background_color = color.preto9
                                            ),
                                            self.path_text
                                        ]
                                    )
                                ),

                                # Controle da opacidade.
                                ft.Container(
                                    expand = True,
                                    height = 50,
                                    alignment = ft.alignment.bottom_center,

                                    content = ft.Text(
                                        value = "Controle da opacidade de cor de fundo da playlist",
                                        text_align = ft.TextAlign.CENTER,
                                        size = 24
                                    )
                                ),

                                # container com a cor referencia | # slider
                                ft.Container(
                                    height = 100,
                                    margin = ft.margin.only(
                                        bottom = 20
                                    ),

                                    content = ft.ResponsiveRow(
                                        alignment = ft.MainAxisAlignment.SPACE_AROUND,
                                        vertical_alignment = ft.CrossAxisAlignment.CENTER,

                                        controls = [
                                            self.container_color_opacity,

                                            ft.Container(
                                                height = 75,
                                                width = 100,
                                                bgcolor = color.preto9,
                                                padding = ft.padding.all(10),
                                                col = 5,
                                                border_radius = ft.border_radius.all(20),
                                                content = self.opacity_slider
                                            )
                                        ]
                                    )
                                ),

                                # Grid de cores.

                                ft.Container(
                                    height = 400,
                                    bgcolor = color.cinza3,
                                    margin = ft.margin.only(
                                        bottom = 20
                                    ),
                                    border_radius = ft.border_radius.all(15),

                                    content = ft.GridView(
                                        max_extent = 50,
                                        padding = ft.padding.all(20),
                                        spacing = 30,
                                        run_spacing = 30,

                                        controls = [
                                            self._create_color_card(color) for color in color._paleta_de_cores()
                                        ]
                                    )
                                ),

                                # botões de salvar e cancelar
                                ft.ResponsiveRow(
                                    height = 75,
                                    alignment = ft.MainAxisAlignment.SPACE_AROUND,
                                    vertical_alignment = ft.CrossAxisAlignment.CENTER,
                                    
                                    controls = [
                                        self._create_button(
                                            click = "cancel", 
                                            text = "Cancelar", 
                                            col = 5,
                                            background_color = color.vermelho,
                                            text_color = color.branco
                                        ),

                                        self._create_button(
                                            click = "concluir", 
                                            text = "Concluir", 
                                            col = 5,
                                            background_color = color.amarelo,
                                            text_color = color.preto_puro,
                                            text_color_hover = color.preto_puro
                                        )
                                    ]
                                )
                            ]
                        )
                    ),

                    # imagens...
                    ft.Container(
                        bgcolor = color.cinza3,
                        padding = ft.padding.all(10),
                        border_radius = ft.border_radius.only(
                            top_left = 10,
                            bottom_left = 10
                        ),
                        col = 6,

                        content = ft.Tabs(                            
                            label_text_style = ft.TextStyle(
                                font_family = "sansita"
                            ),
                            label_color = color.branco_puro,
                            
                            unselected_label_text_style = ft.TextStyle(
                                font_family = "google_sans_flex"
                            ),
                            unselected_label_color = color.branco_suave,

                            divider_color = color.branco_suave,
                            indicator_color = color.branco_suave,

                            animation_duration = 300,
                            tab_alignment = ft.TabAlignment.CENTER,

                            tabs = [
                                ft.Tab(
                                    text = "Albuns",
                                    content = ft.GridView(
                                        max_extent = 220,
                                        spacing = 40,
                                        run_spacing = 40,
                                        padding = ft.padding.all(20),

                                        controls = [
                                            self._create_image_card(f"{self.paths[0]}/{img}") for img in self.albums
                                        ]
                                    )
                                ),

                                ft.Tab(
                                    text = "Capas de Músicas",

                                    content = ft.GridView(
                                        max_extent = 220,
                                        spacing = 40,
                                        run_spacing = 40,
                                        padding = ft.padding.all(20),

                                        controls = [
                                            self._create_image_card(f"{self.paths[1]}/{img}") for img in self.covers
                                        ]
                                    )
                                ),
                            ]
                        )
                    )  
                ]
            )
        )

        if self.mode == PlalistOverlayMode.UPDATE:
            self._fill_in_fields()


    def did_mount(self):
        StateApp.notify(
            event = "set_maximized_window",
            data = True
        )
        StateApp.notify(
            event = "set_min_width",
            data = 860
        )
        

    def will_unmount(self):
        StateApp.notify(
            event = "set_min_width",
            data = 500
        )


    def _fill_in_fields(self):
        playlist = self.state.playlist_config  # PlaylistDetalhada

        self.state.name = playlist.name
        self.state.color = playlist.style["color"]
        self.state.opacity = playlist.style["opacity"]
        self.state.image = playlist.style["image_path"]
        self.state.path = playlist.music["music_path"]

        self.container_color_opacity.bgcolor = playlist.style["color"]
        self.container_color_opacity.opacity = playlist.style["opacity"]
        self.text_name.value = f"Nome da playlist: {playlist.name}"
        self.path_text.value = f"Pasta: {playlist.music['music_path']}"


    def _create_image_card(self, image):
        card = ft.Container(
            height = 220,
            width = 220,
            data = image,
            alignment = ft.alignment.top_right,
            on_click = self._select_image,
            image = ft.DecorationImage(
                src = image,
                fit = ft.ImageFit.COVER
            ),
            padding = ft.padding.all(5),
            border_radius = ft.border_radius.all(5),
            
            content = ft.Icon(
                name = ft.Icons.CHECK,
                color = color.amarelo,
                size = 30,
                visible = False
            )
        )

        self.cards.append(card)
        return card

    
    def _create_color_card(self, color : ft.Colors):
        cont = ft.Container(
            width = 50,
            height = 50,
            border_radius = ft.border_radius.all(10),
            bgcolor = color,
            alignment = ft.alignment.center,
            data = color,
            on_click = self._select_color
        )

        self.colors.append(cont)
        return cont
    
    
    def confirm(self, e):
        if self.mode == PlalistOverlayMode.CREATE:
            self.create_playlist()
        elif self.mode == PlalistOverlayMode.UPDATE:
            self.state.update_playlist()
            self.close_overlay(e=None)


    def _create_button(
        self, 
        click, 
        col: int, 
        text: str, 
        background_color: str,
        text_color: str, 
        text_color_hover: str = color.branco_suave,
        width: int = 250,
        border_color: str | ft.Colors = ft.Colors.TRANSPARENT
    ) -> ft.TextButton:
        if click == "cancel":
            click = self.close_overlay
        elif click == "concluir":
            click = self.confirm
        elif click == "path":
            click = self.open_selector_path
        else:
            click =  None
        
        return ft.TextButton(
            col = col,
            text = text,
            on_click = click,
            height = 40,
            width = width,

            style = ft.ButtonStyle(
                bgcolor = {
                    ft.ControlState.DEFAULT : background_color,
                    ft.ControlState.HOVERED : ft.Colors.with_opacity(color = background_color, opacity = 0.75)
                },
                side = {
                    ft.ControlState.HOVERED : ft.BorderSide(2, border_color)
                },
                color = {
                    ft.ControlState.DEFAULT : text_color,
                    ft.ControlState.HOVERED : text_color_hover
                },
                shape = ft.RoundedRectangleBorder(15),
                padding = ft.padding.all(10)
            )
        )

    
    def _select_image(self, e):
        self.state.image = e.control.data

        for card in self.cards:
            if card.data == e.control.data:
                card.opacity = 0.9
                card.scale = 1.1
                card.content.visible = True
            else:
                card.opacity = 1.0
                card.scale = 1.0
                card.content.visible = False
            
            card.update()

    
    def _change_slider(self, e):
        self.container_color_opacity.opacity = self.opacity_slider.value
        self.container_color_opacity.update()

        cor_opc = ft.Colors.with_opacity(
            color = self.state.color, 
            opacity = self.container_color_opacity.opacity
        )

        self.state.color = cor_opc
        self.state.opacity = self.container_color_opacity.opacity


    def _select_color(self, e):
        self.state.color = e.control.data
        self.container_color_opacity.bgcolor = e.control.data
        self.container_color_opacity.update()
        
        for container in self.colors:
            if container.data == e.control.data:
                container.scale = 1.25
                container.opacity = 0.75
            else:
                container.scale = 1.0
                container.opacity = 1.0
            
            container.update()


    def _submit_name(self, e):
        self.state.name = self.text_field.value
        self.text_name.value = f"Nome da playlist: {self.text_field.value}"
        self.text_field.value = ""
        self.update()

    
    def _change(self, e):
        self.state.name = self.text_field.value
        self.text_name.value = f"Nome da playlist: {self.text_field.value}"
        self.update()


    def on_directory_selected(self, e: ft.FilePickerResultEvent):
        if e.path in self.check_existing_paths():
            UtilsUi.snack_bar(
                page = self.page,
                text = "Já existe uma playlist com essa path de músicas, escolha outra!"
            )
        else:
            self.state.path = e.path
            self.path_text.value = f"Pasta selecionada: {e.path}"
            self.path_text.update()


    def open_selector_path(self, e):
        self.picker.get_directory_path()

    
    def close_overlay(self, e):
        self.state.image = r"assets\images\placeholders\capa_playlist_padrao.png"
        self.state.name = None
        self.state.color = "#3d3d3d"
        self.state.opacity = 1.0
        self.state.path = None
        
        self.page.overlay.clear()
        self.page.update()


    async def start_pipeline(self, path: Path, id: str):
        await asyncio.to_thread(
            Pipeline.start_wrapper_sync,
            path,
            [],
            id
        )


    def check_existing_playlists(self) -> list[str]:
        return self.state.return_existngs_playlists()


    def check_existing_paths(self) -> list[str]:
        return self.state.return_existngs_folders()


    def create_playlist(self):
        if self.state.name is None:
            UtilsUi.snack_bar(
                page = self.page,
                text = "Atribua um nome a sua playlist primeiro"
            )
        elif self.state.name in self.check_existing_playlists():
            UtilsUi.snack_bar(
                page = self.page,
                text = "Já existe uma playlist com esse nome, escolha outro!"
            )
        elif self.state.path is None:
            UtilsUi.snack_bar(
                page = self.page,
                text = "Selecione uma pasta para criar"
            )
        elif self.state.path in self.check_existing_paths():
            UtilsUi.snack_bar(
                page = self.page,
                text = "Já existe uma playlist com essa pasta de músicas, escolha outra!"
            )
        else:
            id = self.state.create_playlist()
            self.page.run_task(
                self.start_pipeline,
                self.state.path,
                id
            )
            self.close_overlay(e = None)