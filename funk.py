"""
=========================================================
KiG POS
=========================================================

Datei:
    funk.py

Beschreibung:
    Daten von Gerät zu Gerät - über das Netz.

    Warum nicht über Bluetooth oder Kabel: Beides reicht
    eine Datei weiter, ohne dass die beiden Programme
    miteinander sprechen. Die Gegenseite kann deshalb nicht
    gefragt werden, ob sie überhaupt etwas will, und das
    sendende Gerät erfährt nie, ob es angekommen ist.

    Hier reden sie miteinander:

        1. Das empfangende Gerät wartet (Empfaenger.start).
        2. Das sendende sucht - ein Ruf ins Netz, wer
           antwortet, steht auf der Liste.
        3. Es verbindet sich und meldet, wer es ist.
        4. Auf dem empfangenden Gerät erscheint die Frage
           "annehmen?". Erst wenn dort jemand zustimmt,
        5. wählt das sendende, WAS es schickt - und schickt.
        6. Zum Schluss meldet das empfangende zurück, was
           daraus geworden ist.

    Damit weiß jede Seite, woran sie ist. Nebenbei ist es
    hundertmal schneller als Bluetooth.

    Zwei Häfen, fest verdrahtet:

        8577  die Verbindung selbst (TCP)
        8578  der Ruf ins Netz (UDP)

    Findet der Ruf niemanden - manche Netze geben
    Rundrufe nicht weiter, und auf Android muss man sie
    eigens erlauben -, bleibt der Weg über die Adresse:
    Das wartende Gerät zeigt sie an, am anderen wird sie
    eingetippt.

Version:
    1.0.0
=========================================================
"""

import json
import socket
import threading

from pathlib import Path


PORT_VERBINDUNG = 8577
PORT_SUCHE = 8578

RUF = b"KIGPOS-SUCHE"

# Kleine Nachrichten gehen als eine Zeile JSON über die Leitung, damit
# Sender und Empfänger nicht über Längenangaben stolpern.
ENDE = b"\n"

# Wartezeiten in Sekunden. Grosszuegig genug fuer ein traeges
# E-Ink-Tablet, kurz genug, dass niemand vor einem haengenden
# Bildschirm sitzt.
WARTEN_VERBINDEN = 8
WARTEN_ANTWORT = 180
WARTEN_SUCHE = 2.5

# Mehr als das nimmt niemand an - eine Kassendatenbank ist ein paar
# Megabyte gross. Die Grenze schuetzt davor, dass ein Missverstaendnis
# den Speicher vollschreibt.
GROESSTE_DATEI = 200 * 1024 * 1024

BROCKEN = 64 * 1024


# =========================================================
# Hilfen
# =========================================================

def eigene_adresse():
    """Die IP-Adresse dieses Geräts im WLAN.

    Über eine Verbindung, die nie zustande kommt: Das Betriebssystem
    verrät dabei, über welche Karte es hinausginge - ohne ein einziges
    Paket zu senden. Zuverlässiger als der Weg über den eigenen Namen,
    der oft nur 127.0.0.1 liefert.
    """

    strippe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    try:
        strippe.connect(("8.8.8.8", 80))

        return strippe.getsockname()[0]

    except OSError:
        return "127.0.0.1"

    finally:
        strippe.close()


def _rundruf_erlauben():
    """Lässt Android Rundrufe durch - sonst kommt der Suchruf nie an.

    Android wirft Rundrufe und Multicast weg, bevor eine App sie
    sieht: Sie kosten Strom, und die wenigsten Apps brauchen sie. Wer
    sie will, muss eine Sperre setzen und sie hinterher wieder lösen.

    Liefert die Sperre oder None (auf dem Rechner gibt es nichts zu
    tun).
    """

    try:
        from jnius import autoclass

        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        Context = autoclass("android.content.Context")

        aktivitaet = PythonActivity.mActivity

        wlan = aktivitaet.getSystemService(Context.WIFI_SERVICE)

        sperre = wlan.createMulticastLock("kigpos")
        sperre.setReferenceCounted(True)
        sperre.acquire()

        return sperre

    except Exception:
        return None


def _rundruf_freigeben(sperre):

    try:
        if sperre is not None and sperre.isHeld():
            sperre.release()

    except Exception:
        pass


def _zeile_senden(verbindung, inhalt):

    daten = json.dumps(inhalt, ensure_ascii=False).encode("utf-8")

    verbindung.sendall(daten + ENDE)


def _zeile_lesen(verbindung, rest=b""):
    """Liest bis zum Zeilenende. Liefert (inhalt, uebriggebliebenes)."""

    puffer = rest

    while ENDE not in puffer:

        stueck = verbindung.recv(4096)

        if not stueck:
            raise ConnectionError("Die Verbindung wurde beendet.")

        puffer += stueck

    zeile, _trenner, uebrig = puffer.partition(ENDE)

    return json.loads(zeile.decode("utf-8")), uebrig


# =========================================================
# Das wartende Gerät
# =========================================================

class Empfaenger:
    """Wartet auf ein sendendes Gerät.

    Alles Netzwerkgeschehen läuft in einem eigenen Faden - die
    Oberfläche darf davon nichts merken. Die Rückmeldungen kommen
    deshalb als Rückrufe, und wer sie entgegennimmt, muss sie in
    seinen eigenen Takt zurückholen (in Kivy: Clock.schedule_once).
    """

    def __init__(self, name, kennung, zielordner):

        self.name = name
        self.kennung = kennung
        self.zielordner = Path(zielordner)

        self.laeuft = False

        self._faden = None
        self._horcher = None
        self._rufhorcher = None

        # Android laesst Rundrufe nur durch, solange sie gehalten wird.
        self._rundruf_sperre = None

        # Wird gesetzt, sobald jemand anklopft: Der Rückruf entscheidet
        # (True/False), ob angenommen wird.
        self._frage_beantworten = None

    # -----------------------------------------------------

    def start(self, on_anfrage, on_datei, on_fehler=None, on_stand=None):
        """Beginnt zu warten.

        on_anfrage(name, kennung, antworten)  jemand klopft an;
                                              antworten(True/False)
        on_datei(art, pfad)                   Datei ist da
        on_fehler(meldung)                    etwas ging schief
        on_stand(meldung)                     Zwischenstand
        """

        if self.laeuft:
            return

        self.laeuft = True

        self._faden = threading.Thread(
            target=self._warten,
            args=(on_anfrage, on_datei, on_fehler, on_stand),
            daemon=True,
        )
        self._faden.start()

    def stop(self):

        self.laeuft = False

        _rundruf_freigeben(self._rundruf_sperre)
        self._rundruf_sperre = None

        for buchse in (self._horcher, self._rufhorcher):

            try:
                if buchse is not None:
                    buchse.close()
            except OSError:
                pass

        self._horcher = None
        self._rufhorcher = None

    # -----------------------------------------------------

    def _warten(self, on_anfrage, on_datei, on_fehler, on_stand):

        def melden(rueckruf, *args):
            if callable(rueckruf):
                rueckruf(*args)

        try:
            self._horcher = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._horcher.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._horcher.bind(("", PORT_VERBINDUNG))
            self._horcher.listen(1)
            self._horcher.settimeout(1.0)

            # Auf Rufe antworten, solange gewartet wird.
            self._rufhorcher = socket.socket(
                socket.AF_INET, socket.SOCK_DGRAM
            )
            self._rufhorcher.setsockopt(
                socket.SOL_SOCKET, socket.SO_REUSEADDR, 1
            )
            self._rufhorcher.bind(("", PORT_SUCHE))
            self._rufhorcher.settimeout(1.0)

            self._rundruf_sperre = _rundruf_erlauben()

            threading.Thread(target=self._rufe_beantworten, daemon=True).start()

        except OSError as fehler:
            self.laeuft = False
            melden(on_fehler, f"Warten nicht möglich: {fehler}")
            return

        while self.laeuft:

            try:
                verbindung, _absender = self._horcher.accept()

            except socket.timeout:
                continue

            except OSError:
                break

            try:
                self._bedienen(
                    verbindung, on_anfrage, on_datei, on_fehler, on_stand
                )

            except Exception as fehler:
                melden(on_fehler, f"Übertragung abgebrochen: {fehler}")

            finally:
                try:
                    verbindung.close()
                except OSError:
                    pass

    def _rufe_beantworten(self):
        """Antwortet auf den Ruf eines suchenden Geräts."""

        while self.laeuft and self._rufhorcher is not None:

            try:
                daten, absender = self._rufhorcher.recvfrom(1024)

            except socket.timeout:
                continue

            except OSError:
                break

            if not daten.startswith(RUF):
                continue

            antwort = json.dumps({
                "name": self.name,
                "kennung": self.kennung,
                "port": PORT_VERBINDUNG,
            }, ensure_ascii=False).encode("utf-8")

            try:
                self._rufhorcher.sendto(antwort, absender)
            except OSError:
                pass

    def _bedienen(self, verbindung, on_anfrage, on_datei, on_fehler, on_stand):

        verbindung.settimeout(WARTEN_ANTWORT)

        anfrage, rest = _zeile_lesen(verbindung)

        if anfrage.get("schritt") != "anfrage":
            _zeile_senden(verbindung, {"schritt": "antwort", "ok": False})
            return

        name = anfrage.get("name", "Unbekannt")
        kennung = anfrage.get("kennung", "")

        # Die Frage stellt die Oberfläche. Bis sie beantwortet ist,
        # bleibt dieser Faden stehen - die Gegenseite wartet ja auch.
        entscheidung = threading.Event()
        ergebnis = {"ok": False}

        def antworten(ja):
            ergebnis["ok"] = bool(ja)
            entscheidung.set()

        if callable(on_anfrage):
            on_anfrage(name, kennung, antworten)
        else:
            antworten(True)

        entscheidung.wait(WARTEN_ANTWORT)

        _zeile_senden(
            verbindung,
            {
                "schritt": "antwort",
                "ok": ergebnis["ok"],
                "name": self.name,
                "kennung": self.kennung,
            },
        )

        if not ergebnis["ok"]:
            return

        if callable(on_stand):
            on_stand(f"{name} sendet ...")

        kopf, rest = _zeile_lesen(verbindung, rest)

        if kopf.get("schritt") != "datei":
            return

        art = kopf.get("art", "datenbank")
        dateiname = Path(kopf.get("name", "empfangen.kigdb")).name
        groesse = int(kopf.get("groesse", 0))

        if groesse <= 0 or groesse > GROESSTE_DATEI:
            raise ValueError(f"Unglaubwürdige Größe: {groesse} Bytes")

        self.zielordner.mkdir(parents=True, exist_ok=True)

        ziel = self.zielordner / dateiname

        offen = 0

        with open(ziel, "wb") as senke:

            if rest:
                senke.write(rest[:groesse])
                offen = len(rest[:groesse])

            while offen < groesse:

                stueck = verbindung.recv(min(BROCKEN, groesse - offen))

                if not stueck:
                    raise ConnectionError(
                        f"Abgebrochen nach {offen} von {groesse} Bytes."
                    )

                senke.write(stueck)
                offen += len(stueck)

        meldung = "Empfangen."

        if callable(on_datei):
            meldung = on_datei(art, ziel) or meldung

        _zeile_senden(
            verbindung, {"schritt": "fertig", "meldung": meldung}
        )


# =========================================================
# Das sendende Gerät
# =========================================================

def suchen(dauer=WARTEN_SUCHE):
    """Ruft ins Netz und sammelt, wer antwortet.

    Liefert eine Liste von {"name", "kennung", "adresse", "port"}.
    """

    gefunden = {}

    rufer = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    rufer.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    rufer.settimeout(0.4)

    try:
        for ziel in ("255.255.255.255", "127.0.0.1"):

            try:
                rufer.sendto(RUF, (ziel, PORT_SUCHE))
            except OSError:
                continue

        ende = _jetzt() + dauer

        while _jetzt() < ende:

            try:
                daten, absender = rufer.recvfrom(1024)

            except socket.timeout:
                continue

            except OSError:
                break

            try:
                antwort = json.loads(daten.decode("utf-8"))

            except (ValueError, UnicodeDecodeError):
                continue

            if "name" not in antwort:
                continue

            antwort["adresse"] = absender[0]
            antwort.setdefault("port", PORT_VERBINDUNG)

            gefunden[antwort.get("kennung") or absender[0]] = antwort

    finally:
        rufer.close()

    return list(gefunden.values())


def _jetzt():

    import time

    return time.monotonic()


def anfragen(adresse, port, name, kennung):
    """Klopft an und wartet auf die Zusage.

    Liefert (verbindung, antwort). Die Verbindung bleibt offen - über
    sie geht danach die Datei (siehe datei_senden).
    """

    verbindung = socket.create_connection(
        (adresse, port), timeout=WARTEN_VERBINDEN
    )

    verbindung.settimeout(WARTEN_ANTWORT)

    _zeile_senden(
        verbindung,
        {"schritt": "anfrage", "name": name, "kennung": kennung},
    )

    antwort, _rest = _zeile_lesen(verbindung)

    return verbindung, antwort


def datei_senden(verbindung, pfad, art):
    """Schickt die Datei und wartet auf die Rückmeldung."""

    pfad = Path(pfad)

    groesse = pfad.stat().st_size

    _zeile_senden(
        verbindung,
        {
            "schritt": "datei",
            "art": art,
            "name": pfad.name,
            "groesse": groesse,
        },
    )

    with open(pfad, "rb") as quelle:

        while True:

            brocken = quelle.read(BROCKEN)

            if not brocken:
                break

            verbindung.sendall(brocken)

    rueckmeldung, _rest = _zeile_lesen(verbindung)

    return rueckmeldung.get("meldung", "Übertragen.")
