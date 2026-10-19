# import geral
import flet as ft


class Colors:

    def __init__(self):
        self.branco = '#ececec'
        self.branco2 = '#f9f9f9'
        self.branco3 = "#dfdfdf"
        self.branco_puro = '#ffffff'
        self.branco_suave = '#dadada'

        self.cinza1 = '#aaaaaa'
        self.cinza2 = '#CCCCCC'
        self.cinza3 = "#8c8c8c"

        self.preto1 = '#1f1f1f'
        self.preto2 = '#2a2a2a'
        self.preto3 = '#0e0d0d'
        self.preto4 = '#1e1e1e'
        self.preto5 = ft.Colors.with_opacity(0.5, self.preto3)
        self.preto6 = ft.Colors.with_opacity(0.95, self.preto1)
        self.preto7 = "#181818"
        self.preto8 = "#3b3b3b"
        self.preto9 = "#505050"

        self.preto_puro = '#000000'
        self.preto_puro_2 = '#070707'
        self.preto_puro_3 = '#121212'
        self.preto_puro_4 = '#2a2a2a'
        self.preto_puro_5 = "#1a1a1a"
        self.preto_cinza = "#34313F"

        self.amarelo = '#f7ff3c'
        self.amarelo2 = "#b1a500"
        self.amarelo3 = "#ceaf5b"
        self.amarelo4 = '#f5c100'
        self.amarelo_opaco1 = ft.Colors.with_opacity(0.9, self.amarelo)
        self.amarelo_opaco2 = ft.Colors.with_opacity(0.3, self.amarelo)
        self.amarelo_suave = '#d6c27a'

        self.laranja = '#ff6f3d'
        self.laranja2 = "#9B4B31"
        
        self.rosa = '#f10258'
        self.rosa_avermelhado = "#b60037"

        self.vermelho = "#b32c2c"
        self.vermelho_suave = '#c98a8a'

        self.azul_escuro = '#021b33'
        self.azul_medio = '#12577b'
        self.azul_medio2 = '#3c4e69'
        self.azul_suave = '#7fa6c9'
        self.azul = "#0088ff"
        self.azul_opaco = ft.Colors.with_opacity(0.9, self.azul_medio2)

        self.roxo = "#4400bf"
        self.roxo_suave = '#a58bcf'

    def _paleta_de_cores(self) -> list:
        return [
            ft.Colors.RED_ACCENT_700,
            ft.Colors.RED_500,
            ft.Colors.DEEP_ORANGE_500,
            ft.Colors.ORANGE_ACCENT_700,
            ft.Colors.ORANGE_500,
            ft.Colors.AMBER_ACCENT_700,
            ft.Colors.AMBER_500,
            ft.Colors.YELLOW_ACCENT_700,
            ft.Colors.YELLOW_500,
            ft.Colors.LIME_500,
            ft.Colors.LIME_ACCENT_700,
            ft.Colors.GREEN_ACCENT_700,
            ft.Colors.LIGHT_GREEN_ACCENT_700,
            ft.Colors.LIGHT_GREEN_500,
            ft.Colors.GREEN_500,
            ft.Colors.TEAL_ACCENT_700,
            ft.Colors.TEAL_500,
            ft.Colors.CYAN_500,
            ft.Colors.LIGHT_BLUE_500,
            ft.Colors.LIGHT_BLUE_ACCENT_700,
            ft.Colors.BLUE_500,
            ft.Colors.BLUE_ACCENT_700,
            ft.Colors.INDIGO_500,
            ft.Colors.INDIGO_ACCENT_700,
            ft.Colors.PINK_500,
            ft.Colors.PURPLE_500,
            ft.Colors.DEEP_PURPLE_500,
            ft.Colors.DEEP_PURPLE_ACCENT_700,
            ft.Colors.BROWN_500,
            ft.Colors.GREY_500,
            ft.Colors.BLUE_GREY_500,
            ft.Colors.BLACK12,
            ft.Colors.BLACK87,
            ft.Colors.WHITE,
            ft.Colors.WHITE70
        ]
    
color = Colors()