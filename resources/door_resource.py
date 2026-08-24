# door_resource.py
# Questa classe rappresenta UNA serratura sul server.
# La stessa classe viene usata sia per la porta principale sia per il garage:
# basta crearla con un nome diverso (prima erano due file identici).
#
# Risponde alle richieste che arrivano dal client:
# - GET  -> restituisce stato e storico, in formato SenML+JSON
# - POST -> apre subito la porta (comando veloce, senza specificare nulla)
# - PUT  -> apre o chiude la porta, in base a cosa scrive il client
# Essendo "ObservableResource", puo' anche avvisare da sola i client
# che stanno osservando la porta (Observe), quando lo stato cambia.

import aiocoap
import aiocoap.resource as resource

from model.lock import Lock
from model.senml import crea_pacchetto_senml
from request.lock_command_request import LockCommandRequest


class DoorResource(resource.ObservableResource):

    def __init__(self, nome_porta, nome_risorsa):
        super().__init__()
        self.serratura = Lock(nome_porta)
        self.nome_risorsa = nome_risorsa          # es. "main_door"
        self.nome_base = nome_risorsa + "/"       # nome base SenML

    # ----- funzioni di supporto ------------------------------------------

    def _log(self, messaggio):
        print(f"{self.nome_risorsa} -> {messaggio}")

    def _risposta(self, records):
        # Costruisce il messaggio CoAP con il pacchetto SenML dentro
        payload_testo = crea_pacchetto_senml(self.nome_base, records)
        return aiocoap.Message(payload=payload_testo.encode('utf-8'))

    def _risposta_solo_stato(self):
        # Dopo un comando basta rimandare lo stato aggiornato, senza storico
        return self._risposta([{"n": "stato", "vs": self.serratura.stato_testo()}])

    # ----- richieste dei client ------------------------------------------

    async def render_get(self, request):
        self._log("Richiesta GET ricevuta, invio stato e storico in SenML ...")
        return self._risposta(self.serratura.to_senml_records())

    async def render_post(self, request):
        self._log("Richiesta POST ricevuta, apertura rapida della porta ...")

        self.serratura.apri()
        self.updated_state()   # avvisa i client in ascolto (Observe)

        return self._risposta_solo_stato()

    async def render_put(self, request):
        self._log("Richiesta PUT ricevuta")

        try:
            # Il comando ricevuto dal client resta un semplice JSON
            # (non e' un dato di telemetria, ma un comando di controllo)
            azione = LockCommandRequest.azione_da_json(request.payload.decode('utf-8'))
        except Exception as errore:
            self._log(f"Comando illeggibile: {errore}")
            return aiocoap.Message(code=aiocoap.Code.BAD_REQUEST,
                                   payload=b"Comando non leggibile")

        if not self.serratura.esegui(azione):
            self._log(f"Azione non valida: {azione}")
            return aiocoap.Message(code=aiocoap.Code.BAD_REQUEST,
                                   payload=b"Azione non valida")

        self._log(f"Porta {self.serratura.stato_testo()}")
        self.updated_state()   # avvisa i client in ascolto (Observe)

        return self._risposta_solo_stato()
