"""
=========================================================
KiG POS
=========================================================

Datei:
    main.py

Beschreibung:
    Einstiegspunkt für Android.

    Buildozer startet auf dem Gerät immer die Datei "main.py" -
    ein anderer Name ist nicht vorgesehen. Die eigentliche
    Anwendung steht unverändert in KiG_POS.py; hier wird sie nur
    gestartet.

    Dazu kommt ein Fangnetz: Stürzt die Anwendung beim Start ab,
    schließt sich auf dem Telefon sonst wortlos das Fenster - der
    Grund steht dann ausschließlich im Systemprotokoll, an das man
    ohne Entwicklerwerkzeuge nicht herankommt. Stattdessen wird der
    Fehler hier

        • auf den Bildschirm geschrieben und
        • in eine Datei gelegt, die per USB-Kabel erreichbar ist:
          Android/data/de.kigev.kigpos/files/exports/absturz/

    Auf dem Windows-Rechner bleibt es beim gewohnten Verhalten
    (Fehlermeldung in der Konsole).

Version:
    1.1.0
=========================================================
"""

import traceback


def _absturz_festhalten(meldung):
    """Schreibt den Fehlertext dorthin, wo man ohne Spezialwerkzeug
    herankommt. Gibt den Pfad zurück - oder None, wenn selbst das
    nicht klappt.
    """

    try:
        from datetime import datetime

        import storage

        ziel = storage.export_dir("absturz") / "letzter_absturz.txt"

        ziel.write_text(
            f"KiG POS - Absturz beim Start\n"
            f"{datetime.now():%d.%m.%Y %H:%M:%S}\n\n{meldung}",
            encoding="utf-8",
        )

        return ziel

    except Exception:
        return None


def _absturz_anzeigen(meldung, pfad):
    """Zeigt den Fehler in einem schlichten, scrollbaren Fenster.

    Bewusst ohne jedes Zutun aus dem übrigen Programm: Was hier läuft,
    darf nicht seinerseits von dem abhängen, was gerade kaputt ist.
    """

    from kivy.app import App
    from kivy.core.window import Window
    from kivy.uix.label import Label
    from kivy.uix.scrollview import ScrollView

    text = "KiG POS konnte nicht gestartet werden.\n\n"

    if pfad is not None:
        text += f"Dieser Text steht auch in:\n{pfad}\n\n"

    text += meldung

    class AbsturzApp(App):

        def build(self):

            Window.clearcolor = (1, 1, 1, 1)

            label = Label(
                text=text,
                color=(0, 0, 0, 1),
                font_size="13sp",
                halign="left",
                valign="top",
                size_hint_y=None,
                padding=(20, 20),
            )

            label.bind(
                width=lambda instance, wert: setattr(
                    instance, "text_size", (wert - 40, None)
                ),
                texture_size=lambda instance, groesse: setattr(
                    instance, "height", groesse[1] + 40
                ),
            )

            scroll = ScrollView()
            scroll.add_widget(label)

            return scroll

    AbsturzApp().run()


if __name__ == "__main__":

    try:
        from KiG_POS import KiGPOS

        KiGPOS().run()

    except Exception:

        meldung = traceback.format_exc()

        print(meldung)

        pfad = _absturz_festhalten(meldung)

        # Auf dem Rechner steht die Meldung bereits in der Konsole -
        # ein zusätzliches Fenster wäre dort nur im Weg. Auf dem
        # Telefon ist es die einzige Möglichkeit, den Grund zu sehen.
        try:
            import storage

            if storage.IS_ANDROID:
                _absturz_anzeigen(meldung, pfad)

        except Exception:
            pass

        raise
