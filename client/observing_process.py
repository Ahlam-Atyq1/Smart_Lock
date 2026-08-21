# coap_observing_client_process.py
# Questo script resta "in ascolto" di una porta: ogni volta che lo stato
# cambia (qualcuno apre o chiude), il server ci avvisa subito da solo,
# senza bisogno di richiedere continuamente lo stato (GET).

import asyncio
from aiocoap import *

# Cambia questo indirizzo per scegliere quale porta osservare:
# - porta principale -> coap://127.0.0.1:5683/main_door
# - garage           -> coap://127.0.0.1:5683/garage_door
uri = "coap://127.0.0.1:5683/garage_door"


async def main():
    protocollo = await Context.create_client_context()

    # observe=0 dice al server: "avvisami ogni volta che qualcosa cambia"
    richiesta = Message(code=GET, uri=uri, observe=0)

    print("In ascolto sulla porta:", uri)
    print("Premi CTRL+C per fermare ... ")

    # request(...) restituisce un oggetto che ci da' sia la prima risposta
    # sia tutti gli aggiornamenti futuri, dentro observation
    richiesta_osservata = protocollo.request(richiesta)

    try:
        # Prima risposta (stato attuale)
        prima_risposta = await richiesta_osservata.response
        print("Stato iniziale:")
        print(prima_risposta.payload.decode())

        # Ogni volta che il server manda un aggiornamento, lo stampiamo
        async for aggiornamento in richiesta_osservata.observation:
            print("\nAggiornamento ricevuto:")
            print(aggiornamento.payload.decode())

    except Exception as errore:
        print("Errore:", errore)


if __name__ == "__main__":
    asyncio.run(main())