# lock.py
# Questa classe rappresenta UNA serratura: ricorda se la porta e' aperta
# o chiusa e tiene lo storico di tutte le azioni fatte su quella porta.
# (Prima erano due classi separate, LockState e LockHistory: qui sono unite
#  perche' descrivono lo stesso oggetto, la serratura.)

import time

from request.lock_command_request import LockCommandRequest


class Lock:

    def __init__(self, nome_porta):
        # Il nome della porta, es. "Porta Principale" o "Garage"
        self.nome_porta = nome_porta

        # Stato iniziale: la porta parte sempre chiusa (True = aperta)
        self.aperta = False

        # Lista vuota all'inizio: qui salveremo tutte le azioni fatte
        self.azioni = []

    def stato_testo(self):
        # Restituisce lo stato come testo leggibile, utile per stamparlo
        return "aperta" if self.aperta else "chiusa"

    def esegui(self, azione):
        # Applica un comando ("apri" oppure "chiudi") e lo salva nello storico.
        # Restituisce False se l'azione non e' una di quelle previste.
        if azione not in LockCommandRequest.AZIONI_VALIDE:
            return False

        self.aperta = (azione == LockCommandRequest.AZIONE_APRI)
        self._salva_azione("apertura" if self.aperta else "chiusura")
        return True

    def apri(self):
        # Scorciatoia usata dal comando rapido POST
        self.esegui(LockCommandRequest.AZIONE_APRI)

    def _salva_azione(self, descrizione):
        # Salviamo il momento attuale come timestamp numerico (secondi),
        # che e' il formato richiesto dallo standard SenML per il campo "t"
        self.azioni.append({"azione": descrizione, "timestamp": time.time()})

    def to_senml_records(self):
        # Lo stato attuale + tutte le azioni passate, in formato SenML.
        # Le azioni hanno tutte lo stesso nome ("azione"): SenML lo permette,
        # perche' vengono distinte dal loro timestamp "t".
        records = [{"n": "stato", "vs": self.stato_testo()}]

        for evento in self.azioni:
            records.append({
                "n": "azione",
                "vs": evento["azione"],
                "t": evento["timestamp"]
            })

        return records
