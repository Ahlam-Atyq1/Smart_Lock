# collector.py
# Data Collector & Manager del sistema.
# E' il componente centrale descritto nella proposta di progetto: non e' un
# dispositivo, ma il "cervello" che tiene insieme i tre Smart Object.
#
# Cosa fa, tutto insieme e in contemporanea:
#   - interroga periodicamente (GET) le due serrature e i sensori ambientali
#   - resta sottoscritto (Observe) alle serrature, cosi' sa subito quando una
#     porta viene aperta o chiusa, senza dover chiedere di continuo
#   - manda i comandi di apertura/chiusura (PUT) alle serrature
#   - raccoglie e mantiene lo storico delle azioni di ogni porta
#     (data, ora e tipo di azione), salvandolo su file
#
# Uso (con il server acceso, da un secondo terminale):
#   python3 collector.py
#
# Mentre il collector lavora si possono scrivere dei comandi nello stesso
# terminale:
#   apri main | chiudi garage | stato | storico | esci

import asyncio
import json
import os
from datetime import datetime

from aiocoap import Context, Message, GET, PUT

from senml import estrai_valore, valore_di
from model import LockCommandRequest

SERVER = "coap://127.0.0.1:5683"

# Le serrature seguite dal collector: nome breve -> risorsa sul server.
# Come in server.py, per seguire una porta in piu' basta aggiungere una riga.
PORTE = {
    "main": "main_door",
    "garage": "garage_door",
}

SENSORI = "environment_sensor"

# Ogni quanti secondi vengono rifatte le interrogazioni periodiche (GET)
INTERVALLO_GET = 15

# File in cui lo storico viene salvato, cosi' non si perde quando il
# collector viene spento e riacceso
FILE_STORICO = "storico.json"


def ora_attuale():
    return datetime.now().strftime("%H:%M:%S")


def data_e_ora(timestamp):
    # Il timestamp SenML e' un numero di secondi: lo mostriamo come data/ora
    return datetime.fromtimestamp(timestamp).strftime("%d/%m/%Y %H:%M:%S")


class DataCollector:

    def __init__(self):
        # Ultimo stato conosciuto di ogni porta (aperta / chiusa)
        self.stato_porte = {nome: "sconosciuto" for nome in PORTE}

        # Ultima lettura dei sensori ambientali
        self.sensori = {"presenza": None, "temperatura": None, "umidita": None}

        # Storico delle azioni, una lista per ogni porta
        self.storico = self._carica_storico()

    # ----- storico delle azioni ------------------------------------------

    def _carica_storico(self):
        # Se esiste gia' un file salvato lo riprendiamo, altrimenti si parte
        # con una lista vuota per ogni porta
        salvato = {}
        if os.path.exists(FILE_STORICO):
            try:
                with open(FILE_STORICO, encoding="utf-8") as file_storico:
                    salvato = json.load(file_storico)
                print(f"Storico precedente caricato da {FILE_STORICO}")
            except ValueError:
                print(f"{FILE_STORICO} illeggibile: riparto con uno storico vuoto.")

        return {nome: salvato.get(nome, []) for nome in PORTE}

    def _salva_storico(self):
        with open(FILE_STORICO, "w", encoding="utf-8") as file_storico:
            json.dump(self.storico, file_storico, ensure_ascii=False, indent=2)

    def aggiorna(self, nome_breve, pacchetto):
        # Legge un pacchetto SenML arrivato da una serratura (per GET o per
        # Observe): aggiorna lo stato attuale e aggiunge allo storico solo le
        # azioni che il collector non aveva ancora registrato.
        stato = estrai_valore(pacchetto, "stato")
        if stato is not None:
            self.stato_porte[nome_breve] = stato

        gia_registrate = {(azione["timestamp"], azione["azione"])
                          for azione in self.storico[nome_breve]}
        nuove = 0

        for misura in pacchetto:
            if misura.get("n") != "azione":
                continue

            evento = {"azione": valore_di(misura), "timestamp": misura.get("t")}
            if (evento["timestamp"], evento["azione"]) in gia_registrate:
                continue

            self.storico[nome_breve].append(evento)
            gia_registrate.add((evento["timestamp"], evento["azione"]))
            nuove += 1

        if nuove:
            self.storico[nome_breve].sort(key=lambda evento: evento["timestamp"])
            self._salva_storico()

        return nuove

    # ----- comunicazione con il server CoAP -------------------------------

    async def leggi(self, protocollo, percorso):
        # Una singola richiesta GET, che restituisce il pacchetto SenML letto
        richiesta = Message(code=GET, uri=f"{SERVER}/{percorso}")
        risposta = await protocollo.request(richiesta).response
        return json.loads(risposta.payload.decode())

    async def interrogazione_periodica(self, protocollo):
        # Interrogazione periodica (GET) di tutti e tre gli Smart Object
        while True:
            try:
                for nome_breve, percorso in PORTE.items():
                    self.aggiorna(nome_breve, await self.leggi(protocollo, percorso))

                pacchetto_sensori = await self.leggi(protocollo, SENSORI)
                for nome_misura in self.sensori:
                    self.sensori[nome_misura] = estrai_valore(pacchetto_sensori, nome_misura)

                print(f"[{ora_attuale()}] GET periodico: " + self.riga_riassunto())
            except Exception as errore:
                print(f"[{ora_attuale()}] Server non raggiungibile ({errore}), riprovo ...")

            await asyncio.sleep(INTERVALLO_GET)

    async def sottoscrivi(self, protocollo, nome_breve):
        # Sottoscrizione (Observe) a una serratura: la prima risposta e' lo
        # stato attuale, poi gli aggiornamenti arrivano da soli appena il
        # sensore di apertura/chiusura rileva un cambiamento.
        percorso = PORTE[nome_breve]
        richiesta = protocollo.request(Message(code=GET, uri=f"{SERVER}/{percorso}", observe=0))

        prima_risposta = await richiesta.response
        self.aggiorna(nome_breve, json.loads(prima_risposta.payload.decode()))
        print(f"[{ora_attuale()}] Observe attivo su /{percorso} "
              f"(stato: {self.stato_porte[nome_breve]})")

        async for aggiornamento in richiesta.observation:
            self.aggiorna(nome_breve, json.loads(aggiornamento.payload.decode()))
            print(f"[{ora_attuale()}] NOTIFICA da /{percorso}: "
                  f"porta {self.stato_porte[nome_breve]}")

    async def invia_comando(self, protocollo, nome_breve, azione):
        # Invio del comando di apertura o chiusura all'attuatore serratura
        comando = LockCommandRequest(azione)
        richiesta = Message(code=PUT,
                            uri=f"{SERVER}/{PORTE[nome_breve]}",
                            payload=comando.to_json().encode("utf-8"))

        risposta = await protocollo.request(richiesta).response
        if not risposta.code.is_successful():
            print(f"Comando rifiutato dal server: {risposta.payload.decode()}")
            return

        self.aggiorna(nome_breve, json.loads(risposta.payload.decode()))
        print(f"[{ora_attuale()}] Comando '{azione}' inviato a /{PORTE[nome_breve]}: "
              f"porta {self.stato_porte[nome_breve]}")

    # ----- stampe a video --------------------------------------------------

    def riga_riassunto(self):
        porte = "  ".join(f"{nome}={stato}" for nome, stato in self.stato_porte.items())
        presenza = self.sensori["presenza"]
        return (f"{porte}  presenza={'si' if presenza else 'no'}  "
                f"temp={self.sensori['temperatura']}C  "
                f"umidita={self.sensori['umidita']}%")

    def stampa_stato(self):
        print("=" * 70)
        print(f"{'Smart Object':<22}{'Stato':<12}{'Azioni raccolte'}")
        print("=" * 70)
        for nome_breve in PORTE:
            print(f"{PORTE[nome_breve]:<22}{self.stato_porte[nome_breve]:<12}"
                  f"{len(self.storico[nome_breve])}")
        presenza = self.sensori["presenza"]
        print(f"{SENSORI:<22}presenza={'si' if presenza else 'no'}  "
              f"temperatura={self.sensori['temperatura']} C  "
              f"umidita={self.sensori['umidita']} %")
        print("=" * 70)

    def stampa_storico(self):
        for nome_breve, percorso in PORTE.items():
            print(f"\nStorico di /{percorso}:")
            if not self.storico[nome_breve]:
                print("  (nessuna azione registrata)")
                continue

            for evento in self.storico[nome_breve]:
                print(f"  - {data_e_ora(evento['timestamp'])}  {evento['azione']}")


# ---------------------------------------------------------------------------
# Comandi scritti da terminale mentre il collector lavora
# ---------------------------------------------------------------------------

ISTRUZIONI = """Comandi disponibili (scrivili qui e premi INVIO):
  apri <porta>     apre una porta      (es. apri main)
  chiudi <porta>   chiude una porta    (es. chiudi garage)
  stato            mostra l'ultimo stato conosciuto di tutti gli Smart Object
  storico          mostra lo storico delle azioni raccolto dal collector
  esci             ferma il collector
"""


async def console_comandi(collector, protocollo):
    print(ISTRUZIONI)

    while True:
        # input() blocca: lo eseguiamo in un thread a parte, cosi' le
        # interrogazioni periodiche e le notifiche Observe continuano
        try:
            riga = await asyncio.to_thread(input, "")
        except EOFError:
            # Nessuno sta scrivendo (per esempio il collector e' stato lanciato
            # in background): restano comunque attivi i GET periodici e le
            # sottoscrizioni Observe, si ferma con CTRL+C.
            print("Nessun comando da terminale: resto in ascolto (CTRL+C per fermare).")
            await asyncio.get_running_loop().create_future()

        parole = riga.strip().lower().split()
        if not parole:
            continue

        comando = parole[0]
        if comando == "esci":
            return
        if comando == "stato":
            collector.stampa_stato()
        elif comando == "storico":
            collector.stampa_storico()
        elif comando in LockCommandRequest.AZIONI_VALIDE:
            nome_breve = parole[1] if len(parole) > 1 else "main"
            if nome_breve not in PORTE:
                print(f"Porta '{nome_breve}' sconosciuta (scrivi: {' | '.join(PORTE)}).")
                continue
            await collector.invia_comando(protocollo, nome_breve, comando)
        else:
            print(f"Comando '{comando}' non riconosciuto.")
            print(ISTRUZIONI)


async def main():
    collector = DataCollector()
    protocollo = await Context.create_client_context()

    print(f"Data Collector & Manager avviato, server: {SERVER}")
    print(f"Interrogazione periodica ogni {INTERVALLO_GET} secondi, "
          f"Observe su: /" + "  /".join(PORTE.values()) + "\n")

    # Tutti i lavori del collector girano insieme: le sottoscrizioni Observe,
    # le interrogazioni periodiche e la console dei comandi.
    lavori = [asyncio.ensure_future(collector.sottoscrivi(protocollo, nome))
              for nome in PORTE]
    lavori.append(asyncio.ensure_future(collector.interrogazione_periodica(protocollo)))

    try:
        # Il collector resta acceso finche' la console non riceve "esci"
        await console_comandi(collector, protocollo)
    finally:
        # Prima fermiamo i lavori in corso e aspettiamo che siano davvero
        # chiusi, poi spegniamo la connessione CoAP: altrimenti aiocoap
        # protesta perche' ci sono ancora richieste Observe aperte.
        for lavoro in lavori:
            lavoro.cancel()
        await asyncio.gather(*lavori, return_exceptions=True)
        await protocollo.shutdown()
        print("Collector fermato.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nCollector fermato.")
