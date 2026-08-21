# lock_history.py
# Questa classe tiene la lista di tutte le azioni fatte sulle serrature
# (ogni volta che una porta viene aperta o chiusa, la salviamo qui).

import time
from datetime import datetime


class LockHistory:

    def __init__(self):
        # Lista vuota all'inizio: qui dentro salveremo tutte le azioni
        self.azioni = []

    def aggiungi_azione(self, nome_porta, azione):
        # Salviamo il momento attuale come timestamp numerico (secondi),
        # che e' il formato richiesto dallo standard SenML per il campo "t"
        momento_attuale = time.time()

        evento = {
            "porta": nome_porta,
            "azione": azione,
            "timestamp": momento_attuale
        }

        self.azioni.append(evento)

    def to_senml_records(self):
        # Trasforma ogni azione salvata in un record SenML.
        # Usiamo lo stesso nome ("azione") per ogni record: SenML permette
        # piu' misurazioni con lo stesso nome, distinte dal loro timestamp "t".
        records = []

        for evento in self.azioni:
            records.append({
                "n": "azione",
                "vs": evento["azione"],
                "t": evento["timestamp"]
            })

        return records

    def to_testo_leggibile(self):
        # Utile per stampare lo storico in modo leggibile da una persona,
        # convertendo il timestamp numerico in data/ora normale
        righe = []
        for evento in self.azioni:
            data_ora = datetime.fromtimestamp(evento["timestamp"]).strftime("%d/%m/%Y %H:%M:%S")
            righe.append(f"{evento['azione']} - {data_ora}")
        return righe