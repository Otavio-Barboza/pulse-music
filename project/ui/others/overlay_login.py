# import de back-end
from core.services.auth.google_login_auth import login_google

# import de front-end
from ui.others.colors import color

# import geral
import asyncio
import flet as ft


class OverlayLogin(ft.Container):
    def __init__(self, page: ft.Page):
        super().__init__(
            expand = True,
            bgcolor = color.preto3,
            opacity = 1,
            animate_opacity = ft.Animation(
                duration = 1000,
                curve = ft.AnimationCurve.EASE_OUT
            )
        )

        self.page = page
        self.login_finished = asyncio.Event()

        self.content = ft.Column(
            alignment = ft.MainAxisAlignment.CENTER,
            horizontal_alignment = ft.CrossAxisAlignment.CENTER,

            controls = [
                ft.Row(expand_loose = True, height = 0),
                ft.Text(
                    value = "Fazer login com o google",
                    size = 30,
                    weight = ft.FontWeight.BOLD,
                    font_family = "google_sans_flex"
                ),
                ft.TextButton(
                    width = 200,
                    height = 50,

                    text = "Fazer Login",
                    icon = ft.Icons.LOGIN_ROUNDED,

                    style = ft.ButtonStyle(
                        padding = ft.padding.all(20),
                        icon_size = 18,
                        alignment = ft.alignment.center,
                        animation_duration = 1000,

                        color = {
                            ft.ControlState.DEFAULT : ft.Colors.WHITE,
                            ft.ControlState.HOVERED : ft.Colors.BLACK
                        },
                        overlay_color = {
                            ft.ControlState.HOVERED : ft.Colors.GREY_100
                        },
                        text_style = ft.TextStyle(
                            size = 20,
                            weight = ft.FontWeight.W_500,
                            font_family = "google_sans_flex"
                        )
                    ),

                    on_click = self.login
                )
            ]
        )


    def will_unmount(self):
        from core.services.controllers.state_app import StateApp
        
        StateApp.notify(
            event = "set_min_width",
            data = 500
        )
    
    
    async def login(self, event):
        await login_google(self.page)
        self.login_finished.set()