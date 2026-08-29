; =========================================================
; KiG POS - Bauanleitung fuer das Installationsprogramm
; =========================================================
;
; Aufruf (nachdem PyInstaller gelaufen ist):
;     "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" KiG_POS_Setup.iss
;
; Ergebnis:
;     installer\KiG POS Setup 0.1.0.exe
;
; Diese eine Datei laesst sich auf jeden Rechner mitnehmen.
;
; Installiert wird PRO BENUTZER nach
;     %LOCALAPPDATA%\Programs\KiG POS
; und zwar aus einem handfesten Grund: Das Programm legt seine
; Datenbank NEBEN die exe (siehe storage.py:data_dir). In
; "C:\Program Files" darf ein normaler Benutzer nicht schreiben -
; die Kasse kaeme dort beim ersten Start nicht einmal hoch. Der
; Ordner unter LocalAppData gehoert dem Benutzer, deshalb braucht
; die Installation auch keine Administratorrechte und laeuft auf
; jedem Rechner durch.
;
; Was der Deinstallierer NICHT anfasst: den Ordner "daten" mit
; Datenbank und Sicherungen und den Ordner "exports". Inno Setup
; entfernt nur, was es selbst hingelegt hat - eine Deinstallation
; kostet also keine Buchungen.

#define AppName        "KiG POS"
#define AppVersion     "0.1.0"
#define AppPublisher   "KiG e.V."
#define AppExeName     "KiG POS.exe"
#define QuellOrdner    "dist\KiG POS"


[Setup]
; Bleibt ueber alle Fassungen gleich - daran erkennt Windows eine
; vorhandene Installation und ersetzt sie, statt sie zu verdoppeln.
AppId={{8B3F1C2A-6D4E-4A91-9C7B-2E5F0A1D3B84}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher={#AppPublisher}
VersionInfoVersion={#AppVersion}

DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes

; Ohne Administratorrechte - siehe Kopf dieser Datei.
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

ArchitecturesAllowed=x64compatible

OutputDir=installer
OutputBaseFilename={#AppName} Setup {#AppVersion}
SetupIconFile=assets\icons\kig_pos.ico
UninstallDisplayIcon={app}\{#AppExeName}
UninstallDisplayName={#AppName}

Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern

; Laeuft die Kasse noch, wuerde die Installation an der belegten exe
; scheitern. Inno bietet dann an, sie zu schliessen.
CloseApplications=yes


[Languages]
Name: "deutsch"; MessagesFile: "compiler:Languages\German.isl"


[Tasks]
Name: "desktopicon"; Description: "Verknüpfung auf dem Desktop anlegen"; GroupDescription: "Zusätzliche Verknüpfungen:"


[Files]
; Der ganze Programmordner. Ausgeschlossen sind die Ordner, die erst
; im Betrieb entstehen: Eine Installationsdatei, die eine fremde
; Datenbank mitbringt, waere ein Unfall - jeder Rechner faengt bei
; null an.
Source: "{#QuellOrdner}\*"; DestDir: "{app}"; \
    Excludes: "daten\*,daten,exports\*,exports,logs\*,logs"; \
    Flags: ignoreversion recursesubdirs createallsubdirs


[Icons]
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\{#AppExeName}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon


[Run]
Filename: "{app}\{#AppExeName}"; Description: "{#AppName} jetzt starten"; \
    Flags: nowait postinstall skipifsilent
