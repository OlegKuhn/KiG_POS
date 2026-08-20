"""
=========================================================
KiG POS
=========================================================

Datei:
    widgets/checklists/checklist_item_row.py

Beschreibung:
    Eine Zeile einer Checkliste.

        [x]  Aufgabe        Frist   Verantwortlich
             Ansprechpartner   Infos             [Entfernen]

    Der Haken links, dann die Aufgabe, dahinter die
    Zusatzangaben. Geändert wird direkt in der Zeile;
    gespeichert wird, sobald ein Feld verlassen wird - so
    schreibt die Anwendung nicht bei jedem Tastendruck in
    die Datenbank.

Version:
    1.0.0
=========================================================
"""

from datetime import datetime

from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button

import theme

from widgets.common.rounded_input import RoundedInput


class ChecklistItemRow(BoxLayout):

    HEIGHT = 56

    # Verteilung der Breite: Die Aufgabe bekommt am meisten, die
    # Zusatzangaben teilen sich den Rest.
    HAKEN_WIDTH = 52
    REMOVE_WIDTH = 110

    # Kivys Roboto kennt weder Haken noch Kreuz - beide kaemen als
    # leeres Kaestchen heraus. Deshalb ein schlichtes X, das jede
    # Schrift hat.
    DONE_MARK = "X"

    def __init__(
            self,
            item,
            on_toggle,
            on_change,
            on_deadline,
            on_remove,
            **kwargs
    ):
        super().__init__(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(self.HEIGHT),
            spacing=dp(theme.ROW_SPACING),
            **kwargs
        )

        self.item = item
        self.on_toggle = on_toggle
        self.on_change = on_change
        self.on_deadline = on_deadline
        self.on_remove = on_remove

        self.done = bool(item["done"])

        # ---- Haken ----
        self.check_button = Button(
            text=self.DONE_MARK if self.done else "",
            size_hint_x=None, width=dp(self.HAKEN_WIDTH),
            background_normal="", background_down="",
            font_size="22sp", bold=True,
        )
        self.check_button.bind(on_release=lambda *_a: self.toggle())
        self._style_check()

        self.add_widget(self.check_button)

        # ---- Aufgabe ----
        self.task_input = self._input(
            item["task"], "Was ist zu tun?", 0.34, "task"
        )

        # Erledigtes tritt auch beim Aufbau zurück, nicht erst nach
        # einem Klick.
        if self.done:
            self.task_input.foreground_color = theme.TEXT_SECONDARY

        self.add_widget(self.task_input)

        # ---- Frist ----
        self.deadline_button = Button(
            text=self.format_deadline(item["deadline"]),
            size_hint_x=0.14,
            background_normal="", background_down="",
            background_color=theme.SURFACE, color=theme.TEXT_PRIMARY,
            font_size="14sp",
        )
        self.deadline_button.bind(
            on_release=lambda *_a: self.on_deadline(self)
        )
        self.add_widget(self.deadline_button)

        # ---- Verantwortlich, Ansprechpartner, Infos ----
        self.responsible_input = self._input(
            item["responsible"], "Verantwortlich", 0.16, "responsible"
        )
        self.add_widget(self.responsible_input)

        self.contact_input = self._input(
            item["contact"], "Ansprechpartner", 0.16, "contact"
        )
        self.add_widget(self.contact_input)

        self.info_input = self._input(
            item["info"], "Infos", 0.20, "info"
        )
        self.add_widget(self.info_input)

        # ---- Entfernen ----
        remove_button = Button(
            text="Entfernen", size_hint_x=None, width=dp(self.REMOVE_WIDTH),
            background_normal="", background_down="",
            background_color=theme.SURFACE, color=theme.ERROR,
            font_size="14sp", bold=True,
        )
        remove_button.bind(on_release=lambda *_a: self.on_remove(self))
        self.add_widget(remove_button)

    # =====================================================

    def _input(self, wert, hinweis, breite, feld):

        feld_widget = RoundedInput(
            text=wert or "", hint_text=hinweis, multiline=False,
            size_hint_x=breite,
        )

        feld_widget.foreground_color = theme.TEXT_PRIMARY
        feld_widget.hint_text_color = theme.TEXT_SECONDARY

        # Beim Verlassen speichern statt bei jedem Tastendruck.
        feld_widget.bind(
            focus=lambda instanz, hat_fokus: (
                None if hat_fokus
                else self.on_change(self, feld, instanz.text)
            )
        )

        return feld_widget

    def _style_check(self):

        self.check_button.background_color = (
            theme.PRIMARY_ORANGE if self.done else theme.SURFACE
        )
        self.check_button.color = (
            theme.TEXT_WHITE if self.done else theme.TEXT_PRIMARY
        )

    def toggle(self):

        self.done = not self.done

        self.check_button.text = self.DONE_MARK if self.done else ""
        self._style_check()

        # Erledigtes tritt zurück, ohne zu verschwinden - so bleibt
        # sichtbar, was schon geschafft ist.
        self.task_input.foreground_color = (
            theme.TEXT_SECONDARY if self.done else theme.TEXT_PRIMARY
        )

        self.on_toggle(self, self.done)

    def set_deadline(self, iso_date):

        self.deadline_button.text = self.format_deadline(iso_date)

        # Den gemerkten Wert NICHT vorher setzen: Der Screen vergleicht
        # beim Speichern mit dem, was er kennt - stünde der neue Wert
        # schon darin, hielte er die Änderung für erledigt und
        # schriebe sie nie in die Datenbank.
        self.on_change(self, "deadline", iso_date or "")

    @staticmethod
    def format_deadline(iso_date):

        if not iso_date:
            return "Frist"

        try:
            return datetime.strptime(iso_date, "%Y-%m-%d").strftime("%d.%m.%Y")
        except (TypeError, ValueError):
            return str(iso_date)
