# coap_dashboard_client_process.py
# Questo script interroga tutti e 3 gli Smart Object (porta principale,
# garage, sensori ambientali) e mostra i dati ricevuti (in formato
# SenML+JSON) in una tabella ordinata e leggibile.

import asyncio
import json
from aiocoap import *

from model.senml_encoder import estrai_valore

# Indirizzi dei 3 Smart Object
URI_MAIN_DOOR = "coap://127.0.0.1:5683/main_door"
URI_GARAGE_DOOR = "coap://127.0.0.1:5683/garage_door"
URI_ENVIRONMENT = "coap://127.0.0.1:5683/environment_sensor"


async def leggi_risorsa(protocollo, uri):
    # Manda una richiesta GET e restituisce il pacchetto SenML ricevuto
    # (una lista di dizionari), gia' convertito da testo JSON a dati Python
    richiesta = Message(code=GET, uri=uri)
    risposta = await protocollo.request(richiesta).response
    testo_ricevuto = risposta.payload.decode()
    return json.loads(testo_ricevuto)


async def main():
    protocollo = await Context.create_client_context()

    print("Lettura dati (SenML+JSON) dai 3 Smart Object in corso ...\n")

    pacchetto_porta_principale = await leggi_risorsa(protocollo, URI_MAIN_DOOR)
    pacchetto_garage = await leggi_risorsa(protocollo, URI_GARAGE_DOOR)
    pacchetto_ambiente = await leggi_risorsa(protocollo, URI_ENVIRONMENT)

    # Estraiamo i singoli valori che ci interessano da ogni pacchetto SenML
    stato_porta = estrai_valore(pacchetto_porta_principale, "stato")
    stato_garage = estrai_valore(pacchetto_garage, "stato")
    presenza = estrai_valore(pacchetto_ambiente, "presenza")
    temperatura = estrai_valore(pacchetto_ambiente, "temperatura")
    umidita = estrai_valore(pacchetto_ambiente, "umidita")

    presenza_testo = "si" if presenza else "no"

    # ---------------------------------------------------------
    # Tabella ordinata con tutti i dati
    # ---------------------------------------------------------
    print("=" * 70)
    print(f"{'Smart Object':<22}{'Stato':<10}{'Presenza':<12}{'Temp (C)':<10}{'Umidita (%)'}")
    print("=" * 70)
    print(f"{'Porta Principale':<22}{stato_porta:<10}{'-':<12}{'-':<10}{'-'}")
    print(f"{'Garage':<22}{stato_garage:<10}{'-':<12}{'-':<10}{'-'}")
    print(f"{'Sensori Ambientali':<22}{'-':<10}{presenza_testo:<12}{str(temperatura):<10}{str(umidita)}")
    print("=" * 70)

    # ---------------------------------------------------------
    # I pacchetti SenML "grezzi", cosi' come arrivano dal server
    # ---------------------------------------------------------
    print("\nPacchetti SenML+JSON ricevuti dal server:\n")
    print("main_door:", json.dumps(pacchetto_porta_principale, ensure_ascii=False))
    print("garage_door:", json.dumps(pacchetto_garage, ensure_ascii=False))
    print("environment_sensor:", json.dumps(pacchetto_ambiente, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())