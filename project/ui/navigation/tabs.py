# imports de back-end
from core.services.account_manager import AccountManager
from core.services.controllers.grid_state import GridState, GridMode, OpenGrid
from core.services.controllers.resize_manager import ResizeManager

# imports da ui (interface)
from ui.others.colors import color
from ui.others.music_search import MusicSearch
from ui.playlist.base.base_playlists import ColumnCards
from ui.grid_view.grid import GridImages
from ui.favorite.favorite import Favorite
from ui.grid_view.grid import OverlayImages

# import geral
import flet as ft


class TabsNavigation(ft.Tabs):
    def __init__(self, page):
        super().__init__(
            selected_index = 0,
            animation_duration = 300,
            label_color = color.amarelo,
            divider_color = ft.Colors.TRANSPARENT,
            indicator_color = color.amarelo,
            indicator_border_radius = ft.border_radius.all(50),
            overlay_color = color.preto8,
            unselected_label_color = color.branco_puro,
            scrollable = False,
            expand = True,
            tab_alignment = ft.TabAlignment.FILL,
            
            label_text_style = ft.TextStyle(
                size = 16,
                weight = ft.FontWeight.BOLD,
                letter_spacing = 1,
            ),

            unselected_label_text_style = ft.TextStyle(
                weight = ft.FontWeight.W_300
            )
        )
        self.page = page
        self._icones_tabs = []
        self._labels_tabs = []
        self.lista_labels = [
            {'label' : 'Playlists', 'icon' : ft.Icons.MUSIC_NOTE_SHARP},
            {'label' : 'Artistas', 'icon' : ft.Icons.PERSON_SEARCH_ROUNDED}, 
            {'label' : 'Álbuns', 'icon' : ft.Icons.QUEUE_MUSIC_ROUNDED}, 
            {'label' : 'Favoritas', 'icon' : ft.Icons.FAVORITE_SHARP}, 
            {'label' : 'Pesquisar', 'icon' : ft.Icons.YOUTUBE_SEARCHED_FOR_ROUNDED}
        ]

        self.playlist = ColumnCards(self.page)
        self.search_music = MusicSearch(self.page)
        self.artists = GridImages(mode = GridMode.ARTIST, page = self.page)
        self.albums = GridImages(mode = GridMode.ALBUM, page = self.page)
        
        self._create_tabs()

        self.tabs = []


    # CRIAÇÃO DOS COMPONENTES DE TABS
    def _build_class(self):
        self._create_tabs()

        self.tabs = [
            ft.Tab(
                tab_content = self._labels_tabs[0],
                content = self.playlist                
            ),

            ft.Tab(
                tab_content = self._labels_tabs[1],
                content = self.artists
            ),

            ft.Tab(
                tab_content = self._labels_tabs[2],
                content = self.albums
            ),

            ft.Tab(
                tab_content = self._labels_tabs[3],
                content = None
            ),

            ft.Tab(
                tab_content = self._labels_tabs[4],
                content = self.search_music
            )
        ]


    # FUNÇÕES PARA INICIALIZAR O CARREGAMENTO/CRIAÇÃO NO main()
    def load(self):
        # criando e carregando componentes
        self._build_class()
        self.playlist.load()
        self.search_music.load()
        
        if (
            isinstance(self.artists, GridImages)
            and isinstance(self.albums, GridImages)
        ):
            self.artists.load()
            self.albums.load()


    def reload(self):
        self.playlist.reload_playlists()
        self.artists.load()
        self.albums.load()

        if (
            isinstance(self.artists, GridImages)
            and isinstance(self.albums, GridImages)
        ):
            self.artists.update()
            self.albums.update()


    def connect(self):
        from core.favorite.controller.favoritas_controller import FavoriteState

        # registrando callbacks
        ResizeManager.register(self._adjust_tabs)
        self.playlist.connect()

        if (
            isinstance(self.artists, GridImages)
            and isinstance(self.albums, GridImages)
        ):
            self.artists.connect()
            self.albums.connect()

        FavoriteState.register_callback(
            event = "actualization_favorites",
            callback = self.load_favorites
        )

        GridState.register_callback(
            event = "alter_grid_content",
            func = self.alter_grid_content
        )
        

    # CRIAÇÃO DOS ITENS
    def _create_tabs(self):
        for l in self.lista_labels:
            label, icone = self._tab_label(
                icon = l["icon"],
                texto = l["label"]
            )

            self._labels_tabs.append(label)
            self._icones_tabs.append(icone)


    def _tab_label(self, icon, texto):
        icone = ft.Icon(icon, size = 18)

        row = ft.Row(
            alignment = ft.MainAxisAlignment.CENTER,
            vertical_alignment = ft.CrossAxisAlignment.CENTER,
            spacing = 8,
            
            controls = [
                icone,
                ft.Text(
                    texto,
                    size = 14,
                    weight = ft.FontWeight.W_700
                )
            ]
        )

        return row, icone

    
    def _adjust_tabs(self, *_):
        compact: float | int = self.page.width < 576
        
        for icon in self._icones_tabs:
            icon.visible = not compact

        self.update()

    
    def load_favorites(self, *_):
        from core.song.model.song import Song
        from core.favorite.controller.favoritas_controller import FavoriteState
        from core.song.model.reproduction import Reproduction
        from core.song.enum.song_enum import ReproductionMode
        
        list_musics: list[Song] = FavoriteState.list_favorited_objects()
            
        self.tabs[3].content = Favorite(
            page = self.page,
            list_music_object = list_musics,
            favorite_mode = ReproductionMode.FAVORITE
        )
        self.tabs[3].update()

        Reproduction.load_songs_from_mode(
            mode = ReproductionMode.FAVORITE,
            list = list_musics
        )


    def alter_grid_content(self, content_expand_grid: OverlayImages | None = None):
        index = 1 if GridState.current_mode == GridMode.ARTIST else 2

        print(
            f"[GRID STATE]: index indentificado: {index}"
        )

        if GridState.open_grid == OpenGrid.CLOSE:
            self.tabs[index].content = self.artists if GridState.current_mode == GridMode.ARTIST else self.albums
            self.tabs[index].update()
            
            print(
                f"[TABS]: alterando conteúdo das tabs: voltando para grid"
            )
        else:
            self.tabs[index].content = content_expand_grid
            self.tabs[index].update()
            
            print(
                f"[TABS]: alterando conteúdo das tabs: abrindo overlay"
            )