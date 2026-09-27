"""Manuelle Einnahmen und Ausgaben für die Veranstaltungsstatistik."""

from datetime import date
import sqlite3

from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView

import geldformat
import theme
from widgets.common.kig_popup import KiGPopup
from widgets.common.rounded_input import RoundedInput
from widgets.common.rounded_spinner import RoundedSpinner
from widgets.common.date_picker_popup import DatePickerPopup


def button(text, callback):
    widget = Button(text=text, background_normal='', background_down='',
                    background_color=theme.SURFACE, color=theme.TEXT_PRIMARY,
                    size_hint_y=None, height=dp(48))
    widget.bind(on_release=lambda *_: callback())
    return widget


def label(text, height=48):
    widget = Label(text=text, color=theme.TEXT_PRIMARY, size_hint_y=None,
                   height=dp(height), halign='left', valign='middle')
    widget.bind(size=lambda obj, value: setattr(obj, 'text_size', value))
    return widget


class ManualEntriesPopup(KiGPopup):
    def __init__(self, db, selection, on_changed, **kwargs):
        super().__init__(title='Manuelle Buchungen', size_hint=(0.94, 0.92), **kwargs)
        self.db, self.selection, self.on_changed = db, selection, on_changed
        root = BoxLayout(orientation='vertical', spacing=dp(8), padding=dp(8))
        root.add_widget(label('Einnahmen und Ausgaben nach Datum / Event.\n'
                              'Der gewählte Tag ist der Geschäftstag (06–06 Uhr).', 60))
        root.add_widget(button('Neue Buchung', lambda: self.edit()))
        scroll = ScrollView(do_scroll_x=False)
        self.rows = BoxLayout(orientation='vertical', spacing=dp(8), size_hint_y=None)
        self.rows.bind(minimum_height=self.rows.setter('height'))
        scroll.add_widget(self.rows)
        root.add_widget(scroll)
        root.add_widget(button('Schließen', self.dismiss))
        self.content = root
        self.refresh()

    def refresh(self):
        self.rows.clear_widgets()
        entries = self.db.get_manual_entries(*self.selection)
        if not entries:
            self.rows.add_widget(label('Keine manuellen Buchungen in dieser Auswahl.', 60))
        for entry in entries:
            sign = '+' if entry['kind'] == 'INCOME' else '-'
            text = (f"{entry['entry_date']} | {entry['event_name']}\n"
                    f"{entry['description']} | {sign}{geldformat.geld(entry['amount_cents'] / 100)}\n"
                    f"Beleg: {entry['reference'] or '-'} — zum Bearbeiten antippen")
            row = button(text, lambda item=dict(entry): self.edit(item))
            row.height = dp(96)
            row.bind(size=lambda obj, value: setattr(obj, 'text_size', value))
            self.rows.add_widget(row)

    def changed(self):
        self.refresh()
        self.on_changed()

    def edit(self, entry=None):
        dialog = KiGPopup(title='Buchung bearbeiten' if entry else 'Neue Buchung',
                          size_hint=(0.92, 0.92), auto_dismiss=False)
        root = BoxLayout(orientation='vertical', spacing=dp(8), padding=dp(8))
        scroll = ScrollView(do_scroll_x=False)
        form = BoxLayout(orientation='vertical', spacing=dp(8), size_hint_y=None)
        form.bind(minimum_height=form.setter('height'))
        scroll.add_widget(form)
        root.add_widget(scroll)
        chosen_date = [entry['entry_date'] if entry else (self.selection[0] or date.today().isoformat())]
        def date_changed(value):
            chosen_date[0] = value
            date_button.text = 'Geschäftstag: ' + value
        date_button = button('Geschäftstag: ' + chosen_date[0], lambda: DatePickerPopup(
            title='Buchungsdatum', initial_date=chosen_date[0], on_select=date_changed).open())
        form.add_widget(date_button)
        options = {'Ohne Event': None}
        for event in self.db.get_events():
            if event['entry_type'] == 'EVENT':
                options[f"{event['name']} ({event['start_date']}) #{event['id']}"] = event['id']
        event_id = entry['event_id'] if entry else self.selection[2]
        event_field = RoundedSpinner(text=next((k for k, v in options.items() if v == event_id), 'Ohne Event'),
                                     values=tuple(options), size_hint_y=None, height=dp(52))
        form.add_widget(event_field)
        kind = RoundedSpinner(text='Ausgabe' if entry and entry['kind'] == 'EXPENSE' else 'Einnahme',
                              values=('Einnahme', 'Ausgabe'), size_hint_y=None, height=dp(52))
        form.add_widget(kind)
        description = RoundedInput(text=entry['description'] if entry else '',
                                   hint_text='Bezeichnung / Firma (z. B. Sponsoring)', multiline=False,
                                   size_hint_y=None, height=dp(56))
        amount = RoundedInput(text=f"{entry['amount_cents'] / 100:.2f}" if entry else '',
                              hint_text='Betrag in EUR, z. B. 125,50', multiline=False,
                              size_hint_y=None, height=dp(56))
        reference = RoundedInput(text=entry['reference'] if entry else '', hint_text='Belegnummer (optional)',
                                 multiline=False, size_hint_y=None, height=dp(56))
        for widget in (description, amount, reference):
            form.add_widget(widget)
        form.add_widget(label('Zusätzliche Rechnungen nicht doppelt als Wareneinsatz buchen.\n'
                              'Diese Buchung verändert weder Lagerbestand noch Kassenbuch.', 68))
        status = label('', 70)
        form.add_widget(status)
        def save():
            try:
                self.db.save_manual_entry(chosen_date[0], options[event_field.text],
                    'INCOME' if kind.text == 'Einnahme' else 'EXPENSE', amount.text,
                    description.text, reference.text, entry['id'] if entry else None)
            except (ValueError, sqlite3.Error) as error:
                status.text = str(error)
                return
            dialog.dismiss()
            self.changed()
        if entry:
            def remove():
                confirmation = KiGPopup(title='Buchung entfernen?', size_hint=(0.8, None), height=dp(220))
                box = BoxLayout(orientation='vertical', spacing=dp(8))
                box.add_widget(label('Diese Buchung aus der Auswertung entfernen?'))
                def confirm():
                    try:
                        self.db.void_manual_entry(entry['id'])
                    except sqlite3.Error as error:
                        status.text = str(error)
                        confirmation.dismiss()
                        return
                    confirmation.dismiss()
                    dialog.dismiss()
                    self.changed()
                box.add_widget(button('Entfernen', confirm))
                box.add_widget(button('Abbrechen', confirmation.dismiss))
                confirmation.content = box
                confirmation.open()
            form.add_widget(button('Buchung entfernen', remove))
        actions = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(8))
        actions.add_widget(button('Abbrechen', dialog.dismiss))
        actions.add_widget(button('Speichern', save))
        root.add_widget(actions)
        dialog.content = root
        dialog.open()
