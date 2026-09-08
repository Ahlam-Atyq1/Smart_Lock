# model.py
# Il "modello" del sistema: gli oggetti di cui parla il progetto, senza
# nessun dettaglio di rete (di CoAP si occupa server.py).
# Dentro ci sono tre cose:
#   - LockCommandRequest : il comando apri/chiudi scambiato fra client e server
#   - Lock               : una serratura (stato + storico delle azioni)
#   - EnvironmentSensor  : i sensori simulati di casa

import json
import random
import time


class LockCommandRequest:
    # Descrive il "comando" che il client manda al server per dire alla
    # serratura cosa fare. Il client lo usa per SCRIVERE il comando,
    # il server per LEGGERLO.

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


class Lock:
    # Rappresenta UNA serratura: ricorda se la porta e' aperta o chiusa
    # e tiene lo storico di tutte le azioni fatte su quella porta.

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


class EnvironmentSensor:
    # Simula i sensori installati vicino all'ingresso di casa: il sensore di
    # presenza (movimento) e il sensore ambientale (temperatura e umidita').
    # In un dispositivo vero qui leggeremmo dei sensori fisici, per la
    # simulazione generiamo valori casuali realistici.

    def leggi_presenza(self):
        # Sensore di presenza (es. PIR): True = qualcuno rilevato
        return random.choice([True, False])

    def leggi_temperatura(self):
        # Temperatura in gradi Celsius
        return round(random.uniform(18.0, 26.0), 1)

    def leggi_umidita(self):
        # Umidita' in percentuale
        return round(random.uniform(30.0, 60.0), 1)

    def to_senml_records(self):
        # Ogni sensore diventa un record SenML, con il suo nome,
        # il suo valore e (quando ha senso) la sua unita' di misura
        return [
            {"n": "presenza", "vb": self.leggi_presenza()},
            {"n": "temperatura", "u": "Cel", "v": self.leggi_temperatura()},
            {"n": "umidita", "u": "%RH", "v": self.leggi_umidita()},
        ]
