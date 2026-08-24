# lock_command_request.py
# Questa classe descrive il "comando" che il client manda al server
# per dire alla serratura cosa fare: aprire o chiudere.
# Il client lo usa per SCRIVERE il comando, il server per LEGGERLO.

import json


class LockCommandRequest:

    # Le due azioni possibili. Le scriviamo qui come costanti
    # cosi' non rischiamo di sbagliare a scrivere la parola a mano.
    AZIONE_APRI = "apri"
    AZIONE_CHIUDI = "chiudi"
    AZIONI_VALIDE = (AZIONE_APRI, AZIONE_CHIUDI)

    def __init__(self, azione):
        # azione sara' una delle due costanti sopra: "apri" oppure "chiudi"
        self.azione = azione

    def to_json(self):
        # Trasforma il comando in testo JSON, per mandarlo al server
        return json.dumps({"azione": self.azione})

    @staticmethod
    def azione_da_json(testo_json):
        # Il contrario: legge il JSON arrivato dal client e restituisce
        # l'azione richiesta, oppure None se il comando non e' valido.
        dati = json.loads(testo_json)
        azione = dati.get("azione")

        if azione in LockCommandRequest.AZIONI_VALIDE:
            return azione
        return None
