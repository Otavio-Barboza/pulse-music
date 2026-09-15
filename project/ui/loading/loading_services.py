# imports de back-end
from core.song.model.audio import AudioProcess
from core.services.controllers.async_manager import AsyncManager
from core.information.process.information_process import InformationProcess

# import de front-end
from ui.others.colors import color

# import geral
import asyncio
import flet as ft


class LoadingServices(ft.Container):
    def __init__(self, page: ft.Page):
        super().__init__(
            expand = True,
            alignment = ft.alignment.center,
            bgcolor = ft.Colors.with_opacity(
                opacity = 0.95,
                color = color.preto7
            )
        )

        self.page = page
        self.services_finished = asyncio.Event()

        self._text_audio = ft.Text(
            value = "⏳ Áudio",
            size = 14,
            weight = ft.FontWeight.W_500,
            font_family = "google_sans_flex"
        )

        self._text_information = ft.Text(
            value = "⏳ Informações",
            size = 14,
            weight = ft.FontWeight.W_500,
            font_family = "google_sans_flex"
        )

        self._text_other_service = ft.Text(
            value = "⏳ Outros Serviços",
            size = 14,
            weight = ft.FontWeight.W_500,
            font_family = "google_sans_flex"
        )

        self._progress_ring = ft.ProgressRing(color = color.amarelo)

        self._services: list[dict] = [
            {
                "function" : AudioProcess.start,
                "component" : self._text_audio,
                "sucess" : "✔️ Áudio",
                "error" : "❌ Áudio"
            },
            {
                "function" : InformationProcess.start,
                "component" : self._text_information,
                "sucess" : "✔️ Informações",
                "error" : "❌ Informações"
            },
            {
                "function" : AsyncManager.start,
                "component" : self._text_other_service,
                "sucess" : "✔️ Outros Serviços",
                "error" : "❌ Outros Serviços"
            }
        ]

        self.content = content = ft.Container(
            height = 300,
            width = 300,
            padding = ft.padding.all(10),

            bgcolor = color.preto7,

            alignment = ft.alignment.center,
            border_radius = 25,

            shadow = ft.BoxShadow(
                spread_radius = 5,
                blur_radius = 15,
                offset = ft.Offset(0, 0),

                color = ft.Colors.BLUE_GREY_900,
                blur_style = ft.ShadowBlurStyle.OUTER,
            ),

            content = ft.Column(
                horizontal_alignment = ft.CrossAxisAlignment.CENTER,
                alignment = ft.MainAxisAlignment.CENTER,
                spacing = 35,

                controls=[
                    ft.Text(
                        value = "Iniciando Serviços...",
                        weight = ft.FontWeight.BOLD,
                        size = 24,
                        font_family = "google_sans_flex"
                    ),

                    ft.Column(
                        horizontal_alignment = ft.CrossAxisAlignment.START,

                        controls=[
                            self._text_audio,
                            self._text_information,
                            self._text_other_service
                        ]
                    ),

                    self._progress_ring
                ]
            )
        )

    async def _error(
        self,
        component: ft.Text,
        text: str
    ):

        self._progress_ring.visible = False
        self.content.content.controls[1].horizontal_alignment = ft.CrossAxisAlignment.START
        
        component.value = text
        component.update()

    async def start(self):
        try:

            item: dict[str, callable | ft.Text | str]
            for item in self._services:

                try:
                    item["function"]()
                    item["component"].value = item.get("sucess")
                    item["component"].update()

                    await asyncio.sleep(0.375)
                except FileNotFoundError as error:
                    await self._error(
                        component = item["component"],
                        text = item["error"]
                    )
                    print(f"[LOADING SERVICES] Executável não encontrado: {error}")
                except RuntimeError as error:
                    await self._error(
                        component = item["component"],
                        text = item["error"]
                    )
                    print(f"[LOADING SERVICES] Serviço não conseguiu iniciar: {error}")
                except Exception as error:
                    await self._error(
                        component = item["component"],
                        text = item["error"]
                    )
                    print(f"[LOADING SERVICES] Erro inesperado: {error}")

            await asyncio.sleep(0.25)
        finally:
            self.services_finished.set()