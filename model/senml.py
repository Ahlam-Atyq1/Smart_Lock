# senml.py
# SenML (Sensor Measurement List) e' uno standard per scrivere dati di
# sensori in JSON in modo strutturato e riconoscibile da qualsiasi sistema.
#
# Un pacchetto SenML e' una LISTA. Il primo elemento contiene il "nome base"
# (bn), che indica a quale dispositivo appartengono i dati. Gli elementi
# successivi sono le singole misurazioni, ognuna con:
# - "n"  = nome della misura (es. "temperatura")
# - "v"  = valore numerico (es. 22.4)
# - "vs" = valore testuale (es. "chiusa")
# - "vb" = valore vero/falso (es. True)
# - "u"  = unita' di misura (es. "Cel" per Celsius)
# - "t"  = timestamp, cioe' il momento in cui e' stata presa la misura
#
# Qui dentro c'e' tutto cio' che serve per SenML: creare un pacchetto
# (lato server) e leggerlo o stamparlo (lato client).

import json
from datetime import datetime


def crea_pacchetto_senml(nome_base, misurazioni):
    # Costruiamo la lista SenML: prima il nome base, poi tutte le misurazioni
    pacchetto = [{"bn": nome_base}]
    pacchetto.extend(misurazioni)

    return json.dumps(pacchetto, ensure_ascii=False)


def valore_di(misura):
    # Ogni misura ha il valore in uno solo di questi tre campi:
    # "vs" (testo), "v" (numero), "vb" (vero/falso)
    for campo in ("vs", "v", "vb"):
        if campo in misura:
            return misura[campo]
    return None


def estrai_valore(pacchetto_senml, nome_misura):
    # Cerca dentro un pacchetto gia' ricevuto (una lista di dizionari)
    # la prima misura con un certo nome e ne restituisce il valore.
    for misura in pacchetto_senml:
        if misura.get("n") == nome_misura:
            return valore_di(misura)
    return None


def formatta_pacchetto(pacchetto_senml):
    # Trasforma il pacchetto in righe di testo leggibili da una persona.
    righe = []

    for misura in pacchetto_senml:
        if "bn" in misura:
            righe.append("Dispositivo: " + misura["bn"])
            continue

        valore = valore_di(misura)
        if isinstance(valore, bool):
            valore = "si" if valore else "no"

        riga = f"  - {misura.get('n')}: {valore}"

        if "u" in misura:
            riga += " " + misura["u"]

        # Se c'e' un timestamp lo mostriamo come data/ora normale
        if "t" in misura:
            data_ora = datetime.fromtimestamp(misura["t"]).strftime("%d/%m/%Y %H:%M:%S")
            riga += f"  ({data_ora})"

        righe.append(riga)

    return righe
