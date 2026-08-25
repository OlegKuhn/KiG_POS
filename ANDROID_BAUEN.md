# KiG POS als Android-App bauen

Das Projekt ist vollständig vorbereitet: `main.py` als Startdatei,
`buildozer.spec` mit allen Einstellungen, App-Symbol und Startbild
liegen bereit.

**Was noch fehlt, ist der eigentliche Bauvorgang.** Buildozer, das
Werkzeug dafür, läuft ausschließlich unter Linux — auf diesem Rechner
gibt es weder WSL noch Docker noch Java. Es gibt zwei Wege, beide unten
beschrieben.

---

## Weg 1: Bei GitHub bauen lassen (empfohlen)

Nichts zu installieren: **Git ist auf deinem Rechner schon vorhanden**
(Version 2.55, samt Anmeldehelfer). Der Bau läuft auf einem
Linux-Rechner bei GitHub, du lädst die fertige APK herunter. Der Ablauf
dafür liegt schon im Projekt (`.github/workflows/android.yml`).

### 1. Einmalig: Wer bist du?

Git weiß noch nicht, unter welchem Namen es Änderungen einträgt. Einmal
festlegen (die Adresse sollte die deines GitHub-Kontos sein):

```bash
git config --global user.name "Oleg Kuhn"
```

```bash
git config --global user.email "oleg.kuhn@googlemail.com"
```

### 2. GitHub-Konto und Projekt anlegen

Auf [github.com](https://github.com) anmelden (oder Konto erstellen),
dann oben rechts **+** → **New repository**:

- **Repository name:** `KiG_POS`
- **Private** auswählen — die Kasse geht niemanden etwas an
- **NICHT** "Add a README" ankreuzen, das Projekt bringt alles mit
- **Create repository**

### 3. Projekt hochladen

Im Projektordner nacheinander ausführen. Beim letzten Befehl öffnet
sich ein Browserfenster zur Anmeldung bei GitHub — danach merkt sich
der Rechner die Anmeldung.

```bash
git init -b main
```

```bash
git add .
```

```bash
git commit -m "KiG POS mit Hochformat und Android-Paket"
```

```bash
git remote add origin https://github.com/DEINNAME/KiG_POS.git
```

```bash
git push -u origin main
```

`DEINNAME` durch deinen GitHub-Benutzernamen ersetzen — die fertige
Zeile steht nach dem Anlegen auch auf der GitHub-Seite.

Hochgeladen werden rund **3 MB in 129 Dateien**. Die virtuelle
Umgebung (119 MB), die Datenbank, Sicherungen, Protokolle und Ausgaben
bleiben dank `.gitignore` außen vor.

### 4. Bau starten

Im Projekt bei GitHub auf **Actions**. Beim ersten Besuch fragt GitHub,
ob Abläufe ausgeführt werden dürfen → bestätigen. Dann links
**Android-App bauen** → rechts **Run workflow** → grüner Knopf
**Run workflow**.

### 5. APK herunterladen

Nach 30–45 Minuten (erster Lauf) ist der Punkt grün. Den Lauf
anklicken, unten unter **Artifacts** liegt `KiG-POS-APK` — das ist eine
ZIP-Datei mit der `.apk` darin.

### Später etwas ändern

Nach jeder Änderung am Programm genügen drei Befehle, und GitHub baut
automatisch eine neue APK:

```bash
git add . && git commit -m "Was geändert wurde" && git push
```

---

## Weg 2: Auf diesem Rechner bauen (WSL)

Braucht rund 10 GB Platz und eine einmalige Einrichtung.

1. **WSL installieren** (PowerShell als Administrator), danach Neustart:

```powershell
wsl --install -d Ubuntu
```

2. **In Ubuntu die Werkzeuge einrichten:**

```bash
sudo apt update && sudo apt install -y git zip unzip openjdk-17-jdk python3-pip autoconf libtool pkg-config zlib1g-dev libncurses-dev libtinfo6 cmake libffi-dev libssl-dev
pip3 install --user buildozer cython==0.29.36
echo 'export PATH=$PATH:~/.local/bin' >> ~/.bashrc && source ~/.bashrc
```

3. **Bauen** (Projektordner liegt unter `/mnt/c/...`):

```bash
cd /mnt/c/Users/oleg_/PycharmProjects/KiG_POS
buildozer android debug
```

Wichtig: Der erste Lauf lädt Android-SDK und -NDK (mehrere GB) und
dauert 30–60 Minuten. Die fertige Datei liegt danach in `bin/`.

---

## Aufs Telefon bringen

Die `.apk` per USB, E-Mail oder Cloud aufs Telefon kopieren und
antippen. Android fragt einmalig nach der Erlaubnis, Apps aus
unbekannter Quelle zu installieren — das ist bei selbst gebauten Apps
normal.

---

## Der Signaturschlüssel — warum Updates jetzt die Daten behalten

Jede Android-App ist unterschrieben. Android lässt ein Update **nur
zu, wenn die neue Fassung denselben Schlüssel trägt** wie die
installierte; sonst gilt sie als fremde App. Man müsste die alte
deinstallieren — und mit ihr verschwindet die Datenbank.

Genau das passierte anfangs: Ohne festen Schlüssel erzeugte Gradle bei
jedem Bau einen neuen.

Seitdem liegt der Schlüssel im Projekt:

```
android/debug.keystore
```

Der Bauablauf kopiert ihn vor dem Übersetzen nach
`~/.android/debug.keystore` — dort sucht Gradle danach. **Danach prüft
er nach**, ob die fertige APK wirklich diesen Fingerabdruck trägt, und
bricht ab, wenn nicht:

```
35:34:42:AF:E7:E8:15:32:21:C4:FF:1E:4D:69:7B:FF:
DB:2E:AD:A4:9F:11:B9:6D:8E:7C:4C:0C:DD:1C:CA:06
```

Eine APK mit fremdem Schlüssel wäre schlimmer als keine: Sie ließe
sich installieren, und erst beim übernächsten Mal fiele auf, dass die
Kette gerissen ist.

**Was das bedeutet:** Der Schlüssel liegt offen im Projekt und trägt
die Standardwerte eines Debug-Schlüssels (Passwort `android`, Alias
`androiddebugkey`). Er ist also kein Geheimnis — wer das Projekt hat,
kann eine APK bauen, die sich über die installierte legt. Für eine
Vereins-App, die von Hand aufs Tablet kommt, ist das in Ordnung. Soll
KiG POS je in einen App-Store, braucht es einen echten
Veröffentlichungsschlüssel, der **nicht** ins Projekt gehört, sondern
in die GitHub-Secrets.

**Einmalig noch nötig:** Die erste Fassung mit festem Schlüssel kann
sich nicht über eine ältere legen — die trägt ja noch den zufälligen
Schlüssel von damals. Für diesen einen Wechsel also: Datenbank sichern,
alte App deinstallieren, neue installieren, Datenbank zurückspielen
(siehe unten). Ab dann genügt `adb install -r`.

---

## Was auf dem Telefon anders ist

| | Windows | Android |
|---|---|---|
| Datenbank | `AppData\Roaming\kigpos\kig.db` | privater App-Ordner, **startet leer** |
| Sicherungen | daneben im Ordner `backups` | ebenso, privat |
| Excel / CSV | Projektordner `exports\` | `Android/data/de.kigev.kigpos/files/exports/` |
| PDF-Export des Handbuchs | vorhanden | nicht verfügbar (siehe unten) |
| Ausrichtung | umschaltbar in den Einstellungen | ebenso; beim ersten Start passend zum Bildschirm vorbelegt |
| Zurück-Taste | – | zur Startseite, von dort Rückfrage vor dem Beenden |
| Bildschirm | – | bleibt an, solange die App läuft |

Die Datenbank wird **bewusst nicht** mitgeliefert: Beim ersten Start
legt die App eine leere an. Kategorien (Alkoholfrei, Alkohol, Cocktail,
Essen, Sonstiges, Zutat), Pfandarten und Grundeinstellungen entstehen
automatisch — Getränke, Rezepte und Events legst du auf dem Telefon neu
an.

Den Ordner mit den Ausgaben erreichst du am Telefon mit jedem
Dateimanager oder am PC über das USB-Kabel unter
`Android/data/de.kigev.kigpos/files/exports/`.

---

## Nach der Installation: kurze Probe

Auf dem Telefon laesst sich einiges erst wirklich pruefen. Diese Runde
dauert fuenf Minuten und deckt die typischen Stolperstellen ab:

1. **Startseite** - sechs Kacheln, zwei je Reihe, nichts abgeschnitten
2. **Artikel** - eine Kategorie und zwei Getraenke anlegen; die
   Bildschirmtastatur des Telefons darf die Eingabefelder nicht
   verdecken
3. **Kasse** - Artikel antippen, Menge aendern, bezahlen
4. **Zuruecktaste/Wischgeste** - fuehrt zur Startseite, dort kommt die
   Ruckfrage vor dem Beenden
5. **Statistik** - "Excel exportieren", danach die Datei unter
   `Android/data/de.kigev.kigpos/files/exports/excel/` suchen
6. **Einstellungen** - dunkler Modus, danach die Kasse erneut oeffnen

---

## Wichtig: die Daten liegen nur auf dem Telefon

Datenbank und Sicherungen liegen im **privaten App-Ordner**. Der ist vor
anderen Apps geschuetzt - wird aber beim **Deinstallieren restlos
geloescht**. Ein Zurueckholen gibt es dann nicht.

Fuer den Vereinsbetrieb heisst das: Nach jeder Veranstaltung in der
Statistik **"Excel exportieren"** druecken. Diese Datei landet im
Ordner `Android/data/...` auf dem gemeinsamen Speicher, ueberlebt eine
Deinstallation und laesst sich per USB-Kabel auf den Rechner ziehen.

Windows-Rechner und Telefon fuehren getrennte Datenbestaende - ein
Abgleich zwischen beiden findet nicht statt.

---

## Falls der Bau abbricht

**Protokoll holen:** Beim fehlgeschlagenen Lauf liegt unter
**Artifacts** das `Bauprotokoll` - darin steht die Ursache. Der Ablauf
sichert es auch dann, wenn der Bau scheitert.

**Bereits erledigt** (steht hier als Gedächtnisstütze, falls die Fehler
wiederkommen):

| Fehler im Protokoll | Ursache | Behoben durch |
|---|---|---|
| `LT_SYS_SYMBOL_USCORE` beim Rezept libffi | autoreconf fand die libtool-Makros nicht | `libltdl-dev`, `m4`, `ACLOCAL_PATH` im Ablauf |
| Python 3.14 wird gebaut, Kivy passt nicht | Buildozer nahm python-for-android vom Zweig `master` | `p4a.branch = v2024.01.21` + `android.ndk = 25b` |
| `incomplete definition of type 'struct _frame'` | Das p4a-Rezept lädt reportlab von 2019, unvereinbar mit Python 3.11 | reportlab aus `requirements` entfernt |

**Neue Fehler:** Meist hilft ein sauberer Neuanfang - im Ablauf die
Zahl im Cache-Schlüssel (`buildozer-2-`) erhöhen und pushen. Dann wird
alles neu gebaut statt aus dem Zwischenspeicher geholt.
