# senml_encoder.py
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

import json


def crea_pacchetto_senml(nome_base, misurazioni):
    # Costruiamo la lista SenML: prima il nome base, poi tutte le misurazioni
    pacchetto = [{"bn": nome_base}]
    pacchetto.extend(misurazioni)

    return json.dumps(pacchetto, ensure_ascii=False)


def estrai_valore(pacchetto_senml, nome_misura):
    # Funzione di supporto per i client: cerca dentro un pacchetto SenML
    # gia' ricevuto (una lista di dizionari) la prima misura con un certo nome,
    # e ne restituisce il valore (numerico, testuale o booleano).

    for misura in pacchetto_senml:
        if misura.get("n") == nome_misura:
            if "vs" in misura:
                return misura["vs"]
            if "v" in misura:
                return misura["v"]
            if "vb" in misura:
                return misura["vb"]

    return None