# client.py
# Unico client CoAP del progetto: prima erano 6 script quasi identici,
# adesso c'e' un solo comando con cinque azioni possibili.
#
# Uso (dalla cartella principale, con il server acceso):
#   python3 client.py get [main|garage|sensori]      stato + storico (o lettura sensori)
#   python3 client.py post [main|garage]             apertura rapida
#   python3 client.py put  [main|garage] [apri|chiudi]
#   python3 client.py observe [main|garage]          ascolto in tempo reale
#   python3 client.py dashboard                      tabella con tutti gli Smart Object

import asyncio
import json
import sys

from aiocoap import Context, Message, GET, POST, PUT

from model.senml import estrai_valore, formatta_pacchetto
from request.lock_command_request import LockCommandRequest

SERVER = "coap://127.0.0.1:5683"

# Nome breve scritto da terminale -> nome della risorsa sul server
RISORSE = {
    "main": "main_door",
    "garage": "garage_door",
    "sensori": "environment_sensor",
}

PORTE = ("main", "garage")


# ---------------------------------------------------------------------------
# Lettura di cio' che l'utente scrive da terminale
# ---------------------------------------------------------------------------

def leggi_argomento(posizione, ammessi, default):
    # sys.argv[0] e' "client.py", sys.argv[1] e' il comando (get, put, ...),
    # quindi gli argomenti veri e propri partono da sys.argv[2].
    if len(sys.argv) <= posizione:
        print(f"Niente scritto, uso '{default}' come default.")
        return default

    parola_scritta = sys.argv[posizione]
    if parola_scritta in ammessi:
        return parola_scritta

    print(f"'{parola_scritta}' non riconosciuto (scrivi: {' | '.join(ammessi)}).",
          f"Uso '{default}' come default.")
    return default


def uri_di(nome_breve):
    return f"{SERVER}/{RISORSE[nome_breve]}"


# ---------------------------------------------------------------------------
# Invio delle richieste e stampa delle risposte
# ---------------------------------------------------------------------------

async def chiedi(protocollo, uri, codice=GET, payload=b""):
    # Manda una richiesta e restituisce il testo della risposta
    richiesta = Message(code=codice, uri=uri, payload=payload)
    risposta = await protocollo.request(richiesta).response
    return risposta.payload.decode()


def mostra(testo_risposta):
    # Stampa il pacchetto SenML in modo leggibile, piu' il JSON grezzo
    try:
        pacchetto = json.loads(testo_risposta)
    except ValueError:
        print(testo_risposta)
        return

    for riga in formatta_pacchetto(pacchetto):
        print(riga)
    print("SenML grezzo:", testo_risposta)


# ---------------------------------------------------------------------------
# I cinque comandi
# ---------------------------------------------------------------------------

async def comando_get(protocollo):
    uri = uri_di(leggi_argomento(2, list(RISORSE), "main"))
    print("Invio richiesta GET a:", uri)
    mostra(await chiedi(protocollo, uri))


async def comando_post(protocollo):
    # Il POST non richiede di specificare nulla, apre sempre la porta
    uri = uri_di(leggi_argomento(2, PORTE, "main"))
    print("Invio richiesta POST (apertura rapida) a:", uri)
    mostra(await chiedi(protocollo, uri, POST))


async def comando_put(protocollo):
    uri = uri_di(leggi_argomento(2, PORTE, "main"))
    azione = leggi_argomento(3, LockCommandRequest.AZIONI_VALIDE,
                             LockCommandRequest.AZIONE_APRI)

    comando = LockCommandRequest(azione)
    print(f"Invio richiesta PUT a: {uri}  (azione: {azione})")
    mostra(await chiedi(protocollo, uri, PUT, comando.to_json().encode('utf-8')))


async def comando_observe(protocollo):
    # observe=0 dice al server: "avvisami ogni volta che qualcosa cambia",
    # cosi' non serve richiedere continuamente lo stato con dei GET.
    uri = uri_di(leggi_argomento(2, PORTE, "main"))
    print("In ascolto su:", uri)
    print("Premi CTRL+C per fermare ...")

    richiesta_osservata = protocollo.request(Message(code=GET, uri=uri, observe=0))

    # La prima risposta e' lo stato attuale
    prima_risposta = await richiesta_osservata.response
    print("\nStato iniziale:")
    mostra(prima_risposta.payload.decode())

    # Poi arrivano da soli tutti gli aggiornamenti
    async for aggiornamento in richiesta_osservata.observation:
        print("\nAggiornamento ricevuto:")
        mostra(aggiornamento.payload.decode())


async def comando_dashboard(protocollo):
    # Interroga tutti e 3 gli Smart Object e mostra i dati in una tabella
    print("Lettura dati (SenML+JSON) dai 3 Smart Object in corso ...\n")

    pacchetti = {}
    for nome_breve in RISORSE:
        testo = await chiedi(protocollo, uri_di(nome_breve))
        pacchetti[nome_breve] = json.loads(testo)

    presenza = estrai_valore(pacchetti["sensori"], "presenza")

    righe = [
        ("Porta Principale", estrai_valore(pacchetti["main"], "stato"), "-", "-", "-"),
        ("Garage", estrai_valore(pacchetti["garage"], "stato"), "-", "-", "-"),
        ("Sensori Ambientali", "-",
         "si" if presenza else "no",
         estrai_valore(pacchetti["sensori"], "temperatura"),
         estrai_valore(pacchetti["sensori"], "umidita")),
    ]

    print("=" * 70)
    print(f"{'Smart Object':<22}{'Stato':<10}{'Presenza':<12}{'Temp (C)':<10}{'Umidita (%)'}")
    print("=" * 70)
    for nome, stato, presenza_testo, temperatura, umidita in righe:
        print(f"{nome:<22}{str(stato):<10}{presenza_testo:<12}{str(temperatura):<10}{umidita}")
    print("=" * 70)

    print("\nPacchetti SenML+JSON ricevuti dal server:\n")
    for nome_breve, pacchetto in pacchetti.items():
        print(f"{RISORSE[nome_breve]}: {json.dumps(pacchetto, ensure_ascii=False)}")


COMANDI = {
    "get": comando_get,
    "post": comando_post,
    "put": comando_put,
    "observe": comando_observe,
    "dashboard": comando_dashboard,
}


async def main():
    nome_comando = sys.argv[1] if len(sys.argv) > 1 else ""

    if nome_comando not in COMANDI:
        print(__doc__ or "")
        print("Comando non riconosciuto. Comandi disponibili:", ", ".join(COMANDI))
        print("Esempio:  python3 client.py put garage chiudi")
        return

    protocollo = await Context.create_client_context()

    try:
        await COMANDI[nome_comando](protocollo)
    except Exception as errore:
        print("Errore:", errore)
    finally:
        await protocollo.shutdown()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nInterrotto.")
