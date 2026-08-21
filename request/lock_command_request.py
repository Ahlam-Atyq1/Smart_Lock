# lock_command_request.py
# Questa classe descrive il "comando" che il client manda al server
# per dire alla serratura cosa fare: aprire o chiudere.

import json


class LockCommandRequest:

    # Le due azioni possibili. Le scriviamo qui come costanti
    # cosi' non rischiamo di sbagliare a scrivere la parola a mano.
    AZIONE_APRI = "apri"
    AZIONE_CHIUDI = "chiudi"

    def __init__(self, azione):
        # azione sara' una delle due costanti sopra: "apri" oppure "chiudi"
        self.azione = azione

    def to_json(self):
        # Trasforma il comando in testo JSON, per mandarlo al server
        return json.dumps(self.__dict__)