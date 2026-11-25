# ================================================================
# ================================================================
#                          MEIN CODE
# ================================================================
# ================================================================
'''
Das ist meine Flughafen_codewetterabfrage im METAR-Format über die
Aviation Weather Center API: https://aviationweather.gov/api/data/metar?ids=LOWI
ids ist der ICAO-Code des Flughafen_codes (Bsp. LOWI für Innsbruck)
'''

import requests

def api():

    flughafen_code = input().upper()

    url = f"https://aviationweather.gov/api/data/metar?ids={flughafen_code}"

    metar = requests.get(url).text
    metar_teile = metar.split()

    return metar, metar_teile


def flughafen_suche():
    flughafen_name = input()

    url_f = f"https://nominatim.openstreetmap.org/search?q={flughafen_name} airport&format=json&namedetails=1&limit=5"

    flughafen_daten = requests.get(url_f, headers = {"User-Agent":"HTL-Anichstraße Airport-METAR-Project"}).json()

    return flughafen_daten[0]['namedetails']['icao'], flughafen_daten[0]['name']


# ================================================================
# ================================================================
#                     AB HIER: GUI (von Claude)
# ================================================================
# ================================================================

import threading
import tkinter as tk
from tkinter import ttk


# ----------------------------------------------------------------
# Farben und Schriften
# ----------------------------------------------------------------
HINTERGRUND = "#f3f4f6"
KARTE = "#ffffff"
RAND = "#d1d5db"
TEXT = "#111827"
TEXT_GRAU = "#6b7280"
AKZENT = "#374151"
AKZENT_HOVER = "#1f2937"
KNOPF_TEXT = "#ffffff"
FEHLER = "#dc2626"

SCHRIFT = "Garamond"
MONO = "Consolas"


# ----------------------------------------------------------------
# Dictionaries (alle METAR-Abkürzungen nach ICAO Annex 3 / WMO)
# ----------------------------------------------------------------
wolken = {
    "FEW": "wenige Wolken (1-2/8)",
    "SCT": "aufgelockerte Bewölkung (3-4/8)",
    "BKN": "durchbrochene Bewölkung (5-7/8)",
    "OVC": "geschlossene Bewölkung (8/8)",
}

wolken_art = {
    "CB": "Cumulonimbus, Gewitterwolken!",
    "TCU": "aufgetürmte Cumulus-Wolken",
}

wetter = {
    # Zusätze
    "VC": "in der Nähe",
    "RE": "kürzlich",
    # Beschreibungen
    "MI": "flacher",
    "BC": "schwadenförmiger",
    "PR": "teilweiser",
    "DR": "fegender",
    "BL": "treibender",
    "SH": "Schauer",
    "TS": "Gewitter",
    "FZ": "gefrierender",
    # Niederschlag
    "DZ": "Nieselregen",
    "RA": "Regen",
    "SN": "Schnee",
    "SG": "Schneegriesel",
    "IC": "Eisnadeln",
    "PL": "Eiskörner",
    "GR": "Hagel",
    "GS": "Graupel",
    "UP": "unbekannter Niederschlag",
    # Sichtbehinderung
    "BR": "feuchter Dunst",
    "FG": "Nebel",
    "FU": "Rauch",
    "VA": "Vulkanasche",
    "DU": "Staub",
    "SA": "Sand",
    "HZ": "trockener Dunst",
    "PY": "Gischt",
    # Sonstige Erscheinungen
    "PO": "Staub-/Sandwirbel",
    "SQ": "Böenwalze",
    "FC": "Trichterwolke (Tornado/Wasserhose)",
    "SS": "Sandsturm",
    "DS": "Staubsturm",
}

intensitaet = {
    "-": "leicht",
    "+": "stark",
}

wind_einheiten = {
    "KT": "Knoten",
    "MPS": "m/s",
    "KMH": "km/h",
}

richtungen = {
    "N": "Norden",
    "NE": "Nordosten",
    "E": "Osten",
    "SE": "Südosten",
    "S": "Süden",
    "SW": "Südwesten",
    "W": "Westen",
    "NW": "Nordwesten",
    "NDV": "keine Richtungsunterschiede messbar",
}

pistensicht = {
    "P": "mehr als",
    "M": "weniger als",
    "U": "steigend",
    "D": "fallend",
    "N": "gleichbleibend",
}

zeitangaben = {
    "FM": "ab",
    "TL": "bis",
    "AT": "um",
}

sonstiges = {
    "METAR": "Routinemeldung",
    "SPECI": "Sondermeldung",
    "AUTO": "automatisch erstellte Meldung",
    "COR": "korrigierte Meldung",
    "NIL": "keine Meldung verfügbar",
    "CAVOK": "Sicht über 10 km, keine Wolken unter 5000 ft, kein signifikantes Wetter",
    "SKC": "wolkenloser Himmel",
    "CLR": "keine Wolken unter 12000 ft (automatisch gemessen)",
    "NSC": "keine signifikanten Wolken",
    "NCD": "keine Wolken erkannt (automatisch gemessen)",
    "NSW": "kein signifikantes Wetter mehr",
    "WS": "Windscherung",
    "ALL": "alle",
    "RWY": "Pisten",
    "NOSIG": "keine wesentliche Änderung in den nächsten 2 Stunden",
    "TEMPO": "vorübergehend:",
    "BECMG": "Übergang zu:",
}

# Wird bei jeder erfolgreichen Flughafensuche ergänzt,
# z.B. {"LOWI": "Flughafen Innsbruck"}
bekannte_namen = {}


# ----------------------------------------------------------------
# Übersetzung: gibt eine Liste von (Abkürzung, Bedeutung) zurück
# ----------------------------------------------------------------
def temperatur(text):
    # "M" steht für Minus, z.B. M05 = -5 °C
    if text.startswith("M"):
        return -int(text[1:])
    return int(text)


def ist_wetter(teil):
    rest = teil.lstrip("-+")
    if len(rest) == 0 or len(rest) % 2 != 0:
        return False
    for i in range(0, len(rest), 2):
        if rest[i:i + 2] not in wetter:
            return False
    return True


def wetter_uebersetzen(teil):
    beschreibung = ""
    if teil[0] in intensitaet:
        beschreibung = intensitaet[teil[0]] + " "
    rest = teil.lstrip("-+")
    woerter = []
    for i in range(0, len(rest), 2):
        woerter.append(wetter[rest[i:i + 2]])
    return beschreibung + " ".join(woerter)


def wind_einheit(teil):
    # Gibt KT, MPS oder KMH zurück, wenn der Teil eine Windangabe ist
    for einheit in wind_einheiten:
        if teil.endswith(einheit) and (teil[:3].isdigit() or teil.startswith("VRB")):
            return einheit
    return None


def pistensicht_uebersetzen(wert):
    # z.B. P1500U -> "mehr als 1500 m, steigend"
    wert = wert.replace("/", "")
    trend = ""
    if wert[-1] in "UDN":
        trend = ", " + pistensicht[wert[-1]]
        wert = wert[:-1]
    einheit = "m"
    if wert.endswith("FT"):
        einheit = "ft"
        wert = wert[:-2]
    werte = []
    for zahl in wert.split("V"):
        if zahl[0] in "PM":
            werte.append(f"{pistensicht[zahl[0]]} {int(zahl[1:])}")
        else:
            werte.append(str(int(zahl)))
    if len(werte) == 2:
        return f"zwischen {werte[0]} und {werte[1]} {einheit}{trend}"
    return f"{werte[0]} {einheit}{trend}"


def uebersetze(metar_teile, flughafen_code):
    ergebnis = []

    for teil in metar_teile:
        try:
            if teil == "RMK":
                ergebnis.append((teil, "ab hier Bemerkungen (werden nicht übersetzt)"))
                break

            elif teil in sonstiges:
                ergebnis.append((teil, sonstiges[teil]))

            elif teil == flughafen_code:
                if teil in bekannte_namen:
                    ergebnis.append((teil, f"{teil} -> {bekannte_namen[teil]}"))
                else:
                    ergebnis.append((teil, f"Flughafen {teil}"))

            # Zeit, z.B. 171850Z
            elif len(teil) == 7 and teil.endswith("Z") and teil[:6].isdigit():
                ergebnis.append((teil, f"Tag {teil[0:2]}, {teil[2:4]}:{teil[4:6]} UTC"))

            # Wind, z.B. 24012KT, 24012G25KT, VRB03KT, 00000KT, 27008MPS
            elif wind_einheit(teil):
                einheit = wind_einheit(teil)
                rest = teil[:-len(einheit)]
                richtung = rest[0:3]
                boeen = ""
                if "G" in rest:
                    rest, boeen = rest.split("G")
                geschw = int(rest[3:])
                name = wind_einheiten[einheit]
                if geschw == 0:
                    text = "Windstille"
                elif richtung == "VRB":
                    text = f"Wind aus wechselnden Richtungen mit {geschw} {name}"
                else:
                    text = f"Wind aus {int(richtung)}° mit {geschw} {name}"
                if boeen:
                    text += f", Böen bis {int(boeen)} {name}"
                ergebnis.append((teil, text))

            # Windrichtung schwankt, z.B. 210V270
            elif len(teil) == 7 and teil[3] == "V" and teil[:3].isdigit():
                ergebnis.append((teil, f"Windrichtung schwankt zwischen {teil[0:3]}° und {teil[4:7]}°"))

            # Sicht in Metern, z.B. 9999, 0800, 4000NE, 9999NDV
            elif len(teil) >= 4 and teil[:4].isdigit() and (teil[4:] == "" or teil[4:] in richtungen):
                if teil[:4] == "9999":
                    text = "Sicht 10 km oder mehr"
                else:
                    text = f"Sicht {int(teil[:4])} m"
                if teil[4:] == "NDV":
                    text += f" ({richtungen['NDV']})"
                elif teil[4:]:
                    text += f" Richtung {richtungen[teil[4:]]}"
                ergebnis.append((teil, text))

            # Sicht in Meilen (USA), z.B. 10SM, 1/2SM, P6SM
            elif teil.endswith("SM"):
                wert = teil[:-2]
                if wert[0] in pistensicht:
                    wert = f"{pistensicht[wert[0]]} {wert[1:]}"
                ergebnis.append((teil, f"Sicht {wert} Meilen"))

            # Vertikalsicht (Himmel nicht erkennbar), z.B. VV002
            elif teil.startswith("VV"):
                ergebnis.append((teil, f"Himmel nicht erkennbar, Vertikalsicht {int(teil[2:5]) * 100} ft"))

            # Wolken, z.B. BKN030, BKN030CB, SCT025TCU
            elif teil[0:3] in wolken:
                text = f"{wolken[teil[0:3]]} in {int(teil[3:6]) * 100} ft"
                if teil[6:] in wolken_art:
                    text += f" ({wolken_art[teil[6:]]})"
                ergebnis.append((teil, text))

            # Pistensichtweite, z.B. R26/1200N, R08L/P1500U, R27/0600V1000D
            elif teil.startswith("R") and "/" in teil:
                piste, wert = teil.split("/", 1)
                ergebnis.append((teil, f"Pistensichtweite Piste {piste[1:]}: {pistensicht_uebersetzen(wert)}"))

            # Zeitangabe in Trends, z.B. FM1200, TL1430, AT1300
            elif teil[0:2] in zeitangaben and teil[2:].isdigit() and len(teil) == 6:
                ergebnis.append((teil, f"{zeitangaben[teil[0:2]]} {teil[2:4]}:{teil[4:6]} UTC"))

            # Temperatur/Taupunkt, z.B. 08/03 oder M02/M05
            elif "/" in teil:
                temp_text, tau_text = teil.split("/")
                ergebnis.append((teil, f"Temperatur {temperatur(temp_text)} °C, "
                                       f"Taupunkt {temperatur(tau_text)} °C"))

            # Luftdruck in hPa, z.B. Q1015
            elif teil.startswith("Q") and teil[1:].isdigit():
                ergebnis.append((teil, f"Luftdruck (QNH) {int(teil[1:])} hPa"))

            # Luftdruck in inHg (USA), z.B. A2992
            elif teil.startswith("A") and teil[1:].isdigit():
                ergebnis.append((teil, f"Luftdruck {teil[1:3]}.{teil[3:5]} inHg"))

            # Wetter, z.B. -RA, +TSRA, BR
            elif ist_wetter(teil):
                ergebnis.append((teil, wetter_uebersetzen(teil)))

            else:
                ergebnis.append((teil, "(unbekannt)"))

        except ValueError:
            # Falls ein Teil zwar wie ein Muster aussieht, aber keine Zahl drin ist
            ergebnis.append((teil, "(unbekannt)"))

    return ergebnis


# ----------------------------------------------------------------
# METAR abrufen (läuft im Hintergrund, damit die GUI nicht einfriert)
# ----------------------------------------------------------------
ergebnis_abruf = {}


gui_eingabe = ""


def input(text=""):
    return gui_eingabe


def metar_holen(flughafen_code):
    global gui_eingabe
    gui_eingabe = flughafen_code
    try:
        metar, metar_teile = api()
        ergebnis_abruf["metar"] = metar.strip()
        ergebnis_abruf["metar_teile"] = metar_teile
        ergebnis_abruf["fehler"] = None
    except Exception as e:
        ergebnis_abruf["metar"] = ""
        ergebnis_abruf["metar_teile"] = []
        ergebnis_abruf["fehler"] = f"Fehler: {e}"
    ergebnis_abruf["fertig"] = True


# ----------------------------------------------------------------
# Flughafen suchen (läuft ebenfalls im Hintergrund)
# ----------------------------------------------------------------
ergebnis_suche = {}


def flughafen_holen(suchtext):
    global gui_eingabe
    gui_eingabe = suchtext
    ergebnis_suche["icao"] = ""
    ergebnis_suche["name"] = ""
    ergebnis_suche["fehler"] = None
    try:
        icao, name = flughafen_suche()
        ergebnis_suche["icao"] = icao.strip().upper()
        ergebnis_suche["name"] = name
    except IndexError:
        ergebnis_suche["fehler"] = f'Kein Flughafen zu "{suchtext}" gefunden.'
    except KeyError:
        ergebnis_suche["fehler"] = f'Zu "{suchtext}" wurde ein Treffer gefunden, aber ohne ICAO-Code.'
    except requests.RequestException:
        ergebnis_suche["fehler"] = "Suchdienst nicht erreichbar. Besteht eine Internetverbindung?"
    except Exception as e:
        ergebnis_suche["fehler"] = f"Fehler: {e}"
    ergebnis_suche["fertig"] = True


# ----------------------------------------------------------------
# GUI-Aktionen
# ----------------------------------------------------------------
aktueller_flughafen_code = ""

# METAR-Abruf und Suche teilen sich gui_eingabe (für input()),
# deshalb darf immer nur eine Anfrage gleichzeitig laufen.
anfrage_laeuft = False


def anfrage_sperren(gesperrt):
    global anfrage_laeuft
    anfrage_laeuft = gesperrt
    zustand = "disabled" if gesperrt else "normal"
    abrufen_knopf.config(state=zustand)
    suchen_knopf.config(state=zustand)


def suche_starten(event=None):
    if anfrage_laeuft:
        return
    suchtext = such_eingabe.get().strip()

    if suchtext == "":
        such_icao.config(text="")
        such_name.config(text="Bitte einen Flughafen- oder Stadtnamen eingeben.", fg=FEHLER)
        return

    such_icao.config(text="")
    such_name.config(text="Suche läuft ...", fg=TEXT_GRAU)
    anfrage_sperren(True)

    ergebnis_suche["fertig"] = False
    threading.Thread(target=flughafen_holen, args=(suchtext,), daemon=True).start()
    root.after(100, suche_pruefen)


def suche_pruefen():
    # Schaut alle 100 ms nach, ob die Suche fertig ist
    if not ergebnis_suche.get("fertig"):
        root.after(100, suche_pruefen)
        return

    anfrage_sperren(False)

    if ergebnis_suche["fehler"]:
        such_icao.config(text="")
        such_name.config(text=ergebnis_suche["fehler"], fg=FEHLER)
        return

    icao = ergebnis_suche["icao"]
    name = ergebnis_suche["name"]
    bekannte_namen[icao] = name

    such_icao.config(text=icao)
    such_name.config(text=name, fg=TEXT_GRAU)

    # ICAO-Code ins METAR-Feld eintragen (noch nicht abrufen)
    eingabe_var.set(icao)
    hinweis.config(text="", fg=TEXT_GRAU)


def abrufen_starten(event=None):
    global aktueller_flughafen_code
    if anfrage_laeuft:
        return
    flughafen_code = eingabe.get().strip()

    if len(flughafen_code) != 4 or not flughafen_code.isalpha():
        hinweis.config(text="Bitte einen 4-stelligen ICAO-Code eingeben (z.B. LOWI).", fg=FEHLER)
        return

    hinweis.config(text="", fg=TEXT_GRAU)
    aktueller_flughafen_code = flughafen_code

    # Ladetext in beide Boxen schreiben
    text_setzen(metar_text, "Lade METAR-Daten...", TEXT_GRAU)
    text_setzen(uebersetzung_text, "Lade METAR-Übersetzung...", TEXT_GRAU)
    anfrage_sperren(True)

    ergebnis_abruf["fertig"] = False
    threading.Thread(target=metar_holen, args=(flughafen_code,), daemon=True).start()
    root.after(100, abruf_pruefen)


def abruf_pruefen():
    # Schaut alle 100 ms nach, ob der Download fertig ist
    if not ergebnis_abruf.get("fertig"):
        root.after(100, abruf_pruefen)
        return

    anfrage_sperren(False)
    metar = ergebnis_abruf["metar"]
    fehler = ergebnis_abruf["fehler"]

    if fehler:
        text_setzen(metar_text, fehler, FEHLER)
        text_setzen(uebersetzung_text, "", TEXT)
    elif metar == "":
        text_setzen(metar_text, f"Kein METAR für {aktueller_flughafen_code} gefunden.", FEHLER)
        text_setzen(uebersetzung_text, "", TEXT)
    else:
        text_setzen(metar_text, metar, TEXT)
        # metar_teile kommt direkt aus api() (metar.split())
        text_setzen(uebersetzung_text, "", TEXT)
        uebersetzung_text.config(state="normal")
        for abkuerzung, bedeutung in uebersetze(ergebnis_abruf["metar_teile"], aktueller_flughafen_code):
            uebersetzung_text.insert("end", f"{abkuerzung}\t", "code")
            uebersetzung_text.insert("end", f"{bedeutung}\n", "bedeutung")
        uebersetzung_text.config(state="disabled")


def text_setzen(feld, text, farbe):
    feld.config(state="normal", fg=farbe)
    feld.delete("1.0", "end")
    feld.insert("1.0", text)
    feld.config(state="disabled")


# ----------------------------------------------------------------
# Hilfsfunktion: flacher, moderner Knopf
# ----------------------------------------------------------------
def knopf(eltern, text, befehl, groesse=14, breite=None):
    b = tk.Button(eltern, text=text, command=befehl, font=(SCHRIFT, groesse, "bold"),
                  bg=AKZENT, fg=KNOPF_TEXT, activebackground=AKZENT_HOVER,
                  activeforeground=KNOPF_TEXT, disabledforeground="#9ca3af", relief="flat", bd=0,
                  padx=18, pady=8, cursor="hand2", width=breite,
                  highlightthickness=0)
    return b


# ----------------------------------------------------------------
# Hilfsfunktion: sieht aus wie ein Label, aber der Text lässt sich
# markieren und mit Strg+C kopieren (schreibgeschütztes Eingabefeld)
# ----------------------------------------------------------------
def kopierbar(eltern, text, schrift, hintergrund, farbe, breite):
    feld = tk.Entry(eltern, font=schrift, fg=farbe, readonlybackground=hintergrund,
                    relief="flat", bd=0, highlightthickness=0, width=breite)
    feld.insert(0, text)
    feld.config(state="readonly")
    return feld


# ----------------------------------------------------------------
# Fenster aufbauen
# ----------------------------------------------------------------
# Scharfe Darstellung bei Windows-Skalierung (sonst wird alles unscharf hochgezogen)
try:
    import ctypes
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

root = tk.Tk()
root.title("METAR-Abfrage")
faktor = root.winfo_fpixels("1i") / 96  # z.B. 1.5 bei 150 % Skalierung
root.geometry(f"{int(1150 * faktor)}x{int(900 * faktor)}")
root.configure(bg=HINTERGRUND)

stil = ttk.Style()
stil.theme_use("clam")

# Container, der alles in der Mitte hält
mitte = tk.Frame(root, bg=HINTERGRUND)
mitte.pack(expand=True, fill="both", padx=30, pady=30)

oben = tk.Frame(mitte, bg=HINTERGRUND)
oben.pack()

# --- Flughafensuche (links) ---
such_karte = tk.Frame(oben, bg=KARTE, padx=26, pady=30,
                      highlightbackground=RAND, highlightcolor=RAND, highlightthickness=1)
such_karte.pack(side="left", fill="y", padx=(0, 16))

tk.Label(such_karte, text="Flughafensuche", font=(SCHRIFT, 20, "bold"),
         bg=KARTE, fg=TEXT).pack(anchor="w")

tk.Label(such_karte, text="Flughafen- oder Stadtnamen eingeben,\num den ICAO-Code zu finden.",
         font=(SCHRIFT, 13), bg=KARTE, fg=TEXT_GRAU, justify="left").pack(anchor="w", pady=(6, 16))

such_zeile = tk.Frame(such_karte, bg=KARTE)
such_zeile.pack(fill="x")

such_eingabe = tk.Entry(such_zeile, font=(SCHRIFT, 16), bg=HINTERGRUND, fg=TEXT,
                        insertbackground=AKZENT, relief="flat", bd=0, width=14,
                        highlightthickness=0)
such_eingabe.pack(side="left", fill="x", expand=True, ipady=8, ipadx=6)
such_eingabe.bind("<Return>", suche_starten)

suchen_knopf = knopf(such_zeile, "Suchen", suche_starten, groesse=13)
suchen_knopf.pack(side="left", padx=(10, 0), fill="y")

# Ausgabebox: ICAO-Code groß, darunter der Name klein
such_ausgabe = tk.Frame(such_karte, bg=HINTERGRUND, padx=14, pady=10)
such_ausgabe.pack(fill="both", expand=True, pady=(14, 0))

such_icao = tk.Label(such_ausgabe, text="", font=(MONO, 28, "bold"),
                     bg=HINTERGRUND, fg=AKZENT)
such_icao.pack(anchor="w")

such_name = tk.Label(such_ausgabe, text="", font=(SCHRIFT, 13), bg=HINTERGRUND,
                     fg=TEXT_GRAU, justify="left", wraplength=int(300 * faktor))
such_name.pack(anchor="w")

# --- Eingabekarte ---
karte = tk.Frame(oben, bg=KARTE, padx=36, pady=30,
                 highlightbackground=RAND, highlightcolor=RAND, highlightthickness=1)
karte.pack(side="left", fill="y")

tk.Label(karte, text="✈  Flughafenwetter", font=(SCHRIFT, 28, "bold"),
         bg=KARTE, fg=TEXT).pack(anchor="w")

tk.Label(karte, text="Dies ist eine internationale Flughafenwetterabfrage im METAR-Format.",
         font=(SCHRIFT, 14), bg=KARTE, fg=TEXT_GRAU).pack(anchor="w", pady=(6, 0))

tk.Label(karte, text="Gib den 4-stelligen ICAO-Code eines Flughafens ein und drücke Enter.",
         font=(SCHRIFT, 13), bg=KARTE, fg=TEXT_GRAU).pack(anchor="w", pady=(2, 20))

eingabe_zeile = tk.Frame(karte, bg=KARTE)
eingabe_zeile.pack(fill="x")

eingabe_var = tk.StringVar()
eingabe = tk.Entry(eingabe_zeile, textvariable=eingabe_var, font=(MONO, 22),
                   bg=HINTERGRUND, fg=TEXT, insertbackground=AKZENT,
                   relief="flat", bd=0, width=12, justify="center", highlightthickness=0)
eingabe.pack(side="left", fill="x", expand=True, ipady=8)
eingabe.bind("<Return>", abrufen_starten)
# Eingabe automatisch in Großbuchstaben und max. 4 Zeichen
eingabe_var.trace_add("write", lambda *a: eingabe_var.set(eingabe_var.get().upper()[:4]))

abrufen_knopf = knopf(eingabe_zeile, "METAR abrufen", abrufen_starten)
abrufen_knopf.pack(side="left", padx=(12, 0), fill="y")

hinweis = tk.Label(karte, text="", font=(SCHRIFT, 13), bg=KARTE, fg=TEXT_GRAU)
hinweis.pack(anchor="w", pady=(10, 0))

# --- Ergebnis (von Anfang an sichtbar, erst leer) ---
ergebnis_bereich = tk.Frame(mitte, bg=HINTERGRUND)
ergebnis_bereich.pack(pady=(24, 0), fill="both", expand=True)

metar_karte = tk.Frame(ergebnis_bereich, bg=KARTE, padx=24, pady=18,
                       highlightbackground=RAND, highlightcolor=RAND, highlightthickness=1)
metar_karte.pack(fill="x")
tk.Label(metar_karte, text="RAW METAR", font=(SCHRIFT, 12, "bold"),
         bg=KARTE, fg=TEXT_GRAU).pack(anchor="w")
# Text-Feld statt Label, damit man den METAR markieren und kopieren kann
metar_text = tk.Text(metar_karte, font=(MONO, 16), bg=KARTE, fg=TEXT, relief="flat", bd=0,
                     highlightthickness=0, wrap="word", height=2, width=1)
metar_text.pack(fill="x", pady=(6, 0))
metar_text.config(state="disabled")
# Beim Klick den Fokus holen, damit Strg+C hier kopiert
metar_text.bind("<Button-1>", lambda e: metar_text.focus_set())

uebersetzung_rahmen = tk.Frame(ergebnis_bereich, bg=KARTE, padx=24, pady=18,
                               highlightbackground=RAND, highlightcolor=RAND, highlightthickness=1)
uebersetzung_rahmen.pack(pady=(16, 0), fill="both", expand=True)
tk.Label(uebersetzung_rahmen, text="ÜBERSETZUNG", font=(SCHRIFT, 12, "bold"),
         bg=KARTE, fg=TEXT_GRAU).pack(anchor="w", pady=(0, 6))
uebersetzung_text = tk.Text(uebersetzung_rahmen, font=(SCHRIFT, 14), bg=KARTE, fg=TEXT,
                            relief="flat", bd=0, highlightthickness=0, wrap="word",
                            tabs=("170p",), spacing1=3, spacing3=3, height=8,
                            yscrollcommand=lambda *a: scrollbar.set(*a))
uebersetzung_text.bind("<Button-1>", lambda e: uebersetzung_text.focus_set())
uebersetzung_text.tag_configure("code", font=(MONO, 14, "bold"), foreground=AKZENT)
uebersetzung_text.tag_configure("bedeutung", lmargin2="170p")
scrollbar = ttk.Scrollbar(uebersetzung_rahmen, orient="vertical",
                          command=uebersetzung_text.yview)
scrollbar.pack(side="right", fill="y")
uebersetzung_text.pack(side="left", fill="both", expand=True)
uebersetzung_text.config(state="disabled")

eingabe.focus_set()
root.mainloop()
