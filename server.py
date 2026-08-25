# server.py
# Questo file avvia il server CoAP e registra i tre Smart Object:
# la porta principale, il garage e i sensori (presenza + ambiente).

import asyncio

import aiocoap
import aiocoap.resource as resource

from resources.door_resource import DoorResource
from resources.sensor_resource import SensorResource

INDIRIZZO = "127.0.0.1"
PORTA = 5683

# Le serrature del progetto: percorso CoAP -> nome leggibile.
# Per aggiungere una porta nuova basta scrivere una riga qui.
PORTE = {
    "main_door": "Porta Principale",
    "garage_door": "Garage",
}

SENSORI = "environment_sensor"


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
