# server.py
# Questo file avvia il server CoAP e registra i tre Smart Object:
# la porta principale, il garage e i sensori (presenza + ambiente).
#
# Contiene anche le due risorse CoAP del sistema:
# - DoorResource   -> una serratura (GET, POST, PUT, Observe)
# - SensorResource -> i sensori di casa (solo GET)

import asyncio

import aiocoap
import aiocoap.resource as resource

from model import EnvironmentSensor, Lock, LockCommandRequest
from senml import crea_pacchetto_senml

INDIRIZZO = "127.0.0.1"
PORTA = 5683

# Le serrature del progetto: percorso CoAP -> nome leggibile.
# Per aggiungere una porta nuova basta scrivere una riga qui.
PORTE = {
    "main_door": "Porta Principale",
    "garage_door": "Garage",
}

SENSORI = "environment_sensor"


# ---------------------------------------------------------------------------
# Risorse CoAP
# ---------------------------------------------------------------------------

class DoorResource(resource.ObservableResource):
    # Rappresenta UNA serratura sul server. La stessa classe viene usata sia
    # per la porta principale sia per il garage: basta crearla con un nome
    # diverso. Risponde alle richieste che arrivano dal client:
    # - GET  -> restituisce stato e storico, in formato SenML+JSON
    # - POST -> apre subito la porta (comando veloce, senza specificare nulla)
    # - PUT  -> apre o chiude la porta, in base a cosa scrive il client
    # Essendo "ObservableResource", puo' anche avvisare da sola i client
    # che stanno osservando la porta (Observe), quando lo stato cambia.

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


class SensorResource(resource.Resource):
    # Il terzo Smart Object: un dispositivo indipendente che contiene il
    # Sensore di Presenza e il Sensore Ambientale. A differenza delle
    # serrature questo Smart Object e' SOLO un sensore: risponde solo a GET
    # (nessun comando da eseguire, nessun PUT/POST).

    def __init__(self, nome_risorsa=SENSORI):
        super().__init__()
        self.sensori = EnvironmentSensor()
        self.nome_risorsa = nome_risorsa

    async def render_get(self, request):
        print(f"{self.nome_risorsa} -> Richiesta GET ricevuta, lettura sensori in SenML ...")

        payload_testo = crea_pacchetto_senml(self.nome_risorsa + "/",
                                             self.sensori.to_senml_records())
        return aiocoap.Message(payload=payload_testo.encode('utf-8'))


# ---------------------------------------------------------------------------
# Avvio del server
# ---------------------------------------------------------------------------

async def main():
    # 1. Creiamo il "sito", cioe' il contenitore di tutte le risorse del server
    root = resource.Site()

    # 2. Colleghiamo ogni indirizzo (path) alla risorsa corrispondente
    #    Esempio: quando un client chiama coap://.../main_door, viene usata
    #    una DoorResource creata con il nome "Porta Principale"
    for percorso, nome_porta in PORTE.items():
        root.add_resource([percorso], DoorResource(nome_porta, percorso))

    root.add_resource([SENSORI], SensorResource(SENSORI))

    # 3. Avviamo il server sulla porta standard CoAP (5683)
    await aiocoap.Context.create_server_context(root, bind=(INDIRIZZO, PORTA))

    print(f"Server CoAP avviato su coap://{INDIRIZZO}:{PORTA}")
    print("Risorse disponibili: /" + "  /".join(list(PORTE) + [SENSORI]))

    # 4. Manteniamo il server sempre acceso, in attesa di richieste
    await asyncio.get_running_loop().create_future()


# Punto di ingresso del programma: se eseguo "python3 server.py", parte da qui
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nServer fermato.")
