# environment_sensor_resource.py
# Questa classe rappresenta il terzo Smart Object: un dispositivo indipendente
# che contiene il Sensore di Presenza e il Sensore Ambientale.
# A differenza delle serrature, questo Smart Object e' SOLO un sensore:
# risponde solo a GET (nessun comando da eseguire, nessun PUT/POST).
#
# I dati vengono restituiti in formato SenML+JSON, come richiesto per
# tutti i messaggi di telemetria.

import aiocoap.resource as resource
import aiocoap

from model.presence_sensor import PresenceSensor
from model.senml_encoder import crea_pacchetto_senml


class EnvironmentSensorResource(resource.Resource):

    def __init__(self):
        super().__init__()
        self.sensore_presenza = PresenceSensor()

    async def render_get(self, request):
        print("EnvironmentSensorResource -> Richiesta GET ricevuta")
        print("EnvironmentSensorResource -> Lettura sensori in formato SenML ... ")

        presenza_rilevata = self.sensore_presenza.leggi_presenza()
        # Ogni sensore diventa un record SenML, con il suo nome,
        # il suo valore, e (quando ha senso) la sua unita' di misura
        misurazioni = [
            {"n": "presenza", "vb": presenza_rilevata},
        ]

        payload_testo = crea_pacchetto_senml("environment_sensor/", misurazioni)
        return aiocoap.Message(payload=payload_testo.encode('utf-8'))