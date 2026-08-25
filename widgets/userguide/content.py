"""
=========================================================
KiG POS
=========================================================

Datei:
    widgets/userguide/content.py

Beschreibung:
    Inhalte des Benutzerhandbuchs (Userguide-Screen).

    Jedes Thema entspricht einem Screen der Anwendung und
    besteht aus einer Liste nummerierter Schritte. Ein
    Schritt besteht aus einer Überschrift, einem
    Beschreibungstext und optional einem Screenshot.

    Neue Themen/Schritte einfach unten ergänzen - der
    Userguide-Screen stellt sie automatisch dar, und der
    PDF-Export (widgets/userguide/pdf_export.py) übernimmt
    sie ohne weiteres Zutun mit.

    Themen ohne Schritte zeigen automatisch den Hinweis
    "wird noch ergänzt".

Bildpfade sind relativ zu config.ASSETS_DIR / "userguide".
Die Screenshots werden aus der laufenden Anwendung heraus
aufgenommen - ändert sich ein Screen deutlich, sollten sie
neu erzeugt werden.

Version:
    2.0.0
=========================================================
"""

TOPICS = [

    # =====================================================
    # Erste Schritte
    # =====================================================

    {
        "id": "start",
        "title": "Erste Schritte",
        "steps": [
            {
                "heading": "Aufbau des Programms",
                "text": (
                    "Nach dem Start landest du auf der Startseite. Die "
                    "Kacheln stehen dort in drei Gruppen, damit du "
                    "findest, was du gerade brauchst:\n\n"
                    "Operativ - was während der Veranstaltung läuft: "
                    "Kasse und Kassenbuch.\n\n"
                    "Administrativ - was vorbereitet und ausgewertet "
                    "wird: Artikel, Events, Checkliste und Statistik.\n\n"
                    "Support - Userguide und Einstellungen.\n\n"
                    "Ein Tipp auf eine Kachel öffnet den jeweiligen "
                    "Bereich. Wie viele Kacheln nebeneinander stehen, "
                    "richtet sich nach dem Bildschirm - am Rechner vier, "
                    "auf dem Telefon eine untereinander."
                ),
                "image": "start/01_startseite.png",
            },
            {
                "heading": "Kopfzeile",
                "text": (
                    "Die Kopfzeile ist immer sichtbar. Links das "
                    "Vereinslogo - ein Tipp darauf bringt dich jederzeit "
                    "zurück zur Startseite. In der Mitte steht das "
                    "aktuelle Event des Tages (falls im Kalender "
                    "eines angelegt ist), rechts das Datum, die Uhrzeit "
                    "und der Tagesumsatz. Der Tagesumsatz aktualisiert "
                    "sich automatisch, sobald ein Verkauf abgeschlossen "
                    "oder in der Statistik gelöscht wird."
                ),
            },
            {
                "heading": "Fußzeile",
                "text": (
                    "Unten stehen links Programmname, Version und "
                    "Build-Nummer - diese Angaben helfen bei Rückfragen. "
                    "Rechts beendest du über \"Programm beenden\" die "
                    "Anwendung; damit das nicht versehentlich mitten in "
                    "einer Veranstaltung passiert, kommt vorher eine "
                    "Sicherheitsabfrage."
                ),
            },
            {
                "heading": "Automatische Datensicherung",
                "text": (
                    "Bei jedem Start legt KiG POS eine Sicherungskopie "
                    "der Datenbank an - im Unterordner \"backups\" neben "
                    "der Datenbank selbst. Die letzten 15 Sicherungen "
                    "bleiben erhalten, ältere werden automatisch "
                    "entfernt. Geht etwas schief, lässt sich eine dieser "
                    "Dateien in \"kig.db\" umbenennen und damit der "
                    "Stand eines früheren Abends zurückholen. Sollte die "
                    "Datenbank beim Start nicht lesbar sein, zeigt das "
                    "Programm einen Hinweis mit dem genauen Speicherort, "
                    "statt einfach nicht zu starten."
                ),
            },
            {
                "heading": "Bedienung mit Touch",
                "text": (
                    "Das Programm ist für Touchbedienung ausgelegt: alle "
                    "Schaltflächen sind bewusst großflächig. Längere "
                    "Listen lassen sich mit dem Finger senkrecht "
                    "scrollen. Für Preise und Mengen erscheint das "
                    "Zahlenfeld des Programms; für Namen und Texte die "
                    "Bildschirmtastatur des Geräts - ein externes "
                    "Keyboard ist also nicht nötig."
                ),
            },
            {
                "heading": "Dieses Handbuch",
                "text": (
                    "Links wählst du das Thema, rechts erscheint die "
                    "Anleitung dazu. Über \"Als PDF exportieren\" oben "
                    "rechts speicherst du das komplette Handbuch mit "
                    "allen Screenshots als PDF-Datei - praktisch zum "
                    "Ausdrucken oder Weitergeben an neue Helfer.\n\n"
                    "Nach dem Export steht unter dem Knopf, wie die Datei "
                    "heißt und in welchem Ordner sie liegt.\n\n"
                    "Den PDF-Export gibt es nur in der Windows-Fassung; "
                    "auf dem Telefon ist der Knopf gesperrt. Das "
                    "Handbuch selbst kannst du dort natürlich trotzdem "
                    "lesen."
                ),
                "image": "start/02_handbuch.png",
            },
        ],
    },

    # =====================================================
    # Kasse
    # =====================================================

    {
        "id": "cash",
        "title": "Kasse",
        "steps": [
            {
                "heading": "Überblick",
                "text": (
                    "Der Kassen-Screen ist in drei Bereiche geteilt: "
                    "links die Kategorien als Liste, daneben die "
                    "Artikel als Kacheln, rechts der Warenkorb mit der "
                    "Summe - genauso aufgebaut wie die "
                    "Artikelverwaltung. So lässt sich ein Verkauf mit "
                    "wenigen Berührungen abschließen.\n\n"
                    "Kategorien und Artikel stehen immer nebeneinander, "
                    "auch im Hochformat; dort rückt nur der Warenkorb "
                    "nach unten."
                ),
                "image": "kasse/01_uebersicht.png",
            },
            {
                "heading": "Nach Kategorie filtern",
                "text": (
                    "Ein Tipp auf eine Kategorie zeigt nur noch deren "
                    "Artikel - die gewählte Kategorie wird orange "
                    "hervorgehoben. Ein zweiter Tipp auf dieselbe "
                    "Kategorie hebt den Filter wieder auf und zeigt alle "
                    "Artikel. Kategorien, in denen kein einziger an der "
                    "Kasse verkäuflicher Artikel liegt (z. B. reine "
                    "Zutaten), tauchen hier gar nicht erst auf."
                ),
                "image": "kasse/02_kategorie_filter.png",
            },
            {
                "heading": "Bestand auf den Kacheln lesen",
                "text": (
                    "Jede Artikelkachel zeigt Name, Bestand und Preis. "
                    "Bei normalen Artikeln steht dort \"Bestand\" - also "
                    "das, was tatsächlich im Lager liegt. Bei Mix- bzw. "
                    "Rezeptartikeln steht stattdessen \"Verfügbar\": "
                    "diese Artikel haben keinen eigenen Bestand, die "
                    "Zahl sagt, wie oft die knappste Zutat den Verkauf "
                    "noch hergibt.\n\n"
                    "Ist der Bestand bei 0 oder darunter, wird die "
                    "Kachel leicht grau. Verkaufen lässt sie sich "
                    "weiter - an der Bar wird schon mal nachgeschenkt, "
                    "bevor jemand den Wareneingang bucht -, sie fällt "
                    "nur auf, damit du ans Nachbuchen denkst."
                ),
            },
            {
                "heading": "Artikel suchen",
                "text": (
                    "Über das Suchfeld rechts neben der Überschrift "
                    "\"Artikel\" schränkst du die Kacheln auf einen "
                    "Suchbegriff ein - es genügt ein Teil des Namens, "
                    "\"cola\" findet also auch \"Jacky Cola\". Groß- und "
                    "Kleinschreibung spielen keine Rolle. Das kleine "
                    "Kreuz daneben setzt die Suche zurück; beim Wechsel "
                    "der Kategorie und beim Betreten der Kasse geschieht "
                    "das automatisch."
                ),
            },
            {
                "heading": "Artikel in den Warenkorb legen",
                "text": (
                    "Ein Tipp auf eine Artikelkachel legt den Artikel in "
                    "den Warenkorb. Tippst du denselben Artikel erneut "
                    "an, erhöht sich einfach dessen Menge. Rechts siehst "
                    "du jede Position mit Menge, Einzelpreis und "
                    "Zeilensumme sowie unten die Gesamtsumme.\n\n"
                    "Am rechten Rand jeder Position stehen die Tasten "
                    "\"-\" und \"+\". Damit änderst du die Menge direkt, "
                    "ohne den Umweg über \"Bearbeiten\"."
                ),
                "image": "kasse/03_warenkorb.png",
            },
            {
                "heading": "Menge direkt ändern",
                "text": (
                    "In jeder Warenkorbzeile sitzen die Tasten \"-\" und "
                    "\"+\". Damit änderst du die Menge, ohne den Artikel "
                    "mehrfach antippen oder den Umweg über \"Bearbeiten\" "
                    "gehen zu müssen. Geht die Menge auf 0, verschwindet "
                    "die Position - der schnellste Weg, einen "
                    "versehentlich angetippten Artikel wieder "
                    "loszuwerden."
                ),
            },
            {
                "heading": "Rezept als Hilfe anzeigen",
                "text": (
                    "Tippst du im Warenkorb auf eine Position, die ein "
                    "Rezept hat (Mix-Artikel), erscheint eine Sprechblase "
                    "mit allen Zutaten samt Menge und Einheit - gedacht "
                    "als Gedächtnisstütze für alle hinter der Bar. Die "
                    "Sprechblase verschwindet wieder, sobald du "
                    "irgendwo anders hintippst."
                ),
                "image": "kasse/04_rezept_hinweis.png",
            },
            {
                "heading": "Position ändern",
                "text": (
                    "Wähle eine Position im Warenkorb aus und tippe auf "
                    "\"Bearbeiten\". Im Panel kannst du die Menge über "
                    "Plus/Minus anpassen, den Preis für diesen einen "
                    "Verkauf abändern (z. B. Sonderpreis), die Position "
                    "duplizieren oder löschen. \"Übernehmen\" schließt "
                    "die Bearbeitung ab, \"Abbrechen\" verwirft sie.\n\n"
                    "Das Panel legt sich dabei über die Oberfläche, "
                    "rechts neben dem Warenkorb: Kategorien, Artikel und "
                    "Warenkorb behalten ihren Platz und rücken nicht "
                    "zusammen. Dasselbe gilt für \"Bezahlen\" und den "
                    "Nummernblock - sind Bearbeiten-Panel und "
                    "Nummernblock gleichzeitig offen, stehen sie "
                    "nebeneinander."
                ),
                "image": "kasse/05_position_bearbeiten.png",
            },
            {
                "heading": "Warenkorb leeren",
                "text": (
                    "Über \"Leeren\" oben rechts wird der komplette "
                    "Warenkorb verworfen. Das ist folgenlos: Solange "
                    "nicht bezahlt wurde, ändert sich am Bestand nichts."
                ),
            },
            {
                "heading": "Stornieren",
                "text": (
                    "Ist ein Verkauf bereits abgeschlossen und war "
                    "falsch, hilft \"Storno\" oben neben \"Leeren\". Der "
                    "Warenkorb färbt sich rot und trägt den Hinweis "
                    "\"Zu stornierende Artikel antippen\" - es ist also "
                    "immer erkennbar, dass gerade nicht verkauft, "
                    "sondern zurückgenommen wird. Tippe die betroffenen "
                    "Artikel an und schließe mit \"Storno buchen\" ab; "
                    "danach folgt noch eine Sicherheitsabfrage. "
                    "\"Abbrechen\" verwirft den Vorgang, ohne dass "
                    "etwas gebucht wird."
                ),
                "image": "kasse/07_storno.png",
            },
            {
                "heading": "Was ein Storno bewirkt",
                "text": (
                    "Der ursprüngliche Verkauf bleibt stehen; das Storno "
                    "kommt als eigene Gegenbuchung mit negativer Menge "
                    "dazu. In der Statistik erscheint es rot hinterlegt "
                    "mit dem Zusatz \"Storno\", und Umsatz wie Gewinn "
                    "verrechnen sich automatisch. So bleibt "
                    "nachvollziehbar, was passiert ist - wichtig, wenn "
                    "am Ende des Abends die Kasse stimmen soll."
                ),
            },
            {
                "heading": "Storno und Bestand",
                "text": (
                    "Zurück ins Lager geht nur, was verschlossen "
                    "übergeben wurde: Einzelartikel wie Flaschen und "
                    "Dosen werden dem Bestand wieder gutgeschrieben, und "
                    "auch ihr Einkaufspreis wird gegengerechnet - der "
                    "Vorgang ist damit vollständig neutralisiert. Bei "
                    "Mix- und Rezeptartikeln bleibt der Bestand "
                    "unverändert: Das Getränk ist eingeschenkt und die "
                    "Zutaten sind verbraucht. Deren Einkaufspreis lässt "
                    "sich nicht zurückholen und bleibt als Verlust in "
                    "der Auswertung stehen. Jeder Storno wird zusätzlich "
                    "in der Bestandshistorie des Artikels vermerkt."
                ),
            },
            {
                "heading": "Bezahlen",
                "text": (
                    "\"Bezahlen\" öffnet den Zahlungsbereich. Über das "
                    "Zahlenfeld gibst du den erhaltenen Betrag ein - das "
                    "Rückgeld wird sofort mitgerechnet. Erst wenn der "
                    "gegebene Betrag mindestens der Summe entspricht, "
                    "lässt sich der Verkauf mit \"OK\" abschließen. "
                    "\"Abbrechen\" bricht den Zahlvorgang ab, der "
                    "Warenkorb bleibt erhalten."
                ),
                "image": "kasse/06_bezahlen.png",
            },
            {
                "heading": "Was beim Abschluss passiert",
                "text": (
                    "Mit dem Abschluss wird der Verkauf für die Statistik "
                    "gespeichert und der Bestand abgezogen: bei normalen "
                    "Artikeln der Artikel selbst, bei Mix-Artikeln "
                    "stattdessen jede einzelne Zutat in der im Rezept "
                    "hinterlegten Menge. Anschließend aktualisieren sich "
                    "Tagesumsatz und die Bestände auf den Kacheln "
                    "automatisch."
                ),
            },
        ],
    },

    # =====================================================
    # Artikelverwaltung
    # =====================================================

    {
        # Fasst die frueher getrennten Screens Artikel, Einkauf,
        # Inventar und Rezepte zusammen (siehe products_screen.py).
        "id": "products",
        "title": "Artikelverwaltung",
        "steps": [
            {
                "heading": "Überblick",
                "text": (
                    "Die Artikelverwaltung fasst alles rund um Artikel "
                    "an einem Ort zusammen: Stammdaten, Bestand, Einkauf "
                    "und Rezepte. Links stehen die Kategorien, rechts die "
                    "Artikelliste mit Verkaufs- und Einkaufspreis, "
                    "Bestand und offener Bestellmenge."
                ),
                "image": "artikel/01_liste.png",
            },
            {
                "heading": "Nach Kategorie filtern",
                "text": (
                    "Ein Tipp auf eine Kategorie links zeigt nur deren "
                    "Artikel, ein zweiter Tipp hebt den Filter wieder "
                    "auf. Die Überschrift der Liste zeigt jeweils mit an, "
                    "welche Kategorie gerade gefiltert ist."
                ),
            },
            {
                "heading": "Kategorien anlegen und ändern",
                "text": (
                    "Über \"Neu\" legst du eine neue Kategorie an. Um "
                    "eine bestehende zu ändern, wähle sie zuerst in der "
                    "Liste aus und tippe dann auf \"Bearbeiten\" - dort "
                    "kannst du sie umbenennen oder löschen. Löschen geht "
                    "nur, solange kein Artikel mehr in der Kategorie "
                    "liegt."
                ),
                "image": "artikel/02_kategorie_anlegen.png",
            },
            {
                "heading": "Bestellmenge erfassen und buchen",
                "text": (
                    "In der Spalte \"Menge\" trägst du direkt in der "
                    "Liste ein, wie viel nachbestellt werden soll. Ist "
                    "die Ware da, bucht \"Buchen\" die Menge sofort dem "
                    "Bestand zu und leert das Mengenfeld wieder. Bei "
                    "Mix-/Rezeptartikeln sind beide Felder ausgegraut - "
                    "sie führen keinen eigenen Bestand."
                ),
            },
            {
                "heading": "Einkaufsliste exportieren",
                "text": (
                    "\"Einkaufsliste exportieren\" schreibt alle Artikel "
                    "mit eingetragener Bestellmenge in eine CSV-Datei "
                    "(Kategorie, Artikel, Menge). Sie landet im Ordner "
                    "exports/csv des Programmverzeichnisses und lässt "
                    "sich mit Excel öffnen oder direkt verschicken.\n\n"
                    "Nach dem Export steht unter dem Knopf, wie die Datei "
                    "heißt und in welchem Ordner sie liegt."
                ),
            },
            {
                "heading": "Reihenfolge festlegen",
                "text": (
                    "Über \"Sortierung\" bestimmst du, in welcher "
                    "Reihenfolge die Artikel an der Kasse erscheinen. "
                    "Das lohnt sich, um die meistverkauften Artikel nach "
                    "vorne zu holen."
                ),
            },
            {
                "heading": "Artikel bearbeiten",
                "text": (
                    "\"Bearbeiten\" öffnet das Dashboard eines Artikels "
                    "und ersetzt dabei die Liste. Bei normalen Artikeln "
                    "siehst du drei Karten nebeneinander: Stammdaten, "
                    "Bestand und Einkauf/Bestellmenge. Über \"← Zurück\" "
                    "kommst du wieder zur Liste."
                ),
                "image": "artikel/03_dashboard_einzelartikel.png",
            },
            {
                "heading": "Stammdaten pflegen",
                "text": (
                    "In der Karte \"Stammdaten\" steht links die "
                    "Bezeichnung, rechts das jeweilige Feld: Name, "
                    "Einheit, Verkaufspreis, Einkaufspreis, Kategorie und "
                    "Artikeltyp. Der Schalter \"Verkauf an Kasse\" "
                    "steuert, ob der Artikel im Kassen-Screen auftaucht - "
                    "reine Zutaten schaltest du hier aus. \"Aktiv\" "
                    "blendet einen Artikel komplett aus, ohne die "
                    "Verkaufshistorie zu verlieren. Änderungen werden "
                    "erst mit \"Speichern\" übernommen."
                ),
            },
            {
                "heading": "Bestand korrigieren",
                "text": (
                    "\"Bestand anpassen\" öffnet die Bestandskorrektur "
                    "für eine Inventur oder zum Ausbuchen von Bruch. "
                    "Neben dem neuen Bestand musst du einen Grund und "
                    "deinen Namen angeben - beides landet in der "
                    "Änderungshistorie, die direkt darunter mitläuft. So "
                    "ist später nachvollziehbar, wer wann was geändert "
                    "hat."
                ),
                "image": "artikel/04_bestandskorrektur.png",
            },
            {
                "heading": "Neuen Artikel anlegen",
                "text": (
                    "\"+ Neuer Artikel\" öffnet ein leeres Formular. "
                    "Trage zuerst den Namen ein und wähle dann die "
                    "Einheit - davon hängt ab, welche Felder überhaupt "
                    "abgefragt werden. Nach dem Speichern landest du "
                    "wieder in der Liste; Bestand, Bestellmenge und "
                    "Rezept lassen sich erst danach pflegen."
                ),
                "image": "artikel/07_neuer_artikel.png",
            },
            {
                "heading": "Mix- und Rezeptartikel",
                "text": (
                    "Setzt du den Artikeltyp auf \"Mix / Rezept\", "
                    "erscheint statt Bestand und Einkauf die Karte "
                    "\"Zusammensetzung\". Solche Artikel führen keinen "
                    "eigenen Bestand - beim Verkauf werden stattdessen "
                    "die Zutaten abgezogen. Der Einkaufspreis entfällt "
                    "deshalb ebenfalls: Er ergibt sich aus den Zutaten."
                ),
                "image": "artikel/05_rezept.png",
            },
            {
                "heading": "Zutaten zuordnen",
                "text": (
                    "Wähle unten die Zutat aus, trage die Menge ein, "
                    "prüfe die Einheit und tippe auf \"Hinzufügen\". Im "
                    "Auswahlfeld stehen nur echte Zutaten-Artikel, also "
                    "solche, die nicht an der Kasse verkauft werden. Die "
                    "Einheit lässt sich nur auf passende Werte umstellen "
                    "(z. B. ml/cl/l) - so kann beim Lagerabzug nichts "
                    "durcheinandergeraten."
                ),
            },
            {
                "heading": "Zutaten ohne eigenen Artikel",
                "text": (
                    "Für Dinge, die man nicht im Bestand führen möchte - "
                    "Minze, Limettenscheibe, brauner Zucker - gibt es die "
                    "Zeile \"...oder eine Zutat ohne Artikel eintragen\". "
                    "Name, Menge und eine frei wählbare Einheit genügen. "
                    "Solche Zutaten erscheinen im Rezept und in der "
                    "Sprechblase an der Kasse, werden aber nicht vom "
                    "Bestand abgezogen."
                ),
            },
            {
                "heading": "Verfügbarkeit und Kosten je Portion",
                "text": (
                    "Über der Zutatenliste steht, wie oft sich das Rezept "
                    "mit dem aktuellen Zutatenbestand noch verkaufen "
                    "lässt (begrenzt durch die knappste Zutat) und was "
                    "eine Portion im Einkauf kostet - anteilig "
                    "hochgerechnet aus den Kosten aller Zutaten. Ein "
                    "Shot von 20 ml aus einer Flasche, deren Inhalt mit "
                    "0,0429 € je ml zu Buche steht, kostet also 0,86 €. "
                    "Dieser Preis fließt beim Verkauf automatisch in die "
                    "Gewinnermittlung der Statistik ein.\n\n"
                    "Steht dort in Rot \"Einkaufspreis unbestimmt\", "
                    "fehlt bei mindestens einer Zutat der Preis - meist, "
                    "weil für eine Flasche noch kein Wareneingang mit "
                    "Preis gebucht wurde. Solche Verkäufe werden mit "
                    "0,00 € Einkauf erfasst, der Gewinn steht dann zu "
                    "hoch."
                ),
            },
            {
                "heading": "Spirituosen als Flasche führen",
                "text": (
                    "Wählst du bei der Einheit \"Flasche\", handelt es "
                    "sich immer um eine reine Lagerzutat. Kategorie, "
                    "Artikeltyp, Verkaufspreis und der Verkauf-Schalter "
                    "entfallen dann, weil sie feststehen. Der Bestand "
                    "wird intern immer in Millilitern geführt - beim "
                    "Buchen fragt das Programm in zwei Schritten nach "
                    "der Flaschengröße und dem Preis je Flasche und "
                    "rechnet selbst um. Der Bestand zeigt zusätzlich an, "
                    "wie vielen Flaschen die Milliliter entsprechen.\n\n"
                    "Aus Größe und Preis ergeben sich die Kosten je "
                    "Milliliter - nur damit kann ein Rezept anteilig "
                    "rechnen. Beide Angaben dürfen sich bei jedem "
                    "Einkauf ändern: Kaufst du erst 0,7 l für 30 € und "
                    "danach 1 l für 35 €, führt das Programm beides "
                    "zusammen (65 € auf 1700 ml) und rechnet ab dann mit "
                    "diesem Mischpreis. So passt der Wert immer zu dem, "
                    "was tatsächlich im Regal steht."
                ),
                "image": "artikel/06_flasche_und_shot.png",
            },
            {
                "heading": "Flasche zusätzlich als Shot verkaufen",
                "text": (
                    "Der Schalter \"Auch als Shot verkaufen\" legt dir "
                    "automatisch einen passenden Verkaufsartikel an. Du "
                    "gibst nur Kassenname, Portionsgröße in ml, Preis je "
                    "Shot und Kategorie an - das Programm erstellt daraus "
                    "einen Mix-Artikel, der beim Verkauf genau diese "
                    "Menge von der Flasche abzieht. Der Name muss sich "
                    "vom Flaschennamen unterscheiden, da jeder Artikel "
                    "nur einmal vorkommen darf. Schaltest du den Regler "
                    "wieder aus, verschwindet der Shot aus der Kasse."
                ),
            },
            {
                "heading": "Artikel löschen",
                "text": (
                    "Das rote Kreuz am Ende einer Listenzeile entfernt "
                    "einen Artikel nach einer Sicherheitsabfrage aus der "
                    "Übersicht. Er wird dabei nur deaktiviert, nicht "
                    "wirklich gelöscht - bereits erfasste Verkäufe "
                    "bleiben in der Statistik also vollständig erhalten."
                ),
            },
        ],
    },

    # =====================================================
    # Kalender
    # =====================================================

    {
        "id": "events",
        "title": "Kalender",
        "steps": [
            {
                "heading": "Überblick",
                "text": (
                    "Der Kalender zeigt einen Monat am Stück. Der heutige "
                    "Tag ist orange hervorgehoben, Tage mit Einträgen sind "
                    "gekennzeichnet. Über die Pfeile links und rechts "
                    "neben dem Monatsnamen blätterst du zwischen den "
                    "Monaten, über das Auswahlfeld springst du direkt zu "
                    "einem bestimmten Monat."
                ),
                "image": "kalender/01_uebersicht.png",
            },
            {
                "heading": "Einen Tag öffnen",
                "text": (
                    "Ein Tipp auf einen Tag öffnet dessen Übersicht mit "
                    "allen Einträgen. Von dort legst du über \"Neu\" "
                    "einen weiteren Eintrag an oder tippst einen "
                    "bestehenden an, um ihn zu bearbeiten. \"Schließen\" "
                    "bringt dich zurück zum Kalender."
                ),
                "image": "kalender/02_tag.png",
            },
            {
                "heading": "Eintragsarten",
                "text": (
                    "Es gibt drei Arten: \"Event\" für Veranstaltungen, "
                    "\"Barschicht\" für die Diensteinteilung und "
                    "\"Termin\" für alles Übrige. Bei einer Barschicht "
                    "trägst du die Namen der arbeitenden Personen ein, "
                    "bei Event und Termin den Namen der Veranstaltung."
                ),
            },
            {
                "heading": "Eintrag speichern oder löschen",
                "text": (
                    "\"Speichern\" übernimmt den Eintrag, \"Abbrechen\" "
                    "verwirft ihn. Bearbeitest du einen bestehenden "
                    "Eintrag, gibt es zusätzlich \"Löschen\". Ein leeres "
                    "Namensfeld wird nicht gespeichert."
                ),
            },
            {
                "heading": "Zusammenspiel mit Kasse und Statistik",
                "text": (
                    "Liegt für den aktuellen Geschäftstag ein Event vor, "
                    "erscheint dessen Name in der Kopfzeile, und alle "
                    "Verkäufe dieses Tages werden dem Event zugeordnet. "
                    "In der Statistik kannst du später gezielt nach "
                    "diesem Event auswerten. Ein Geschäftstag läuft dabei "
                    "von 6:00 Uhr morgens bis 5:59 Uhr des Folgetags - "
                    "Verkäufe nach Mitternacht zählen also noch zur "
                    "Veranstaltung des Vorabends."
                ),
            },
        ],
    },

    # =====================================================
    # Kassenbuch
    # =====================================================

    {
        "id": "cashbook",
        "title": "Kassenbuch",
        "steps": [
            {
                "heading": "Wozu das Kassenbuch",
                "text": (
                    "Die Statistik beantwortet, was verkauft wurde. Das "
                    "Kassenbuch beantwortet eine andere Frage: Was liegt "
                    "tatsächlich in der Kasse? Dort landen auch "
                    "Wechselgeld, Einlagen und Entnahmen - Beträge, die "
                    "nie über die Kasse gebucht werden.\n\n"
                    "Je Tag eine Zeile: Womit die Kasse begonnen hat, "
                    "was hinein- und was herausgegangen ist, womit sie "
                    "geschlossen wurde."
                ),
                "image": "kassenbuch/01_uebersicht.png",
            },
            {
                "heading": "Zeitraum wählen",
                "text": (
                    "Links wählst du oben das Jahr und darunter den "
                    "Monat. Die Tabelle zeigt immer genau diesen Monat. "
                    "Angeboten werden alle Jahre, in denen etwas erfasst "
                    "ist, dazu das laufende - beim allerersten Eintrag "
                    "steht also schon ein Jahr zur Auswahl."
                ),
            },
            {
                "heading": "Die Tabelle lesen",
                "text": (
                    "Datum, Startbestand, Einnahmen, Ausgaben, "
                    "Endbestand, Kommentar und Prüfer. Unter der Tabelle "
                    "stehen die Summen des Monats und der zuletzt "
                    "erfasste Kassenstand."
                ),
            },
            {
                "heading": "Wenn die Rechnung nicht aufgeht",
                "text": (
                    "Geprüft wird zweierlei.\n\n"
                    "Innerhalb einer Zeile: Startbestand plus Einnahmen "
                    "minus Ausgaben muss den Endbestand ergeben.\n\n"
                    "Von Zeile zu Zeile: Der Startbestand einer Zeile "
                    "muss dem Endbestand der Zeile davor entsprechen. "
                    "Was am Abend in der Kasse lag, liegt am nächsten "
                    "Morgen noch darin - ist das nicht so, fehlt eine "
                    "Buchung. Bei einer Lücke bekommen beide beteiligten "
                    "Zeilen den Hinweis, denn von außen ist nicht zu "
                    "sagen, welche der beiden falsch ist. Auch der "
                    "Übertrag in einen neuen Monat wird so geprüft.\n\n"
                    "Gibt es einen Befund, steht in der Spalte "
                    "\"Kommentar\" ein rotes \"Prüfen\" - dein eigener "
                    "Kommentar tritt dann zurück, damit der Hinweis "
                    "nicht untergeht. Stimmt alles, steht dort einfach "
                    "dein Kommentar oder gar nichts."
                ),
            },
            {
                "heading": "Kassenbuch exportieren",
                "text": (
                    "\"Excel exportieren\" schreibt den angezeigten "
                    "Monat als Tabelle in den Ordner exports/excel - "
                    "eingerichtet zum Ausdrucken: Querformat, auf eine "
                    "Seitenbreite passend, mit wiederholter Kopfzeile "
                    "und einer Summenzeile.\n\n"
                    "Die letzte Spalte \"Hinweis\" nennt bei "
                    "auffälligen Zeilen den Grund im Klartext. Auf "
                    "Papier hilft ein rotes \"Prüfen\" ohne Erklärung "
                    "niemandem weiter - der Kassenprüfer sieht so "
                    "sofort, woran es liegt.\n\n"
                    "Nach dem Export steht unter dem Knopf, wie die Datei "
                    "heißt und in welchem Ordner sie liegt."
                ),
            },
            {
                "heading": "Eine Zeile erfassen",
                "text": (
                    "Rechts trägst du eine Zeile ein: Datum über den "
                    "Kalender, die vier Beträge über den Nummernblock, "
                    "Kommentar und Prüfer über die Tastatur. "
                    "\"Speichern\" legt die Zeile an.\n\n"
                    "Zwei Hilfen nimmt dir das Programm ab: Der "
                    "Startbestand wird mit dem Endbestand des letzten "
                    "Eintrags davor vorbelegt - in der Kasse liegt am "
                    "Morgen das, was am Abend zuvor drin lag. Und der "
                    "Endbestand rechnet sich beim Tippen mit, solange du "
                    "ihn nicht selbst überschreibst. Weicht das Gezählte "
                    "ab, trägst du einfach den echten Betrag ein - dann "
                    "erscheint der Hinweis \"Prüfen\"."
                ),
            },
            {
                "heading": "Zeile ändern oder löschen",
                "text": (
                    "Ein Tipp auf eine Zeile lädt sie ins Eingabefeld. "
                    "Nach dem Ändern speicherst du erneut; \"Löschen\" "
                    "entfernt die Zeile nach einer Rückfrage.\n\n"
                    "Ein zweiter Tipp auf dieselbe Zeile hebt die "
                    "Auswahl wieder auf - dann steht rechts eine leere "
                    "Zeile für den nächsten Tag bereit."
                ),
            },
        ],
    },

    # =====================================================
    # Checkliste
    # =====================================================

    {
        "id": "checklist",
        "title": "Checkliste",
        "steps": [
            {
                "heading": "Wozu Checklisten",
                "text": (
                    "Vor einem Fest ist an vieles zu denken: "
                    "Genehmigung, Kühlwagen, Wechselgeld, Helferplan. "
                    "Hier legst du für jeden Anlass eine eigene Liste "
                    "an und hakst ab, was erledigt ist.\n\n"
                    "Links stehen die Listen, rechts die Aufgaben der "
                    "gewählten Liste."
                ),
                "image": "checkliste/01_uebersicht.png",
            },
            {
                "heading": "Listen anlegen und löschen",
                "text": (
                    "\"Neue Liste\" fragt nach einem Namen - zum "
                    "Beispiel \"Stadtfest 2026\". Ein Tipp auf einen "
                    "Namen zeigt dessen Aufgaben; hinter dem Namen steht, "
                    "wie viele davon schon erledigt sind.\n\n"
                    "\"Löschen\" entfernt die gewählte Liste samt ihrer "
                    "Aufgaben - nach einer Rückfrage, die die Anzahl "
                    "nennt."
                ),
            },
            {
                "heading": "Aufgaben eintragen",
                "text": (
                    "Unten schreibst du die Aufgabe ins Feld und tippst "
                    "auf \"Hinzufügen\" - oder drückst die Eingabetaste. "
                    "Die neue Aufgabe hängt sich unten an."
                ),
            },
            {
                "heading": "Eine Aufgabenzeile",
                "text": (
                    "Ganz links das Kästchen: Ein Tipp hakt die Aufgabe "
                    "ab, ein weiterer nimmt den Haken zurück. Erledigte "
                    "Aufgaben bleiben stehen, treten aber zurück.\n\n"
                    "Daneben die Aufgabe selbst, dahinter die "
                    "Zusatzangaben: Frist über den Kalender, "
                    "Verantwortlich, Ansprechpartner und ein freies Feld "
                    "für Infos. Geändert wird direkt in der Zeile; "
                    "gespeichert wird, sobald du ein Feld verlässt."
                ),
            },
            {
                "heading": "Checkliste exportieren",
                "text": (
                    "\"Excel exportieren\" schreibt die gewählte Liste "
                    "in den Ordner exports/excel, eingerichtet zum "
                    "Ausdrucken. So kann die Liste am Stand hängen, ohne "
                    "dass jemand das Tablet mit sich herumträgt - "
                    "erledigte Punkte sind dort mit einem x "
                    "gekennzeichnet.\n\n"
                    "Nach dem Export steht unter dem Knopf, wie die Datei "
                    "heißt und in welchem Ordner sie liegt."
                ),
            },
        ],
    },

    # =====================================================
    # Schichtplan
    # =====================================================

    {
        "id": "shiftplan",
        "title": "Schichtplan",
        "steps": [
            {
                "heading": "Wozu ein Schichtplan",
                "text": (
                    "Er beantwortet eine einzige Frage: Wo fehlen noch "
                    "Helfer?\n\n"
                    "Links stehen die Veranstaltungen mit Plan, rechts "
                    "deren Schichten. Je Schicht siehst du, wie viele "
                    "gebraucht werden und wie viele eingetragen sind - "
                    "und der Balken daneben zeigt dasselbe auf einen "
                    "Blick."
                ),
                "image": "schichtplan/01_uebersicht.png",
            },
            {
                "heading": "Die Farben",
                "text": (
                    "Grün heißt: besetzt, hier ist nichts mehr zu tun.\n\n"
                    "Orange heißt: teilweise besetzt, es fehlt noch "
                    "jemand.\n\n"
                    "Rot heißt: für diese Schicht hat sich noch niemand "
                    "eingetragen. In der Spalte \"Helfer\" steht dann "
                    "\"niemand\".\n\n"
                    "Über der Tabelle steht dasselbe in Worten, zum "
                    "Beispiel \"11 von 15 Plätzen besetzt · 2 Schichten "
                    "brauchen noch Helfer\"."
                ),
            },
            {
                "heading": "Einen Plan anlegen",
                "text": (
                    "Am einfachsten gleich im Kalender: Beim Anlegen "
                    "einer Veranstaltung kannst du \"Schichtplan dazu "
                    "anlegen\" ankreuzen - und gleich daneben auch eine "
                    "Checkliste mit demselben Namen.\n\n"
                    "Später geht es auch hier über \"Plan anlegen\". "
                    "Angeboten werden dann die Veranstaltungen, die noch "
                    "keinen Plan haben."
                ),
            },
            {
                "heading": "Schichten eintragen",
                "text": (
                    "Unten die Tätigkeit ins Feld schreiben und auf "
                    "\"Hinzufügen\" tippen - zum Beispiel \"Theke\", "
                    "\"Grill\" oder \"Aufbau\".\n\n"
                    "In der Zeile stehen dann Uhrzeit von und bis "
                    "(einfach hineinschreiben, etwa 18:00) und hinter "
                    "\"Ist / Soll\" die Zahl der benötigten Helfer. Ein "
                    "Tipp darauf öffnet den Nummernblock.\n\n"
                    "Getrennte Schichten je Uhrzeit lohnen sich: Meist "
                    "ist nicht die Tätigkeit das Problem, sondern die "
                    "späte Stunde."
                ),
            },
            {
                "heading": "Helfer eintragen",
                "text": (
                    "Ein Tipp auf die Spalte \"Helfer\" öffnet die Liste "
                    "der Schicht. Dort trägst du Namen ein und nimmst sie "
                    "mit dem roten Kreuz wieder heraus.\n\n"
                    "Die Zahl vor dem Schrägstrich zählt sich selbst - "
                    "sie ist schlicht die Anzahl der eingetragenen Namen "
                    "und kann deshalb nie mit der Wirklichkeit "
                    "auseinanderlaufen."
                ),
            },
            {
                "heading": "Schichten übernehmen",
                "text": (
                    "\"Schichten übernehmen\" holt das Gerüst einer "
                    "anderen Veranstaltung herüber: dieselben "
                    "Tätigkeiten, Zeiten und Bedarfszahlen. Die Helfer "
                    "bleiben außen vor - wer letztes Jahr da war, sagt "
                    "nichts darüber, wer dieses Jahr kann.\n\n"
                    "Beim Stadtfest, das jedes Jahr gleich abläuft, "
                    "spart das die halbe Arbeit."
                ),
            },
            {
                "heading": "Schichtplan exportieren",
                "text": (
                    "\"Excel exportieren\" schreibt den Plan zum "
                    "Ausdrucken: Tätigkeit, Zeit, Soll, Ist, wie viele "
                    "fehlen und die Namen. So hängt der Plan am Stand, "
                    "ohne dass jemand das Tablet mit sich herumträgt.\n\n"
                    "Nach dem Export steht unter dem Knopf, wie die Datei "
                    "heißt und in welchem Ordner sie liegt."
                ),
            },
        ],
    },

    # =====================================================
    # Statistik
    # =====================================================

    {
        "id": "statistics",
        "title": "Statistik",
        "steps": [
            {
                "heading": "Überblick",
                "text": (
                    "Der Statistik-Screen zeigt alle über die Kasse "
                    "abgeschlossenen Verkäufe. Links siehst du die "
                    "einzelnen Verkaufspositionen als Tabelle, rechts "
                    "eine Zusammenfassung mit den meistverkauften "
                    "Artikeln und den Gesamteinnahmen je Artikel."
                ),
                "image": "statistik/01_uebersicht.png",
            },
            {
                "heading": "Nach Event filtern",
                "text": (
                    "Über das Auswahlfeld \"Alle Events\" oben links "
                    "kannst du die Liste auf ein einzelnes, im Kalender "
                    "angelegtes Event einschränken. \"Alle Events\" "
                    "zeigt wieder sämtliche Verkäufe ohne "
                    "Event-Einschränkung."
                ),
            },
            {
                "heading": "Nach Zeitraum filtern",
                "text": (
                    "Über die Schaltflächen \"Von\" und \"Bis\" öffnest "
                    "du je einen Kalender und wählst das Datum direkt "
                    "aus. Mit dem kleinen Kreuz daneben setzt du ein "
                    "Datum wieder zurück, um den Zeitraum nur nach oben "
                    "oder unten zu begrenzen. \"Aktualisieren\" wendet "
                    "den Filter an."
                ),
            },
            {
                "heading": "Verkaufsliste lesen",
                "text": (
                    "Jede Zeile zeigt Event, Datum, Kategorie, Artikel "
                    "sowie Verkaufspreis, Einkaufspreis und den daraus "
                    "berechneten Gewinn der jeweiligen Position. Bei "
                    "Mix-Artikeln stammt der Einkaufspreis aus den "
                    "Zutaten, hochgerechnet auf die verkaufte Portion. "
                    "Die Liste lässt sich senkrecht scrollen."
                ),
            },
            {
                "heading": "Einzelne Positionen löschen",
                "text": (
                    "Tippe eine oder mehrere Zeilen an, um sie "
                    "auszuwählen - ausgewählte Zeilen werden orange "
                    "hervorgehoben. Über \"Ausgewählte löschen\" werden "
                    "genau diese Positionen nach einer Sicherheitsabfrage "
                    "entfernt. Betrifft eine gelöschte Position den "
                    "heutigen Tag, aktualisiert sich der Tagesumsatz in "
                    "der Kopfzeile sofort mit."
                ),
                "image": "statistik/02_zeile_gewaehlt.png",
            },
            {
                "heading": "Ganzen Zeitraum löschen",
                "text": (
                    "Über \"Zeitraum löschen\" werden alle Verkäufe im "
                    "aktuell gewählten Von/Bis-Zeitraum auf einmal "
                    "gelöscht - dafür müssen beide Datumsfelder gesetzt "
                    "sein. Auch hier erscheint vorher eine "
                    "Sicherheitsabfrage, da sich dieser Schritt nicht "
                    "rückgängig machen lässt."
                ),
            },
            {
                "heading": "Nach Excel exportieren",
                "text": (
                    "\"Excel exportieren\" schreibt die aktuelle "
                    "Auswertung in eine Excel-Datei: ein Blatt mit allen "
                    "Verkaufspositionen und ein Blatt mit der "
                    "Zusammenfassung inklusive Diagrammen. Die Datei "
                    "landet im Ordner exports/excel des "
                    "Programmverzeichnisses.\n\n"
                    "Nach dem Export steht unter dem Knopf, wie die Datei "
                    "heißt und in welchem Ordner sie liegt."
                ),
            },
            {
                "heading": "Gesamtverkaufszahlen",
                "text": (
                    "Oben rechts stehen die Zahlen des gewählten "
                    "Ausschnitts: Einnahmen, Ausgaben und der Gewinn "
                    "als Differenz. Die Zeile darunter nennt Zeitraum, "
                    "Event und den Umfang - so ist immer klar, worauf "
                    "sich die Beträge beziehen.\n\n"
                    "Das Kreisdiagramm zeigt, wie sich die Einnahmen auf "
                    "die Kategorien verteilen, in den Farben, die du den "
                    "Kategorien gegeben hast. Die Legende nennt Anteil "
                    "und Betrag."
                ),
            },
            {
                "heading": "Top-Artikel",
                "text": (
                    "Unten rechts zeigt das Balkendiagramm die "
                    "meistverkauften Artikel nach Menge - praktisch, um "
                    "auf einen Blick die Verkaufsschlager zu erkennen."
                ),
            },
            {
                "heading": "Einkaufspreise nachtragen",
                "text": (
                    "Wurde ein Rezeptartikel verkauft, während der Preis "
                    "seiner Zutaten noch unbestimmt war, steht in der "
                    "Verkaufsliste 0,00 € Einkauf - der Gewinn ist dann "
                    "zu hoch ausgewiesen. In diesem Fall erscheint über "
                    "der Tabelle ein roter Hinweis mit der Zahl der "
                    "betroffenen Verkäufe.\n\n"
                    "Buche zuerst bei den Zutaten den Wareneingang mit "
                    "Preis, dann trägt \"Einkaufspreise nachtragen\" den "
                    "heute gültigen Rezeptpreis bei diesen Verkäufen "
                    "nach. Das ändert Zahlen einer abgeschlossenen "
                    "Abrechnung und passiert deshalb nur auf "
                    "ausdrückliche Bestätigung."
                ),
            },
            {
                "heading": "Alles folgt dem Filter",
                "text": (
                    "Kennzahlen, Kreisdiagramm und Balkendiagramm zeigen "
                    "immer denselben Ausschnitt wie die Tabelle links. "
                    "Grenzt du den Zeitraum ein oder wählst ein Event, "
                    "rechnet die ganze rechte Spalte mit - für die "
                    "Abrechnung nach einer Veranstaltung genügt es also, "
                    "oben das Event auszuwählen."
                ),
            },
        ],
    },

    # =====================================================
    # Einstellungen
    # =====================================================

    {
        "id": "settings",
        "title": "Einstellungen",
        "steps": [
            {
                "heading": "Farbmodus umstellen",
                "text": (
                    "Unter \"Farbmodus\" wechselst du zwischen hellem und "
                    "dunklem Erscheinungsbild. Der dunkle Modus ist "
                    "angenehmer bei Abendveranstaltungen und schont in "
                    "dunkler Umgebung die Augen. Die Umstellung wirkt "
                    "sofort im ganzen Programm."
                ),
                "image": "einstellungen/01_uebersicht.png",
            },
            {
                "heading": "Hoch- oder Querformat wählen",
                "text": (
                    "Unter \"Bildschirmausrichtung\" stellst du ein, wie "
                    "das Programm aufgebaut wird. Im Querformat stehen "
                    "zusammengehörige Bereiche nebeneinander - an der "
                    "Kasse zum Beispiel die Artikel links und der "
                    "Warenkorb rechts. Im Hochformat stehen dieselben "
                    "Bereiche untereinander: Artikel oben, Warenkorb "
                    "unten. Das ist für hochkant montierte Bildschirme "
                    "und Tablets gedacht.\n\n"
                    "Beim allerersten Start wählt das Programm selbst, was "
                    "zum Bildschirm passt - am Rechner Querformat, auf "
                    "einem hochkanten Telefon Hochformat. Danach gilt, "
                    "was hier eingestellt ist."
                ),
            },
            {
                "heading": "Was sich im Hochformat ändert",
                "text": (
                    "Am Rechner wird das Fenster beim Umschalten "
                    "automatisch schmaler und höher; auf einem Gerät mit "
                    "Drehsensor drehst du es einfach. Die Startseite zeigt zwei "
                    "Kacheln je Reihe statt drei, in der Artikelliste "
                    "steht jeder Artikel zweizeilig (oben Name und "
                    "Kategorie, darunter Preise, Bestand und die "
                    "Schaltflächen), und der Nummernblock sowie das "
                    "Bearbeiten-Fenster nutzen die ganze Fläche, solange "
                    "sie geöffnet sind. Es geht dabei keine Funktion "
                    "verloren - alles ist nur anders angeordnet."
                ),
            },
            {
                "heading": "Demo-Modus",
                "text": (
                    "Unter \"Demo\" startest du eine Spielwiese: Das "
                    "Programm friert den aktuellen Stand der Datenbank "
                    "ein und arbeitet ab da auf einer Kopie. Alles "
                    "funktioniert wie sonst - Verkäufe, Artikel, "
                    "Kassenbuch, Checklisten werden gespeichert -, aber "
                    "nur in dieser Kopie. An den echten Daten ändert "
                    "sich nichts.\n\n"
                    "Gedacht zum Zeigen und Ausprobieren: neue Helfer "
                    "einweisen, eine Rezeptkalkulation durchspielen, "
                    "einen Abend üben."
                ),
                "image": "einstellungen/02_demo.png",
            },
            {
                "heading": "Woran du den Demo-Modus erkennst",
                "text": (
                    "Die Akzentfarbe wechselt von Orange auf ein grelles "
                    "Grün, und oben in der Kopfzeile steht groß DEMO. "
                    "So ist auch von weitem klar, dass gerade nichts "
                    "Echtes gebucht wird."
                ),
                "image": "einstellungen/03_demo_aktiv.png",
            },
            {
                "heading": "Demo beenden",
                "text": (
                    "Über denselben Knopf verlässt du den Demo-Modus. "
                    "Die Kopie wird dabei verworfen: Alles, was im "
                    "Demo-Modus angelegt oder geändert wurde, ist weg, "
                    "und es gilt wieder der Stand von vor dem Start. "
                    "Auch das kommt vorher als Rückfrage.\n\n"
                    "Der Demo-Modus wird nie gespeichert - nach jedem "
                    "Programmstart läuft der normale Modus. Sollte das "
                    "Programm im Demo-Modus abstürzen, räumt der "
                    "nächste Start die Kopie weg."
                ),
            },
            {
                "heading": "Einstellungen bleiben erhalten",
                "text": (
                    "Farbmodus und Ausrichtung werden gespeichert und "
                    "beim nächsten Start automatisch wieder verwendet - "
                    "du musst sie also nur einmal einstellen."
                ),
            },
        ],
    },

]
