# garage_door_resource.py
# Questa classe rappresenta la serratura del GARAGE sul server.
# E' identica a MainDoorResource, solo che gestisce la porta del garage.

import aiocoap.resource as resource
import aiocoap
import json

from model.lock_state import LockState
from model.lock_history import LockHistory
from request.lock_command_request import LockCommandRequest
from model.senml_encoder import crea_pacchetto_senml


class GarageDoorResource(resource.ObservableResource):

    def __init__(self):
        super().__init__()
        self.stato = LockState("Garage")
        self.storico = LockHistory()

    async def render_get(self, request):
        print("GarageDoorResource -> Richiesta GET ricevuta")
        print("GarageDoorResource -> Invio stato e storico in formato SenML ... ")

        misurazioni = [{"n": "stato", "vs": self.stato.stato_testo()}]
        misurazioni.extend(self.storico.to_senml_records())

        payload_testo = crea_pacchetto_senml("garage_door/", misurazioni)
        return aiocoap.Message(payload=payload_testo.encode('utf-8'))

    async def render_post(self, request):
        print("GarageDoorResource -> Richiesta POST ricevuta")
        print("GarageDoorResource -> Apertura rapida della porta ... ")

        self.stato.apri()
        self.storico.aggiungi_azione(self.stato.nome_porta, "apertura")

        self.updated_state()

        misurazioni = [{"n": "stato", "vs": self.stato.stato_testo()}]
        payload_testo = crea_pacchetto_senml("garage_door/", misurazioni)
        return aiocoap.Message(payload=payload_testo.encode('utf-8'))

    async def render_put(self, request):
        print("GarageDoorResource -> Richiesta PUT ricevuta")

        try:
            payload_ricevuto = request.payload.decode('utf-8')
            dati = json.loads(payload_ricevuto)
            azione = dati.get("azione", LockCommandRequest.AZIONE_CHIUDI)

            if azione == LockCommandRequest.AZIONE_APRI:
                self.stato.apri()
                self.storico.aggiungi_azione(self.stato.nome_porta, "apertura")
                print("GarageDoorResource -> Porta aperta")

            elif azione == LockCommandRequest.AZIONE_CHIUDI:
                self.stato.chiudi()
                self.storico.aggiungi_azione(self.stato.nome_porta, "chiusura")
                print("GarageDoorResource -> Porta chiusa")

            else:
                print("GarageDoorResource -> Azione sconosciuta:", azione)
                return aiocoap.Message(code=aiocoap.Code.BAD_REQUEST, payload=b"Azione non valida")

            self.updated_state()

            misurazioni = [{"n": "stato", "vs": self.stato.stato_testo()}]
            payload_testo = crea_pacchetto_senml("garage_door/", misurazioni)
            return aiocoap.Message(payload=payload_testo.encode('utf-8'))

        except Exception as errore:
            print("GarageDoorResource -> Errore:", str(errore))
            return aiocoap.Message(code=aiocoap.Code.BAD_REQUEST, payload=str(errore).encode('utf-8'))