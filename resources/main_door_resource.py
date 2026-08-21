# main_door_resource.py
# Questa classe rappresenta la serratura della PORTA PRINCIPALE sul server.
# Risponde alle richieste che arrivano dal client:
# - GET  -> restituisce stato e storico, in formato SenML+JSON
# - POST -> apre subito la porta (comando veloce, senza specificare nulla)
# - PUT  -> apre o chiude la porta, in base a cosa scrive il client

import aiocoap.resource as resource
import aiocoap
import json

from model.lock_state import LockState
from model.lock_history import LockHistory
from request.lock_command_request import LockCommandRequest
from model.senml_encoder import crea_pacchetto_senml


class MainDoorResource(resource.ObservableResource):

    def __init__(self):
        super().__init__()
        self.stato = LockState("Porta Principale")
        self.storico = LockHistory()

    async def render_get(self, request):
        print("MainDoorResource -> Richiesta GET ricevuta")
        print("MainDoorResource -> Invio stato e storico in formato SenML ... ")

        # Il record principale: lo stato attuale della porta
        misurazioni = [{"n": "stato", "vs": self.stato.stato_testo()}]

        # Aggiungiamo anche tutte le azioni passate, come record SenML
        misurazioni.extend(self.storico.to_senml_records())

        payload_testo = crea_pacchetto_senml("main_door/", misurazioni)
        return aiocoap.Message(payload=payload_testo.encode('utf-8'))

    async def render_post(self, request):
        print("MainDoorResource -> Richiesta POST ricevuta")
        print("MainDoorResource -> Apertura rapida della porta ... ")

        self.stato.apri()
        self.storico.aggiungi_azione(self.stato.nome_porta, "apertura")

        self.updated_state()

        misurazioni = [{"n": "stato", "vs": self.stato.stato_testo()}]
        payload_testo = crea_pacchetto_senml("main_door/", misurazioni)
        return aiocoap.Message(payload=payload_testo.encode('utf-8'))

    async def render_put(self, request):
        print("MainDoorResource -> Richiesta PUT ricevuta")

        try:
            # Il comando ricevuto dal client resta un semplice JSON
            # (non e' un dato di telemetria, ma un comando di controllo)
            payload_ricevuto = request.payload.decode('utf-8')
            dati = json.loads(payload_ricevuto)
            azione = dati.get("azione", LockCommandRequest.AZIONE_CHIUDI)

            if azione == LockCommandRequest.AZIONE_APRI:
                self.stato.apri()
                self.storico.aggiungi_azione(self.stato.nome_porta, "apertura")
                print("MainDoorResource -> Porta aperta")

            elif azione == LockCommandRequest.AZIONE_CHIUDI:
                self.stato.chiudi()
                self.storico.aggiungi_azione(self.stato.nome_porta, "chiusura")
                print("MainDoorResource -> Porta chiusa")

            else:
                print("MainDoorResource -> Azione sconosciuta:", azione)
                return aiocoap.Message(code=aiocoap.Code.BAD_REQUEST, payload=b"Azione non valida")

            self.updated_state()

            misurazioni = [{"n": "stato", "vs": self.stato.stato_testo()}]
            payload_testo = crea_pacchetto_senml("main_door/", misurazioni)
            return aiocoap.Message(payload=payload_testo.encode('utf-8'))

        except Exception as errore:
            print("MainDoorResource -> Errore:", str(errore))
            return aiocoap.Message(code=aiocoap.Code.BAD_REQUEST, payload=str(errore).encode('utf-8'))