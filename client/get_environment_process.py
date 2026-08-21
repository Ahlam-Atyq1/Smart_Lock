# coap_get_environment_client_process.py
# Questo script chiede al server i dati letti dallo Smart Object Sensori
# Ambientali: se c'e' presenza rilevata, la temperatura e l'umidita'.

import asyncio
from aiocoap import *

uri = "coap://127.0.0.1:5683/environment_sensor"


async def main():
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