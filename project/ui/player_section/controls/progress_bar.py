# import de interface
from ui.others.colors import color

# import de back-end
from core.song.controller.reproduction_manager import ReproductionManager
from core.services.controllers.resize_manager import ResizeManager

# import geral
import flet as ft


class CompactProgressBar(ft.Container):
    def __init__(self, page: ft.Page):
        super().__init__(
            alignment = ft.alignment.center
        )

        self.slider = ft.Slider(
            col = {'md' : 9, 'sm' : 8.5, 'xs' : 12},
            thumb_color = color.amarelo,
            inactive_color = color.preto8,
            active_color = color.amarelo,
            overlay_color = color.amarelo_opaco2,
            on_change_end = self.alter_position_slider,
            on_change_start = self.detect_drag_slider
        )
        self.current_time = self._create_text('00:00')
        self.total_time = self._create_text('00:00')

        self.content = ft.ResponsiveRow(
            alignment = ft.MainAxisAlignment.CENTER,
            vertical_alignment = ft.CrossAxisAlignment.CENTER,
            spacing = 0,

            controls = [
                self.current_time,
                self.slider,
                self.total_time
            ]
        )

        ResizeManager.register(self._on_resize)

        ReproductionManager.register_callback(
            event = 'slider_position', 
            callback = self.actualization_current_duration
        )
        ReproductionManager.register_callback(
            event = 'slider', 
            callback = self.actualization_slider
        )
        ReproductionManager.register_callback(
            event = 'total_time',
            callback = self.actualization_total_duration
        )

    def did_mount(self):
        self._on_resize()

    def _on_resize(self, e = None):
        self.current_time.visible = not self.page.width < 576
        self.total_time.visible = not self.page.width < 576
        self.update()

    def _create_text(self, text: str) -> ft.Text:
        return ft.Text(
            value = text,
            visible = True,
            col = {'md' : 1, 'sm' : 1.5},
            text_align = ft.TextAlign.CENTER
        )

    def actualization_slider(self, *_):
        self.slider.max = ReproductionManager.state.total_time
        self.slider.min = 0
        self.slider.value = ReproductionManager.state.current_time
        self.slider.update()
    
    def actualization_total_duration(self, *_):
        self.total_time.value = ReproductionManager.formatted_total_duration()
        self.update()

    def actualization_current_duration(self, *_):
        self.current_time.value = ReproductionManager.formatted_current_duration() if ReproductionManager.state.current_time != 0.0 else '00:00'
        
        if (
            ReproductionManager.state.current_time > 0 
            and ReproductionManager.state.total_time != 0.0
            and self.slider.max is not None
        ):
            self.slider.value = min(
                ReproductionManager.state.current_time,
                ReproductionManager.state.total_time,
                self.slider.max
            )

        self.update()

    def detect_drag_slider(self, e):
        ReproductionManager.set_drag_slider(True)
    
    def alter_position_slider(self, e):        
        ReproductionManager.set_drag_slider(False)
        ReproductionManager.go_to(e.control.value)