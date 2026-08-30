"""
=========================================================
KiG POS
=========================================================

Datei:
    widgets/cash/schmales_artikelpanel.py

Beschreibung:
    Artikelauswahl der Kasse auf einem Telefon.

    Nebeneinander ist dort kein Platz: Die Kategorienliste
    neben den Artikeln brauchte 150 dp der 412 dp Breite,
    und im Rest brach "Alkoholfrei" mitten im Wort um.

    Deshalb hier untereinander - und klappbar:

        ▾ Alkoholfrei              4
            [Cola]  [Fanta]
            [Spezi] [Apfelschorle]
        ▸ Alkohol                  3
        ▸ Essen                    2

    Offen ist immer genau eine Kategorie. Zwei geöffnete
    hätten auf einem Telefon dieselbe Endlosliste ergeben,
    die zu vermeiden der ganze Zweck ist.

    Die Suche darüber sticht das Klappen aus: Wer tippt,
    sucht quer durch alle Kategorien und bekommt die Treffer
    als eine Liste - beim Suchen weiß man ja gerade nicht,
    wo der Artikel einsortiert ist.

    Nach außen verhält sich das Panel wie
    widgets/cash/article_panel.py (set_articles,
    search_input, clear_search) - der Kassenbildschirm merkt
    nicht, mit welchem der beiden er spricht.

Version:
    1.0.0
=========================================================
"""

from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView

import theme

from widgets.cash.article_tile import CashArticleTile
from widgets.common.adaptive_grid import KiGAdaptiveGrid
from widgets.common.klappkopf import Klappkopf
from widgets.common.rounded_input import RoundedInput
from widgets.common.rounded_panel import RoundedPanel
from widgets.kig_label import KiGLabel


class SchmalesArtikelpanel(RoundedPanel):

    KOPF_HOEHE = 44

    def __init__(
            self,
            article_callback=None,
            category_callback=None,
            **kwargs
    ):
        super().__init__(**kwargs)

        self.article_callback = article_callback
        self.category_callback = category_callback

        self.orientation = "vertical"
        self.padding = dp(theme.CARD_PADDING)
        self.spacing = dp(theme.CARD_SPACING)

        # Kategorie -> (Klappkopf, Raster)
        self._abschnitte = []

        self._offene_kategorie = None

        # Alle Artikel - Grundlage der Suche über alle Kategorien
        # hinweg.
        self._alle_artikel = []

        # =====================================================
        # Suche
        # =====================================================

        kopf = BoxLayout(
            size_hint_y=None, height=dp(self.KOPF_HOEHE),
            spacing=dp(theme.ROW_SPACING),
        )

        self.search_input = RoundedInput(
            hint_text="Artikel suchen...", multiline=False,
        )
        self.search_input.bind(text=lambda *_args: self._apply_filter())
        kopf.add_widget(self.search_input)

        self.clear_search_button = Button(
            text="X", size_hint=(None, 1), width=dp(44),
            background_normal="", background_down="",
            background_color=theme.SURFACE, color=theme.TEXT_PRIMARY,
            font_size="16sp", bold=True, opacity=0, disabled=True,
        )
        self.clear_search_button.bind(
            on_release=lambda *_args: self.clear_search()
        )
        kopf.add_widget(self.clear_search_button)

        self.add_widget(kopf)

        # =====================================================
        # Kategorien und Artikel
        # =====================================================

        self.liste = BoxLayout(
            orientation="vertical",
            spacing=dp(theme.SPACE_XS),
            size_hint_y=None,
        )
        self.liste.bind(minimum_height=self.liste.setter("height"))

        scroll = ScrollView(do_scroll_x=False, bar_width=dp(10))
        scroll.add_widget(self.liste)

        self.add_widget(scroll)

        # Ergebnisse der Suche - nur sichtbar, solange gesucht wird.
        self.treffer_raster = self._raster()

    # =====================================================
    # Bausteine
    # =====================================================

    @staticmethod
    def _raster():

        breite, hoehe = theme.narrow_article_tile()

        return KiGAdaptiveGrid(
            tile_width=dp(breite),
            tile_height=dp(hoehe),
        )

    # =====================================================
    # Kategorien
    # =====================================================

    def set_categories(self, categories):
        """Baut die Klappköpfe - einen je Kategorie."""

        self.liste.clear_widgets()

        self._abschnitte = []
        self._offene_kategorie = None

        for kategorie in categories:

            artikel = self._artikel_der_kategorie(kategorie)

            kopf = Klappkopf(
                text=kategorie["name"],
                offen=False,
                zusatz=str(len(artikel)),
            )

            raster = self._raster()

            kopf.on_klapp = (
                lambda offen, k=kategorie: self._geklappt(k, offen)
            )

            self.liste.add_widget(kopf)

            self._abschnitte.append((kategorie, kopf, raster))

        self.erste_oeffnen()

    def erste_oeffnen(self):
        """Klappt die erste Kategorie auf.

        Ganz zugeklappt zeigte die Kasse keinen einzigen Artikel - das
        wäre ein Bildschirm, auf dem man erst etwas aufklappen muss,
        bevor man verkaufen kann. Eine ist deshalb immer offen.
        """

        if not self._abschnitte:
            return

        kategorie, kopf, _raster = self._abschnitte[0]

        kopf.set_offen(True)

        self._geklappt(kategorie, True)

    def _geklappt(self, kategorie, offen):

        if not offen:

            self._schliessen(kategorie)

            self._offene_kategorie = None

            return

        # Immer nur eine offen: die andere zuerst zumachen.
        for andere, kopf, _raster in self._abschnitte:

            if andere["id"] != kategorie["id"] and kopf.offen:
                kopf.set_offen(False)
                self._schliessen(andere)

        self._oeffnen(kategorie)

        self._offene_kategorie = kategorie

    def _oeffnen(self, kategorie):

        for eigene, kopf, raster in self._abschnitte:

            if eigene["id"] != kategorie["id"]:
                continue

            raster.set_tiles(
                self._artikel_der_kategorie(kategorie),
                CashArticleTile,
                callback=self.article_callback,
            )

            if raster.parent is None:

                stelle = self.liste.children.index(kopf)

                # children zählt von unten nach oben - das Raster
                # gehört unter seinen Kopf, also an dieselbe Stelle.
                self.liste.add_widget(raster, index=stelle)

            kopf.hervorheben(True)

            return

    def _schliessen(self, kategorie):

        for eigene, kopf, raster in self._abschnitte:

            if eigene["id"] != kategorie["id"]:
                continue

            if raster.parent is not None:
                self.liste.remove_widget(raster)

            kopf.hervorheben(False)

            return

    def _artikel_der_kategorie(self, kategorie):

        if not callable(self.category_callback):
            return []

        return list(self.category_callback(kategorie))

    # =====================================================
    # Von außen: wie article_panel.py
    # =====================================================

    @property
    def selected_category(self):

        return self._offene_kategorie

    def show_category(self, category):

        self.search_input.text = ""

        if category is None:
            self.erste_oeffnen()
            return

        self._geklappt(category, True)

    def set_articles(self, articles):
        """Frischt die Anzeige auf - etwa nach einem Verkauf.

        Die Liste selbst wird nicht übernommen: Welche Artikel wohin
        gehören, weiß die Kategorie besser als der Aufrufer. Gebraucht
        wird sie aber für die Suche, die quer durch alles geht.
        """

        self._alle_artikel = list(articles)

        if self.search_input.text.strip():
            self._apply_filter()
            return

        if self._offene_kategorie is not None:
            self._oeffnen(self._offene_kategorie)

    # =====================================================
    # Suche
    # =====================================================

    def _apply_filter(self, *_args):

        suchtext = self.search_input.text.strip().lower()

        self.clear_search_button.opacity = 1 if suchtext else 0
        self.clear_search_button.disabled = not suchtext

        if not suchtext:

            if self.treffer_raster.parent is not None:
                self.liste.remove_widget(self.treffer_raster)

            self._koepfe_zeigen(True)

            if self._offene_kategorie is not None:
                self._oeffnen(self._offene_kategorie)

            return

        # Während der Suche treten die Kategorien zurück: Gesucht wird
        # über alle hinweg.
        if self._offene_kategorie is not None:
            self._schliessen(self._offene_kategorie)

        self._koepfe_zeigen(False)

        treffer = [
            artikel for artikel in self._alle_artikel
            if suchtext in self._artikelname(artikel).lower()
        ]

        self.treffer_raster.set_tiles(
            treffer, CashArticleTile, callback=self.article_callback
        )

        if self.treffer_raster.parent is None:
            self.liste.add_widget(self.treffer_raster)

    def _koepfe_zeigen(self, sichtbar):

        for _kategorie, kopf, _raster in self._abschnitte:

            if sichtbar and kopf.parent is None:
                # Reihenfolge stimmt wieder, weil beim Suchen nur die
                # Köpfe entfernt und hier in derselben Folge wieder
                # angehängt werden.
                self.liste.add_widget(kopf)

            elif not sichtbar and kopf.parent is not None:
                self.liste.remove_widget(kopf)

    @staticmethod
    def _artikelname(artikel):

        if hasattr(artikel, "name"):
            return artikel.name

        return artikel["name"]

    def clear_search(self):

        if self.search_input.text:
            self.search_input.text = ""
        else:
            self._apply_filter()

    def clear(self):

        self._alle_artikel = []

        for _kategorie, _kopf, raster in self._abschnitte:
            raster.clear_widgets()
