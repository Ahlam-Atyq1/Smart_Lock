# coap_get_client_process.py
# Questo script chiede al server lo stato attuale di una porta
# (aperta o chiusa) e lo storico delle azioni fatte su quella porta.
# Puoi scegliere quale porta interrogare direttamente da terminale.

import sys
import asyncio
from aiocoap import *


def leggi_porta_da_terminale():
    # sys.argv[1] e' cio' che scrivi dopo il comando, es. "main" o "garage"

    if len(sys.argv) < 2:
        print("Nessuna porta scritta, uso 'main' (porta principale) come default.")
        print("(la prossima volta puoi scrivere: main oppure garage)")
        return "main_door"

    parola_scritta = sys.argv[1]

    if parola_scritta == "main":
        return "main_door"
    elif parola_scritta == "garage":
        return "garage_door"
    else:
        print("Parola non riconosciuta:", parola_scritta)
        print("Scrivi solo 'main' oppure 'garage'. Uso 'main' come default.")
        return "main_door"


async def main():
    nome_risorsa = leggi_porta_da_terminale()
    uri = "coap://127.0.0.1:5683/" + nome_risorsa

    protocollo = await Context.create_client_context()
    richiesta = Message(code=GET, uri=uri)

    print("Invio richiesta GET a:", uri)

    try:
        risposta = await protocollo.request(richiesta).response
        print("Risposta dal server:")
        print(risposta.payload.decode())
    except Exception as errore:
        print("Errore:", errore)


if __name__ == "__main__":
    asyncio.run(main())