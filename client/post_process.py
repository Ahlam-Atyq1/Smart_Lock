# coap_post_client_process.py
# Questo script manda un comando veloce al server: "apri la porta".
# Il POST non richiede di specificare nulla, apre sempre la porta.

import asyncio
from aiocoap import *

# Cambia questo indirizzo per scegliere quale porta aprire:
# - porta principale -> coap://127.0.0.1:5683/main_door
# - garage           -> coap://127.0.0.1:5683/garage_door
uri = "coap://127.0.0.1:5683/main_door"


async def main():
    protocollo = await Context.create_client_context()

    richiesta = Message(code=POST, uri=uri)

    print("Invio richiesta POST (apertura rapida) a:", uri)

    try:
        risposta = await protocollo.request(richiesta).response
        print("Risposta dal server:")
        print(risposta.payload.decode())
    except Exception as errore:
        print("Errore:", errore)


if __name__ == "__main__":
    asyncio.run(main())