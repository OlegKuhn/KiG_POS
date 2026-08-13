Attribute VB_Name = "KiG_POS"
' =====================================================================
' KiG POS - Excel-Kasse
' =====================================================================
'
' Bildet die Kernlogik von KiG POS in Excel nach:
'
'   - Verkauf buchen (zieht Bestand ab, protokolliert den Verkauf)
'   - Mix-/Rezeptartikel ziehen ihre Zutaten ab, nicht sich selbst
'   - Flaschen werden intern in Millilitern gefuehrt
'   - Wareneingang buchen (Bestellmenge -> Bestand)
'   - Bestandskorrektur mit Grund und Bearbeiter (Historie)
'   - Einkaufsliste erzeugen
'   - Verfuegbarkeit und Rezeptkosten neu berechnen
'
' Import: Alt+F11 -> Datei -> Datei importieren -> diese .bas waehlen.
' Anschliessend die Mappe als .xlsm speichern.
'
' =====================================================================

Option Explicit

' --- Blattnamen -------------------------------------------------------
Private Const BL_ARTIKEL As String = "Artikel"
Private Const BL_REZEPTE As String = "Rezepte"
Private Const BL_KASSE As String = "Kasse"
Private Const BL_VERKAEUFE As String = "Verkäufe"
Private Const BL_HISTORIE As String = "Bestandshistorie"
Private Const BL_EINKAUF As String = "Einkaufsliste"

' --- Spalten im Blatt "Artikel" ---------------------------------------
Private Const SP_NR As Long = 1
Private Const SP_NAME As Long = 2
Private Const SP_KATEGORIE As Long = 3
Private Const SP_EINHEIT As Long = 4
Private Const SP_VK As Long = 5
Private Const SP_EK As Long = 6
Private Const SP_TYP As Long = 7
Private Const SP_KASSE As Long = 8
Private Const SP_AKTIV As Long = 9
Private Const SP_FLASCHE As Long = 10
Private Const SP_BESTAND As Long = 11
Private Const SP_BESTELLMENGE As Long = 12
Private Const SP_EK_BASIS As Long = 13
Private Const SP_VERFUEGBAR As Long = 14
Private Const SP_REZEPTKOSTEN As Long = 15

' --- Spalten im Blatt "Rezepte" ---------------------------------------
Private Const RZ_REZEPT As Long = 1
Private Const RZ_ZUTAT As Long = 2
Private Const RZ_MENGE As Long = 3
Private Const RZ_EINHEIT As Long = 4

' --- Kasse ------------------------------------------------------------
Private Const KA_EVENT_ZELLE As String = "B2"
Private Const KA_ERSTE_ZEILE As Long = 5
Private Const KA_LETZTE_ZEILE As Long = 24

Private Const ERSTE_DATENZEILE As Long = 2


' =====================================================================
' Verkauf buchen
' =====================================================================

Public Sub VerkaufBuchen()

    Dim wsKasse As Worksheet, wsArtikel As Worksheet, wsVerkauf As Worksheet
    Dim zeile As Long, artikelZeile As Long
    Dim artikelName As String, event_ As String
    Dim menge As Double, verkaufspreis As Double, einkaufspreis As Double
    Dim positionen As Long, summe As Double
    Dim beleg As Long, zielZeile As Long
    Dim jetzt As Date

    Set wsKasse = ThisWorkbook.Worksheets(BL_KASSE)
    Set wsArtikel = ThisWorkbook.Worksheets(BL_ARTIKEL)
    Set wsVerkauf = ThisWorkbook.Worksheets(BL_VERKAEUFE)

    ' --- Erst pruefen, dann buchen: sonst waere der Warenkorb bei
    '     einem Fehler in der Mitte nur halb verarbeitet.
    For zeile = KA_ERSTE_ZEILE To KA_LETZTE_ZEILE

        artikelName = Trim(CStr(wsKasse.Cells(zeile, 1).Value))
        If Len(artikelName) > 0 Then

            menge = NullWennLeer(wsKasse.Cells(zeile, 2).Value)

            If menge <= 0 Then
                MsgBox "Zeile " & zeile & ": Bitte eine Menge groesser 0 eintragen.", _
                       vbExclamation, "Verkauf nicht gebucht"
                Exit Sub
            End If

            If ArtikelZeileFinden(artikelName) = 0 Then
                MsgBox "Zeile " & zeile & ": Artikel '" & artikelName & _
                       "' steht nicht im Artikelstamm.", _
                       vbExclamation, "Verkauf nicht gebucht"
                Exit Sub
            End If

            positionen = positionen + 1
        End If
    Next zeile

    If positionen = 0 Then
        MsgBox "Der Warenkorb ist leer.", vbInformation, "Nichts zu buchen"
        Exit Sub
    End If

    ' --- Buchen
    ' Fehlerbehandlung, damit ScreenUpdating auch bei einem
    ' unerwarteten Fehler wieder eingeschaltet wird - sonst wirkt
    ' Excel eingefroren.
    On Error GoTo Fehler
    Application.ScreenUpdating = False

    BestandNeuBerechnenStill
    beleg = NaechsteBelegnummer()
    event_ = Trim(CStr(wsKasse.Range(KA_EVENT_ZELLE).Value))
    jetzt = Now

    For zeile = KA_ERSTE_ZEILE To KA_LETZTE_ZEILE

        artikelName = Trim(CStr(wsKasse.Cells(zeile, 1).Value))
        If Len(artikelName) = 0 Then GoTo NaechsteZeile

        menge = NullWennLeer(wsKasse.Cells(zeile, 2).Value)
        artikelZeile = ArtikelZeileFinden(artikelName)

        verkaufspreis = NullWennLeer(wsArtikel.Cells(artikelZeile, SP_VK).Value)

        If IstMixArtikel(artikelZeile) Then
            einkaufspreis = Rezeptkosten(artikelName)
            ZutatenAbziehen artikelName, menge
        Else
            einkaufspreis = NullWennLeer(wsArtikel.Cells(artikelZeile, SP_EK).Value)
            wsArtikel.Cells(artikelZeile, SP_BESTAND).Value = _
                NullWennLeer(wsArtikel.Cells(artikelZeile, SP_BESTAND).Value) - menge
        End If

        zielZeile = wsVerkauf.Cells(wsVerkauf.Rows.Count, 1).End(xlUp).Row + 1
        If zielZeile < ERSTE_DATENZEILE Then zielZeile = ERSTE_DATENZEILE

        With wsVerkauf
            .Cells(zielZeile, 1).Value = Int(jetzt)
            .Cells(zielZeile, 1).NumberFormat = "TT.MM.JJJJ"
            .Cells(zielZeile, 2).Value = jetzt - Int(jetzt)
            .Cells(zielZeile, 2).NumberFormat = "hh:mm"
            .Cells(zielZeile, 3).Value = beleg
            .Cells(zielZeile, 4).Value = event_
            .Cells(zielZeile, 5).Value = wsArtikel.Cells(artikelZeile, SP_KATEGORIE).Value
            .Cells(zielZeile, 6).Value = artikelName
            .Cells(zielZeile, 7).Value = menge
            .Cells(zielZeile, 8).Value = verkaufspreis
            .Cells(zielZeile, 9).Value = einkaufspreis
            .Cells(zielZeile, 10).Value = menge * verkaufspreis
            .Cells(zielZeile, 11).Value = menge * (verkaufspreis - einkaufspreis)
            .Range(.Cells(zielZeile, 8), .Cells(zielZeile, 11)).NumberFormat = "#,##0.00 ""EUR"""
        End With

        summe = summe + menge * verkaufspreis

NaechsteZeile:
    Next zeile

    WarenkorbLeerenStill
    BestandNeuBerechnenStill

    Application.ScreenUpdating = True

    MsgBox "Verkauf gebucht." & vbCrLf & vbCrLf & _
           "Beleg-Nr.: " & beleg & vbCrLf & _
           "Positionen: " & positionen & vbCrLf & _
           "Summe: " & Format(summe, "#,##0.00") & " EUR", _
           vbInformation, "Verkauf abgeschlossen"

    Exit Sub

Fehler:
    Application.ScreenUpdating = True
    MsgBox "Beim Buchen ist ein Fehler aufgetreten:" & vbCrLf & vbCrLf & _
           Err.Description & vbCrLf & vbCrLf & _
           "Bitte Best" & Chr(228) & "nde und Verk" & Chr(228) & "ufe pr" & Chr(252) & "fen.", _
           vbCritical, "Verkauf unvollst" & Chr(228) & "ndig"

End Sub


' Zieht die Zutaten eines Rezepts vom Bestand ab.
' Zutaten ohne eigenen Artikel (z. B. "Minze") werden uebersprungen -
' sie werden bewusst nicht lagergefuehrt.
Private Sub ZutatenAbziehen(ByVal rezept As String, ByVal anzahl As Double)

    Dim wsRezepte As Worksheet, wsArtikel As Worksheet
    Dim zeile As Long, letzte As Long, zutatZeile As Long
    Dim mengeBasis As Double

    Set wsRezepte = ThisWorkbook.Worksheets(BL_REZEPTE)
    Set wsArtikel = ThisWorkbook.Worksheets(BL_ARTIKEL)

    letzte = wsRezepte.Cells(wsRezepte.Rows.Count, RZ_REZEPT).End(xlUp).Row

    For zeile = ERSTE_DATENZEILE To letzte
        If StrComp(Trim(CStr(wsRezepte.Cells(zeile, RZ_REZEPT).Value)), rezept, vbTextCompare) = 0 Then

            zutatZeile = ArtikelZeileFinden(CStr(wsRezepte.Cells(zeile, RZ_ZUTAT).Value))

            If zutatZeile > 0 Then
                mengeBasis = InBasiseinheit( _
                    NullWennLeer(wsRezepte.Cells(zeile, RZ_MENGE).Value), _
                    CStr(wsRezepte.Cells(zeile, RZ_EINHEIT).Value))

                wsArtikel.Cells(zutatZeile, SP_BESTAND).Value = _
                    NullWennLeer(wsArtikel.Cells(zutatZeile, SP_BESTAND).Value) - mengeBasis * anzahl
            End If
        End If
    Next zeile

End Sub


' =====================================================================
' Warenkorb
' =====================================================================

Public Sub WarenkorbLeeren()
    WarenkorbLeerenStill
    MsgBox "Warenkorb geleert.", vbInformation, "Kasse"
End Sub


Private Sub WarenkorbLeerenStill()

    Dim ws As Worksheet
    Set ws = ThisWorkbook.Worksheets(BL_KASSE)

    ws.Range(ws.Cells(KA_ERSTE_ZEILE, 1), ws.Cells(KA_LETZTE_ZEILE, 2)).ClearContents

End Sub


' =====================================================================
' Wareneingang
' =====================================================================

Public Sub WareneingangBuchen()

    Dim wsArtikel As Worksheet
    Dim zeile As Long, letzte As Long, gebucht As Long
    Dim menge As Double, zugang As Double, flaschengroesse As Double
    Dim antwort As String

    Set wsArtikel = ThisWorkbook.Worksheets(BL_ARTIKEL)
    letzte = LetzteArtikelZeile()

    For zeile = ERSTE_DATENZEILE To letzte

        menge = NullWennLeer(wsArtikel.Cells(zeile, SP_BESTELLMENGE).Value)
        If menge <= 0 Then GoTo NaechsterArtikel

        If IstFlasche(zeile) Then
            ' Eine Flasche hat keinen festen ml-Wert - deshalb hier
            ' nachfragen und in Milliliter umrechnen.
            flaschengroesse = NullWennLeer(wsArtikel.Cells(zeile, SP_FLASCHE).Value)
            If flaschengroesse <= 0 Then flaschengroesse = 700

            antwort = InputBox( _
                "Wie viele Milliliter hat eine Flasche '" & _
                wsArtikel.Cells(zeile, SP_NAME).Value & "'?", _
                "Wareneingang - Flaschengroesse", CStr(flaschengroesse))

            If Len(Trim(antwort)) = 0 Then GoTo NaechsterArtikel
            If Not IsNumeric(antwort) Then GoTo NaechsterArtikel

            flaschengroesse = CDbl(antwort)
            If flaschengroesse <= 0 Then GoTo NaechsterArtikel

            wsArtikel.Cells(zeile, SP_FLASCHE).Value = flaschengroesse
            zugang = menge * flaschengroesse
        Else
            zugang = menge
        End If

        HistorieSchreiben _
            CStr(wsArtikel.Cells(zeile, SP_NAME).Value), _
            NullWennLeer(wsArtikel.Cells(zeile, SP_BESTAND).Value), _
            NullWennLeer(wsArtikel.Cells(zeile, SP_BESTAND).Value) + zugang, _
            "Wareneingang", "Einkauf"

        wsArtikel.Cells(zeile, SP_BESTAND).Value = _
            NullWennLeer(wsArtikel.Cells(zeile, SP_BESTAND).Value) + zugang
        wsArtikel.Cells(zeile, SP_BESTELLMENGE).ClearContents

        gebucht = gebucht + 1

NaechsterArtikel:
    Next zeile

    BestandNeuBerechnenStill

    If gebucht = 0 Then
        MsgBox "Es ist keine Bestellmenge eingetragen.", vbInformation, "Wareneingang"
    Else
        MsgBox gebucht & " Artikel wurden dem Bestand gutgeschrieben.", _
               vbInformation, "Wareneingang gebucht"
    End If

End Sub


' =====================================================================
' Bestandskorrektur
' =====================================================================

Public Sub BestandKorrigieren()

    Dim wsArtikel As Worksheet
    Dim artikelName As String, grund As String, bearbeiter As String
    Dim eingabe As String
    Dim zeile As Long
    Dim alt As Double, neu As Double

    Set wsArtikel = ThisWorkbook.Worksheets(BL_ARTIKEL)

    artikelName = Trim(InputBox("Name des Artikels:", "Bestandskorrektur"))
    If Len(artikelName) = 0 Then Exit Sub

    zeile = ArtikelZeileFinden(artikelName)
    If zeile = 0 Then
        MsgBox "Artikel '" & artikelName & "' nicht gefunden.", _
               vbExclamation, "Bestandskorrektur"
        Exit Sub
    End If

    alt = NullWennLeer(wsArtikel.Cells(zeile, SP_BESTAND).Value)

    eingabe = InputBox("Neuer Bestand" & _
        IIf(IstFlasche(zeile), " (in Millilitern)", "") & _
        " fuer '" & artikelName & "':" & vbCrLf & vbCrLf & _
        "Aktueller Bestand: " & alt, "Bestandskorrektur", CStr(alt))

    If Len(Trim(eingabe)) = 0 Then Exit Sub
    If Not IsNumeric(eingabe) Then
        MsgBox "Bitte eine Zahl eingeben.", vbExclamation, "Bestandskorrektur"
        Exit Sub
    End If
    neu = CDbl(eingabe)

    grund = Trim(InputBox("Grund der Korrektur (z. B. Inventur, Bruch):", _
                          "Bestandskorrektur"))
    If Len(grund) = 0 Then
        MsgBox "Ohne Grund wird nicht korrigiert.", vbExclamation, "Bestandskorrektur"
        Exit Sub
    End If

    bearbeiter = Trim(InputBox("Bearbeitet von:", "Bestandskorrektur"))
    If Len(bearbeiter) = 0 Then
        MsgBox "Ohne Namen wird nicht korrigiert.", vbExclamation, "Bestandskorrektur"
        Exit Sub
    End If

    HistorieSchreiben artikelName, alt, neu, grund, bearbeiter
    wsArtikel.Cells(zeile, SP_BESTAND).Value = neu

    BestandNeuBerechnenStill

    MsgBox "Bestand von '" & artikelName & "' geaendert: " & _
           alt & " -> " & neu, vbInformation, "Bestandskorrektur"

End Sub


Private Sub HistorieSchreiben(ByVal artikelName As String, _
                              ByVal alt As Double, ByVal neu As Double, _
                              ByVal grund As String, ByVal bearbeiter As String)

    Dim ws As Worksheet
    Dim zeile As Long

    Set ws = ThisWorkbook.Worksheets(BL_HISTORIE)

    zeile = ws.Cells(ws.Rows.Count, 1).End(xlUp).Row + 1
    If zeile < ERSTE_DATENZEILE Then zeile = ERSTE_DATENZEILE

    ws.Cells(zeile, 1).Value = Now
    ws.Cells(zeile, 1).NumberFormat = "TT.MM.JJJJ hh:mm"
    ws.Cells(zeile, 2).Value = artikelName
    ws.Cells(zeile, 3).Value = alt
    ws.Cells(zeile, 4).Value = neu
    ws.Cells(zeile, 5).Value = grund
    ws.Cells(zeile, 6).Value = bearbeiter

End Sub


' =====================================================================
' Einkaufsliste
' =====================================================================

Public Sub EinkaufslisteErzeugen()

    Dim wsArtikel As Worksheet, wsListe As Worksheet
    Dim zeile As Long, letzte As Long, ziel As Long
    Dim menge As Double

    Set wsArtikel = ThisWorkbook.Worksheets(BL_ARTIKEL)
    Set wsListe = ThisWorkbook.Worksheets(BL_EINKAUF)

    letzte = wsListe.Cells(wsListe.Rows.Count, 1).End(xlUp).Row
    If letzte >= ERSTE_DATENZEILE Then
        wsListe.Range(wsListe.Cells(ERSTE_DATENZEILE, 1), _
                      wsListe.Cells(letzte, 4)).ClearContents
    End If

    ziel = ERSTE_DATENZEILE
    letzte = LetzteArtikelZeile()

    For zeile = ERSTE_DATENZEILE To letzte
        menge = NullWennLeer(wsArtikel.Cells(zeile, SP_BESTELLMENGE).Value)
        If menge > 0 Then
            wsListe.Cells(ziel, 1).Value = wsArtikel.Cells(zeile, SP_KATEGORIE).Value
            wsListe.Cells(ziel, 2).Value = wsArtikel.Cells(zeile, SP_NAME).Value
            wsListe.Cells(ziel, 3).Value = menge
            wsListe.Cells(ziel, 4).Value = wsArtikel.Cells(zeile, SP_EINHEIT).Value
            ziel = ziel + 1
        End If
    Next zeile

    wsListe.Activate

    If ziel = ERSTE_DATENZEILE Then
        MsgBox "Es ist keine Bestellmenge eingetragen.", vbInformation, "Einkaufsliste"
    Else
        MsgBox (ziel - ERSTE_DATENZEILE) & " Artikel in die Einkaufsliste uebernommen.", _
               vbInformation, "Einkaufsliste"
    End If

End Sub


' =====================================================================
' Verfuegbarkeit und Rezeptkosten
' =====================================================================

Public Sub BestandNeuBerechnen()
    BestandNeuBerechnenStill
    MsgBox "Verfuegbarkeit und Rezeptkosten wurden neu berechnet.", _
           vbInformation, "Aktualisiert"
End Sub


Private Sub BestandNeuBerechnenStill()

    Dim wsArtikel As Worksheet
    Dim zeile As Long, letzte As Long
    Dim name As String

    Set wsArtikel = ThisWorkbook.Worksheets(BL_ARTIKEL)
    letzte = LetzteArtikelZeile()

    For zeile = ERSTE_DATENZEILE To letzte

        name = Trim(CStr(wsArtikel.Cells(zeile, SP_NAME).Value))
        If Len(name) = 0 Then GoTo Weiter

        If IstMixArtikel(zeile) Then
            wsArtikel.Cells(zeile, SP_VERFUEGBAR).Value = Verfuegbar(name)
            wsArtikel.Cells(zeile, SP_REZEPTKOSTEN).Value = Rezeptkosten(name)
            wsArtikel.Cells(zeile, SP_REZEPTKOSTEN).NumberFormat = "#,##0.00 ""EUR"""
        Else
            ' Einzelartikel fuehren ihren Bestand selbst - hier gibt es
            ' nichts hochzurechnen.
            wsArtikel.Cells(zeile, SP_VERFUEGBAR).ClearContents
            wsArtikel.Cells(zeile, SP_REZEPTKOSTEN).ClearContents
        End If
Weiter:
    Next zeile

End Sub


' Wie oft laesst sich das Rezept mit dem aktuellen Zutatenbestand noch
' verkaufen? Begrenzend ist die knappste Zutat.
Public Function Verfuegbar(ByVal rezept As String) As Long

    Dim wsRezepte As Worksheet, wsArtikel As Worksheet
    Dim zeile As Long, letzte As Long, zutatZeile As Long
    Dim mengeBasis As Double, bestand As Double
    Dim moeglich As Long, kleinste As Long
    Dim gefunden As Boolean

    Set wsRezepte = ThisWorkbook.Worksheets(BL_REZEPTE)
    Set wsArtikel = ThisWorkbook.Worksheets(BL_ARTIKEL)

    letzte = wsRezepte.Cells(wsRezepte.Rows.Count, RZ_REZEPT).End(xlUp).Row

    For zeile = ERSTE_DATENZEILE To letzte
        If StrComp(Trim(CStr(wsRezepte.Cells(zeile, RZ_REZEPT).Value)), rezept, vbTextCompare) = 0 Then

            zutatZeile = ArtikelZeileFinden(CStr(wsRezepte.Cells(zeile, RZ_ZUTAT).Value))

            ' Zutaten ohne eigenen Artikel (Minze, Limette, ...) fuehren
            ' keinen Bestand und begrenzen daher auch nichts.
            If zutatZeile > 0 Then

                mengeBasis = InBasiseinheit( _
                    NullWennLeer(wsRezepte.Cells(zeile, RZ_MENGE).Value), _
                    CStr(wsRezepte.Cells(zeile, RZ_EINHEIT).Value))

                If mengeBasis > 0 Then
                    bestand = NullWennLeer(wsArtikel.Cells(zutatZeile, SP_BESTAND).Value)
                    moeglich = Int(bestand / mengeBasis)
                    If moeglich < 0 Then moeglich = 0

                    If Not gefunden Then
                        kleinste = moeglich
                        gefunden = True
                    ElseIf moeglich < kleinste Then
                        kleinste = moeglich
                    End If
                End If
            End If
        End If
    Next zeile

    If gefunden Then Verfuegbar = kleinste Else Verfuegbar = 0

End Function


' Einkaufspreis einer Portion, hochgerechnet aus den Zutaten.
Public Function Rezeptkosten(ByVal rezept As String) As Double

    Dim wsRezepte As Worksheet, wsArtikel As Worksheet
    Dim zeile As Long, letzte As Long, zutatZeile As Long
    Dim mengeBasis As Double, summe As Double

    Set wsRezepte = ThisWorkbook.Worksheets(BL_REZEPTE)
    Set wsArtikel = ThisWorkbook.Worksheets(BL_ARTIKEL)

    letzte = wsRezepte.Cells(wsRezepte.Rows.Count, RZ_REZEPT).End(xlUp).Row

    For zeile = ERSTE_DATENZEILE To letzte
        If StrComp(Trim(CStr(wsRezepte.Cells(zeile, RZ_REZEPT).Value)), rezept, vbTextCompare) = 0 Then

            zutatZeile = ArtikelZeileFinden(CStr(wsRezepte.Cells(zeile, RZ_ZUTAT).Value))

            If zutatZeile > 0 Then
                mengeBasis = InBasiseinheit( _
                    NullWennLeer(wsRezepte.Cells(zeile, RZ_MENGE).Value), _
                    CStr(wsRezepte.Cells(zeile, RZ_EINHEIT).Value))

                summe = summe + mengeBasis * EinkaufspreisJeBasiseinheit(zutatZeile)
            End If
        End If
    Next zeile

    Rezeptkosten = summe

End Function


' Einkaufspreis je Basiseinheit (ml / g / Stueck).
' Bei einer Flasche gilt der Einkaufspreis fuer EINE Flasche - der
' Bestand wird aber in Millilitern gefuehrt, also umrechnen.
Private Function EinkaufspreisJeBasiseinheit(ByVal artikelZeile As Long) As Double

    Dim wsArtikel As Worksheet
    Dim ek As Double, flaschengroesse As Double

    Set wsArtikel = ThisWorkbook.Worksheets(BL_ARTIKEL)

    ek = NullWennLeer(wsArtikel.Cells(artikelZeile, SP_EK).Value)

    If IstFlasche(artikelZeile) Then
        flaschengroesse = NullWennLeer(wsArtikel.Cells(artikelZeile, SP_FLASCHE).Value)
        If flaschengroesse > 0 Then
            EinkaufspreisJeBasiseinheit = ek / flaschengroesse
        Else
            EinkaufspreisJeBasiseinheit = 0
        End If
    Else
        EinkaufspreisJeBasiseinheit = ek
    End If

End Function


' =====================================================================
' Hilfsfunktionen
' =====================================================================

' Rechnet eine Menge in die Basiseinheit ihrer Groesse um
' (Volumen -> ml, Masse -> g, Anzahl -> Stueck).
Public Function InBasiseinheit(ByVal menge As Double, ByVal einheit As String) As Double

    Select Case LCase(Trim(einheit))
        Case "cl"
            InBasiseinheit = menge * 10
        Case "l", "kg"
            InBasiseinheit = menge * 1000
        Case Else
            ' ml, g, Stueck und alles Uebrige gelten bereits als Basis.
            InBasiseinheit = menge
    End Select

End Function


Private Function ArtikelZeileFinden(ByVal artikelName As String) As Long

    Dim wsArtikel As Worksheet
    Dim zeile As Long, letzte As Long

    artikelName = Trim(artikelName)
    If Len(artikelName) = 0 Then Exit Function

    Set wsArtikel = ThisWorkbook.Worksheets(BL_ARTIKEL)
    letzte = LetzteArtikelZeile()

    For zeile = ERSTE_DATENZEILE To letzte
        If StrComp(Trim(CStr(wsArtikel.Cells(zeile, SP_NAME).Value)), _
                   artikelName, vbTextCompare) = 0 Then
            ArtikelZeileFinden = zeile
            Exit Function
        End If
    Next zeile

End Function


Private Function LetzteArtikelZeile() As Long

    Dim wsArtikel As Worksheet
    Set wsArtikel = ThisWorkbook.Worksheets(BL_ARTIKEL)

    LetzteArtikelZeile = wsArtikel.Cells(wsArtikel.Rows.Count, SP_NAME).End(xlUp).Row
    If LetzteArtikelZeile < ERSTE_DATENZEILE Then LetzteArtikelZeile = ERSTE_DATENZEILE

End Function


Private Function IstMixArtikel(ByVal artikelZeile As Long) As Boolean

    Dim typ As String
    typ = LCase(Trim(CStr(ThisWorkbook.Worksheets(BL_ARTIKEL).Cells(artikelZeile, SP_TYP).Value)))

    IstMixArtikel = (InStr(typ, "mix") > 0) Or (InStr(typ, "rezept") > 0)

End Function


Private Function IstFlasche(ByVal artikelZeile As Long) As Boolean

    IstFlasche = (StrComp( _
        Trim(CStr(ThisWorkbook.Worksheets(BL_ARTIKEL).Cells(artikelZeile, SP_EINHEIT).Value)), _
        "Flasche", vbTextCompare) = 0)

End Function


Private Function NaechsteBelegnummer() As Long

    Dim ws As Worksheet
    Dim letzte As Long

    Set ws = ThisWorkbook.Worksheets(BL_VERKAEUFE)
    letzte = ws.Cells(ws.Rows.Count, 3).End(xlUp).Row

    If letzte < ERSTE_DATENZEILE Then
        NaechsteBelegnummer = 1
    Else
        NaechsteBelegnummer = Application.WorksheetFunction.Max( _
            ws.Range(ws.Cells(ERSTE_DATENZEILE, 3), ws.Cells(letzte, 3))) + 1
    End If

End Function


Private Function NullWennLeer(ByVal wert As Variant) As Double

    If IsNumeric(wert) Then
        NullWennLeer = CDbl(wert)
    Else
        NullWennLeer = 0
    End If

End Function
