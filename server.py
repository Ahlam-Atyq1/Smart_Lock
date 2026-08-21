# server.py
# Questo file avvia il server CoAP e registra le due serrature
# (porta principale e garage) come risorse raggiungibili dai client.

import asyncio
import aiocoap
import aiocoap.resource as resource

from resources.main_door_resource import MainDoorResource
from resources.garage_door_resource import GarageDoorResource
from resources.environment_sensor_resource import EnvironmentSensorResource
from resources.presence_sensor_resource import PresenceSensorResource


async def main():
    # 1. Creiamo il "sito", cioe' il contenitore di tutte le risorse del server
    root = resource.Site()

    # 2. Colleghiamo ogni indirizzo (path) alla risorsa corrispondente
    #    Esempio: quando un client chiama coap://.../main_door, viene usata MainDoorResource
    root.add_resource(['main_door'], MainDoorResource())
    root.add_resource(['garage_door'], GarageDoorResource())
    root.add_resource(['environment_sensor'], EnvironmentSensorResource())
    root.add_resource(['presece_sensor'], PresenceSensorResource())


    # 3. Avviamo il server sulla porta standard CoAP (5683)
    print("Server CoAP avviato su coap://127.0.0.1:5683")
    print("Risorse disponibili: /main_door  /garage_door  /environment_sensor /presence_sensor")
    await aiocoap.Context.create_server_context(root, bind=('127.0.0.1', 5683))

    # 4. Manteniamo il server sempre acceso, in attesa di richieste
    #    (un anno di attesa, tanto per dire "per sempre")
    un_anno_in_secondi = 60 * 60 * 24 * 365
    await asyncio.sleep(un_anno_in_secondi)


# Punto di ingresso del programma: se eseguo "python server.py", parte da qui
if __name__ == "__main__":
    asyncio.run(main())