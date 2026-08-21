# coap_put_client_process.py
# Questo script manda un comando preciso al server: apri OPPURE chiudi,
# su una porta a scelta (main_door o garage_door).
# Sia la porta che l'azione si scrivono direttamente da terminale.

import sys
import asyncio
from aiocoap import *

from request.lock_command_request import LockCommandRequest


def leggi_porta_da_terminale():
    # Il primo argomento scritto dopo il comando (sys.argv[1]) e' la porta

    if len(sys.argv) < 2:
        print("Nessuna porta scritta, uso 'main' (porta principale) come default.")
        return "main_door"

    parola_scritta = sys.argv[1]

    if parola_scritta == "main":
        return "main_door"
    elif parola_scritta == "garage":
        return "garage_door"
    else:
        print("Porta non riconosciuta:", parola_scritta, "-> uso 'main' come default.")
        return "main_door"


def leggi_azione_da_terminale():
    # Il secondo argomento (sys.argv[2]) e' l'azione: apri oppure chiudi

    if len(sys.argv) < 3:
        print("Nessuna azione scritta, uso 'apri' come default.")
        return LockCommandRequest.AZIONE_APRI

    parola_scritta = sys.argv[2]

    if parola_scritta == "apri":
        return LockCommandRequest.AZIONE_APRI
    elif parola_scritta == "chiudi":
        return LockCommandRequest.AZIONE_CHIUDI
    else:
        print("Azione non riconosciuta:", parola_scritta, "-> uso 'apri' come default.")
        return LockCommandRequest.AZIONE_APRI


async def main():
    nome_risorsa = leggi_porta_da_terminale()
    azione_da_fare = leggi_azione_da_terminale()
    uri = "coap://127.0.0.1:5683/" + nome_risorsa

    protocollo = await Context.create_client_context()

    comando = LockCommandRequest(azione_da_fare)
    payload_da_inviare = comando.to_json()

    richiesta = Message(code=PUT, uri=uri, payload=payload_da_inviare.encode('utf-8'))

    print("Invio richiesta PUT a:", uri)
    print("Azione richiesta:", azione_da_fare)

    try:
        risposta = await protocollo.request(richiesta).response
        print("Risposta dal server:")
        print(risposta.payload.decode())
    except Exception as errore:
        print("Errore:", errore)


if __name__ == "__main__":
    asyncio.run(main())