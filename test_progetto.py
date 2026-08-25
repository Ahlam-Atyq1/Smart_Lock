# test_progetto.py
# Test automatici del progetto: controllano che tutto funzioni senza dover
# provare i comandi a mano uno per uno.
#
# Uso (dalla cartella principale, NON serve avere il server acceso:
# i test ne accendono uno loro sulla porta 5684):
#   python3 -m unittest test_progetto -v
#
# I test sono divisi in due gruppi:
#   1. i "pezzi" da soli: serratura, sensori, SenML, comando apri/chiudi, collector
#   2. il sistema intero: un vero server CoAP interrogato da un vero client
#      (GET, POST, PUT, Observe)

import asyncio
import json
import os
import tempfile
import unittest

import aiocoap
import aiocoap.resource as resource
from aiocoap import Context, Message, GET, POST, PUT

import collector
from collector import DataCollector
from model.lock import Lock
from model.senml import crea_pacchetto_senml, estrai_valore, formatta_pacchetto
from model.sensors import EnvironmentSensor
from request.lock_command_request import LockCommandRequest
from resources.door_resource import DoorResource
from resources.sensor_resource import SensorResource

# Porta diversa da quella del server vero (5683), cosi' i test si possono
# lanciare anche mentre il server normale e' acceso
INDIRIZZO_TEST = "127.0.0.1"
PORTA_TEST = 5684


# ---------------------------------------------------------------------------
# 1. Test dei singoli pezzi
# ---------------------------------------------------------------------------

class TestSerratura(unittest.TestCase):
    # Controlla la classe Lock: stato della porta e storico delle azioni

    def setUp(self):
        self.serratura = Lock("Porta Principale")

    def test_parte_chiusa_e_senza_storico(self):
        self.assertEqual(self.serratura.stato_testo(), "chiusa")
        self.assertEqual(self.serratura.azioni, [])

    def test_apri_e_chiudi_cambiano_lo_stato(self):
        self.assertTrue(self.serratura.esegui(LockCommandRequest.AZIONE_APRI))
        self.assertEqual(self.serratura.stato_testo(), "aperta")

        self.assertTrue(self.serratura.esegui(LockCommandRequest.AZIONE_CHIUDI))
        self.assertEqual(self.serratura.stato_testo(), "chiusa")

    def test_ogni_azione_finisce_nello_storico(self):
        self.serratura.esegui("apri")
        self.serratura.esegui("chiudi")

        descrizioni = [azione["azione"] for azione in self.serratura.azioni]
        self.assertEqual(descrizioni, ["apertura", "chiusura"])

        # Ogni azione deve avere il suo momento (data e ora), come chiede la traccia
        for azione in self.serratura.azioni:
            self.assertIsInstance(azione["timestamp"], float)

    def test_azione_inventata_viene_rifiutata(self):
        self.assertFalse(self.serratura.esegui("spalanca"))
        self.assertEqual(self.serratura.stato_testo(), "chiusa")
        self.assertEqual(self.serratura.azioni, [])

    def test_post_apre_sempre(self):
        self.serratura.apri()
        self.assertEqual(self.serratura.stato_testo(), "aperta")

    def test_senml_contiene_stato_e_azioni(self):
        self.serratura.esegui("apri")
        records = self.serratura.to_senml_records()

        self.assertEqual(records[0], {"n": "stato", "vs": "aperta"})
        self.assertEqual(records[1]["n"], "azione")
        self.assertEqual(records[1]["vs"], "apertura")
        self.assertIn("t", records[1])


class TestSensori(unittest.TestCase):
    # Controlla lo Smart Object dei sensori: presenza, temperatura, umidita'

    def setUp(self):
        self.sensori = EnvironmentSensor()

    def test_letture_sempre_in_un_intervallo_realistico(self):
        # I valori sono casuali: proviamo tante volte per essere sicuri
        # che non escano mai fuori dai limiti previsti
        for _ in range(200):
            self.assertIsInstance(self.sensori.leggi_presenza(), bool)

            temperatura = self.sensori.leggi_temperatura()
            self.assertGreaterEqual(temperatura, 18.0)
            self.assertLessEqual(temperatura, 26.0)

            umidita = self.sensori.leggi_umidita()
            self.assertGreaterEqual(umidita, 30.0)
            self.assertLessEqual(umidita, 60.0)

    def test_il_sensore_di_presenza_rileva_sia_si_sia_no(self):
        # Se rispondesse sempre la stessa cosa il sensore sarebbe rotto
        letture = {self.sensori.leggi_presenza() for _ in range(200)}
        self.assertEqual(letture, {True, False})

    def test_senml_dei_sensori(self):
        records = self.sensori.to_senml_records()
        nomi = [record["n"] for record in records]
        self.assertEqual(nomi, ["presenza", "temperatura", "umidita"])

        # La presenza e' un vero/falso ("vb"), gli altri due sono numeri ("v")
        # con la loro unita' di misura ("u")
        self.assertIsInstance(records[0]["vb"], bool)
        self.assertEqual(records[1]["u"], "Cel")
        self.assertEqual(records[2]["u"], "%RH")
        self.assertIsInstance(records[1]["v"], float)
        self.assertIsInstance(records[2]["v"], float)


class TestSenML(unittest.TestCase):
    # Controlla che i pacchetti SenML siano scritti e letti correttamente

    def test_il_pacchetto_inizia_con_il_nome_base(self):
        testo = crea_pacchetto_senml("main_door/", [{"n": "stato", "vs": "chiusa"}])
        pacchetto = json.loads(testo)

        self.assertEqual(pacchetto[0], {"bn": "main_door/"})
        self.assertEqual(pacchetto[1], {"n": "stato", "vs": "chiusa"})

    def test_estrai_valore(self):
        pacchetto = [{"bn": "environment_sensor/"},
                     {"n": "presenza", "vb": True},
                     {"n": "temperatura", "u": "Cel", "v": 21.5}]

        self.assertEqual(estrai_valore(pacchetto, "temperatura"), 21.5)
        self.assertEqual(estrai_valore(pacchetto, "presenza"), True)
        self.assertIsNone(estrai_valore(pacchetto, "misura_che_non_esiste"))

    def test_stampa_leggibile(self):
        righe = formatta_pacchetto([{"bn": "environment_sensor/"},
                                    {"n": "presenza", "vb": False},
                                    {"n": "temperatura", "u": "Cel", "v": 21.5},
                                    {"n": "azione", "vs": "apertura", "t": 1700000000.0}])

        self.assertIn("Dispositivo: environment_sensor/", righe[0])
        self.assertIn("presenza: no", righe[1])          # il vero/falso diventa si/no
        self.assertIn("21.5 Cel", righe[2])              # il valore ha la sua unita'
        self.assertIn("(", righe[3])                     # l'azione ha data e ora


class TestComando(unittest.TestCase):
    # Controlla il comando apri/chiudi che viaggia dal client al server

    def test_scrittura_e_lettura_del_comando(self):
        testo = LockCommandRequest("apri").to_json()
        self.assertEqual(json.loads(testo), {"azione": "apri"})
        self.assertEqual(LockCommandRequest.azione_da_json(testo), "apri")

    def test_comando_non_valido(self):
        self.assertIsNone(LockCommandRequest.azione_da_json('{"azione": "spalanca"}'))
        self.assertIsNone(LockCommandRequest.azione_da_json('{}'))


class TestCollector(unittest.TestCase):
    # Controlla il Data Collector & Manager: come raccoglie lo stato delle
    # porte e come tiene lo storico delle azioni

    def setUp(self):
        # Lo storico viene salvato in un file temporaneo, cosi' i test non
        # toccano il vero storico.json del progetto
        self.file_temporaneo = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        self.file_temporaneo.close()
        os.remove(self.file_temporaneo.name)

        self.file_originale = collector.FILE_STORICO
        collector.FILE_STORICO = self.file_temporaneo.name
        self.collector = DataCollector()

    def tearDown(self):
        collector.FILE_STORICO = self.file_originale
        if os.path.exists(self.file_temporaneo.name):
            os.remove(self.file_temporaneo.name)

    def pacchetto_porta(self, stato, azioni):
        # Costruisce un pacchetto SenML come quello che arriva da una serratura
        pacchetto = [{"bn": "main_door/"}, {"n": "stato", "vs": stato}]
        for descrizione, momento in azioni:
            pacchetto.append({"n": "azione", "vs": descrizione, "t": momento})
        return pacchetto

    def test_legge_lo_stato_e_raccoglie_le_azioni(self):
        nuove = self.collector.aggiorna(
            "main", self.pacchetto_porta("aperta", [("apertura", 1000.0)]))

        self.assertEqual(nuove, 1)
        self.assertEqual(self.collector.stato_porte["main"], "aperta")
        self.assertEqual(self.collector.storico["main"],
                         [{"azione": "apertura", "timestamp": 1000.0}])

    def test_la_stessa_azione_non_viene_contata_due_volte(self):
        # La stessa azione arriva prima con l'Observe e poi con il GET
        # periodico: nello storico deve restare una volta sola
        azioni = [("apertura", 1000.0)]
        self.collector.aggiorna("main", self.pacchetto_porta("aperta", azioni))
        nuove = self.collector.aggiorna("main", self.pacchetto_porta("aperta", azioni))

        self.assertEqual(nuove, 0)
        self.assertEqual(len(self.collector.storico["main"]), 1)

    def test_le_azioni_restano_in_ordine_di_tempo(self):
        self.collector.aggiorna("main", self.pacchetto_porta(
            "chiusa", [("apertura", 3000.0), ("chiusura", 1000.0), ("apertura", 2000.0)]))

        tempi = [azione["timestamp"] for azione in self.collector.storico["main"]]
        self.assertEqual(tempi, [1000.0, 2000.0, 3000.0])

    def test_lo_storico_non_si_perde_al_riavvio(self):
        self.collector.aggiorna(
            "main", self.pacchetto_porta("aperta", [("apertura", 1000.0)]))

        # Un secondo collector, come se fosse stato spento e riacceso
        collector_riavviato = DataCollector()
        self.assertEqual(collector_riavviato.storico["main"],
                         [{"azione": "apertura", "timestamp": 1000.0}])

    def test_storico_salvato_illeggibile(self):
        # Se il file e' rovinato il collector deve ripartire, non bloccarsi
        with open(self.file_temporaneo.name, "w", encoding="utf-8") as file_rovinato:
            file_rovinato.write("questo non e' json")

        collector_riavviato = DataCollector()
        self.assertEqual(collector_riavviato.storico, {"main": [], "garage": []})


# ---------------------------------------------------------------------------
# 2. Test del sistema intero (server CoAP + client CoAP veri)
# ---------------------------------------------------------------------------

class TestSistemaCoAP(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        # Accendiamo un server di prova con le stesse risorse di server.py
        root = resource.Site()
        root.add_resource(["main_door"], DoorResource("Porta Principale", "main_door"))
        root.add_resource(["garage_door"], DoorResource("Garage", "garage_door"))
        root.add_resource(["environment_sensor"], SensorResource("environment_sensor"))

        self.server = await Context.create_server_context(
            root, bind=(INDIRIZZO_TEST, PORTA_TEST))
        self.client = await Context.create_client_context()

    async def asyncTearDown(self):
        await self.client.shutdown()
        await self.server.shutdown()

    def uri(self, risorsa):
        return f"coap://{INDIRIZZO_TEST}:{PORTA_TEST}/{risorsa}"

    async def richiesta(self, risorsa, codice=GET, payload=b""):
        messaggio = Message(code=codice, uri=self.uri(risorsa), payload=payload)
        return await self.client.request(messaggio).response

    async def pacchetto(self, risorsa, codice=GET, payload=b""):
        risposta = await self.richiesta(risorsa, codice, payload)
        return json.loads(risposta.payload.decode())

    # ----- interrogazione (GET) -------------------------------------------

    async def test_get_porta_restituisce_lo_stato(self):
        pacchetto = await self.pacchetto("main_door")
        self.assertEqual(pacchetto[0], {"bn": "main_door/"})
        self.assertEqual(estrai_valore(pacchetto, "stato"), "chiusa")

    async def test_get_sensori_restituisce_le_tre_misure(self):
        pacchetto = await self.pacchetto("environment_sensor")

        self.assertEqual(pacchetto[0], {"bn": "environment_sensor/"})
        self.assertIsInstance(estrai_valore(pacchetto, "presenza"), bool)
        self.assertGreaterEqual(estrai_valore(pacchetto, "temperatura"), 18.0)
        self.assertLessEqual(estrai_valore(pacchetto, "temperatura"), 26.0)
        self.assertGreaterEqual(estrai_valore(pacchetto, "umidita"), 30.0)
        self.assertLessEqual(estrai_valore(pacchetto, "umidita"), 60.0)

    async def test_i_sensori_non_rispondono_ai_comandi(self):
        # Lo Smart Object dei sensori e' solo un sensore: niente PUT
        risposta = await self.richiesta("environment_sensor", PUT, b'{"azione": "apri"}')
        self.assertFalse(risposta.code.is_successful())

    # ----- comandi (PUT / POST) -------------------------------------------

    async def test_put_apre_e_chiude_la_porta(self):
        comando = LockCommandRequest("apri").to_json().encode("utf-8")
        pacchetto = await self.pacchetto("main_door", PUT, comando)
        self.assertEqual(estrai_valore(pacchetto, "stato"), "aperta")

        comando = LockCommandRequest("chiudi").to_json().encode("utf-8")
        pacchetto = await self.pacchetto("main_door", PUT, comando)
        self.assertEqual(estrai_valore(pacchetto, "stato"), "chiusa")

    async def test_post_apre_subito(self):
        pacchetto = await self.pacchetto("garage_door", POST)
        self.assertEqual(estrai_valore(pacchetto, "stato"), "aperta")

    async def test_comando_non_valido_viene_rifiutato(self):
        risposta = await self.richiesta("main_door", PUT, b'{"azione": "spalanca"}')
        self.assertEqual(risposta.code, aiocoap.Code.BAD_REQUEST)

        risposta = await self.richiesta("main_door", PUT, b"non sono json")
        self.assertEqual(risposta.code, aiocoap.Code.BAD_REQUEST)

    async def test_le_due_porte_sono_indipendenti(self):
        await self.richiesta("garage_door", POST)                  # apre il garage

        pacchetto = await self.pacchetto("main_door")
        self.assertEqual(estrai_valore(pacchetto, "stato"), "chiusa")

    # ----- storico ---------------------------------------------------------

    async def test_lo_storico_si_riempie_con_le_azioni(self):
        for azione in ("apri", "chiudi", "apri"):
            comando = LockCommandRequest(azione).to_json().encode("utf-8")
            await self.richiesta("main_door", PUT, comando)

        pacchetto = await self.pacchetto("main_door")
        azioni = [misura for misura in pacchetto if misura.get("n") == "azione"]

        self.assertEqual([azione["vs"] for azione in azioni],
                         ["apertura", "chiusura", "apertura"])
        # Le azioni devono essere in ordine di tempo
        tempi = [azione["t"] for azione in azioni]
        self.assertEqual(tempi, sorted(tempi))

    # ----- sottoscrizione (Observe) ---------------------------------------

    async def test_observe_avvisa_quando_la_porta_cambia(self):
        richiesta_osservata = self.client.request(
            Message(code=GET, uri=self.uri("main_door"), observe=0))

        prima_risposta = await richiesta_osservata.response
        self.assertEqual(estrai_valore(json.loads(prima_risposta.payload.decode()), "stato"),
                         "chiusa")

        notifiche = []

        async def resta_in_ascolto():
            async for aggiornamento in richiesta_osservata.observation:
                notifiche.append(json.loads(aggiornamento.payload.decode()))
                return

        ascolto = asyncio.ensure_future(resta_in_ascolto())
        await asyncio.sleep(0.1)      # diamo tempo alla sottoscrizione di attivarsi

        # Un altro client apre la porta: chi osserva deve essere avvisato da solo
        await self.richiesta("main_door", PUT,
                             LockCommandRequest("apri").to_json().encode("utf-8"))

        try:
            await asyncio.wait_for(ascolto, timeout=5)
        finally:
            richiesta_osservata.observation.cancel()

        self.assertEqual(len(notifiche), 1)
        self.assertEqual(estrai_valore(notifiche[0], "stato"), "aperta")


if __name__ == "__main__":
    unittest.main(verbosity=2)
