# imports de interface
from ui.others.colors import color
from ui.settings.account_settings import AccountSettings
from ui.settings.about_settings import AboutSettings
from ui.settings.settings_support import SettingsSupport
from ui.settings.other_settings import OtherSettings
from ui.utils.utils_ui import UtilsUi

# imports de back-end
from core.services.controllers.state_app import StateApp

# import geral
import flet as ft


class ScreenSettings(ft.Container):
    def __init__(self, page):
        super().__init__(
            expand = True,
            bgcolor = color.preto6,
            padding = 0
        )
        self.page = page
        # dicionário que guarda todos os botões
        self.buttons = {}

        # registrar para escutar mudanças de seção
        StateApp.register_callback("configurations_session", self._when_section_changes)
        
        self.side_menu = self._side_menu()

        self.content_area = ft.Container(
            expand = True,
            padding = 20,
            bgcolor = color.preto2,
            border_radius = ft.border_radius.only(
                top_left = 10,
                bottom_left = 10
            ),

            content = AccountSettings(self.page)
        )

        self.content = ft.Row(
            spacing = 5,
            controls = [
                self.side_menu,
                self.content_area
            ]
        )


    def did_mount(self):
        StateApp.notify(
            event = "set_min_width",
            data = 860
        )
        

    def will_unmount(self):
        StateApp.notify(
            event = "set_min_width",
            data = 500
        )


    def _side_menu(self):
        """
            Cria o menú lateral das configurações

        Returns:
            ft.Container: Menú lateral das configurações
        """

        return ft.Container(
            width = 250,
            bgcolor = color.preto7,
            padding = ft.padding.all(20),
            border_radius = ft.border_radius.only(
                top_right = 10, 
                bottom_right = 10
            ),

            content = ft.Column(
                controls = [
                    ft.Text(
                        value = "Configurações", 
                        size = 26, 
                        weight = ft.FontWeight.BOLD,
                        text_align = ft.TextAlign.CENTER
                    ),
                    ft.Divider(),

                    self._create_button(text = "Conta", section_id = "account"),
                    self._create_button(text = "Sobre o Player", section_id = "about"),
                    self._create_button(text = "Aparência", section_id = "appearance"),
                    self._create_button(text = "Outras Configurações", section_id = "others"),
                    self._create_button(text = "Suporte", section_id = "support"),

                    ft.Divider(),

                    ft.TextButton(
                        text = "Fechar",
                        width = 200,
                        icon = ft.Icons.CLOSE_ROUNDED,

                        style = ft.ButtonStyle(
                            bgcolor = {
                                ft.ControlState.DEFAULT : ft.Colors.TRANSPARENT,
                                ft.ControlState.HOVERED : color.amarelo4
                            },
                            text_style = ft.TextStyle(
                                size = 16,
                                weight = ft.FontWeight.BOLD
                            ),
                            padding = ft.padding.symmetric(
                                vertical = 20,
                                horizontal = 15
                            ),
                            color = {
                                ft.ControlState.DEFAULT : color.branco,
                                ft.ControlState.HOVERED : color.preto_puro
                            },
                            alignment = ft.alignment.center,
                            icon_size = 20
                        ),
                        on_click = lambda e: self.page.overlay.remove(self) or self.page.update()
                    )
                ]
            )
        )


    def _create_button(self, text : str, section_id : str):
        """
            Cria os botões do menú lateral das configurações e depois armazena eles no dict self.buttons

        Args:
            text (str): Texto que irá compor o nome do botão
            section_id (str): Seção a qual será destinada ao botão

        Returns:
            ft.TextButton: Botoão de text
        """

        button = ft.TextButton(
            text = text,
            width = 200,
            on_click = lambda e: self._select(section_id),
        
            style = ft.ButtonStyle(
                bgcolor = {
                    ft.ControlState.DEFAULT: ft.Colors.TRANSPARENT,
                    ft.ControlState.HOVERED : color.preto4
                },
                padding = ft.padding.symmetric(
                    vertical = 20,
                    horizontal = 10
                ),
                text_style = ft.TextStyle(
                    size = 16,
                    weight = ft.FontWeight.W_500
                ),

                color = color.branco,
                shape = ft.RoundedRectangleBorder(radius = 5),
                alignment = ft.alignment.center_left
            )
        )

        self.buttons[section_id] = button
        return button


    def _select(self, section: str):
        """
            Quando é clicado em algum botão a ação é registrada no ouvinte do StateApp com o section 

        Args:
            section (str): Seção responsável de conteúdo
        """
        StateApp.select_config_section(section)


    def _when_section_changes(self, section_id: str):
        """
            1. Altera o Conteúdo da seção principal conforme o botão clicado
            2. Navega nos intens do dict de botões para atualizar a color, isso caso a seção da chave seja a mesma que o section_id informado

        Args:
            section_id (str): Seção responsável
        """

        current_content = self.content_area.content

        if hasattr(current_content, "stop_loop"):
            current_content.stop_loop()

        if section_id == "account":
            self.content_area.content = AccountSettings(page = self.page)
        elif section_id == "about":
            self.content_area.content = AboutSettings(page = self.page)
            self.content_area.content.start_loop()
        elif section_id == "appearance":
            self.content_area.content = ft.Column(
                expand = True,
                controls = [
                    ft.Text(
                        value = "Em Desenvolvimento Configurações de Aparência", 
                        size = 18
                    )
                ]
            )
        elif section_id == "others":
            self.content_area.content = OtherSettings(page = self.page)
        elif section_id == "support":
            self.content_area.content = SettingsSupport(page = self.page)
        else:
            UtilsUi.snack_bar(
                text = "Erro ao trocar a seção de configurações",
                page = self.page
            )
            
        self.content_area.update()
        
        key: str
        button: ft.Icons
        
        for key, button in self.buttons.items():
            if key == section_id:
                # botão selecionado → color diferente
                button.style.bgcolor = {
                    ft.ControlState.DEFAULT: color.amarelo3,
                    ft.ControlState.HOVERED: color.amarelo,
                }
                button.style.color = color.preto1
            else:
                button.style.bgcolor = {
                    ft.ControlState.DEFAULT: ft.Colors.TRANSPARENT,
                    ft.ControlState.HOVERED: color.preto4,
                }
                button.style.color = color.branco

            button.update()