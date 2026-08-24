# sensor_resource.py
# Questa classe rappresenta il terzo Smart Object: un dispositivo indipendente
# che contiene il Sensore di Presenza e il Sensore Ambientale.
# A differenza delle serrature, questo Smart Object e' SOLO un sensore:
# risponde solo a GET (nessun comando da eseguire, nessun PUT/POST).
#
# I dati vengono restituiti in formato SenML+JSON, come richiesto per
# tutti i messaggi di telemetria.

import aiocoap
import aiocoap.resource as resource

from model.sensors import EnvironmentSensor
from model.senml import crea_pacchetto_senml


class SensorResource(resource.Resource):

    def __init__(self, nome_risorsa="environment_sensor"):
        super().__init__()
        self.sensori = EnvironmentSensor()
        self.nome_risorsa = nome_risorsa

    async def render_get(self, request):
        print(f"{self.nome_risorsa} -> Richiesta GET ricevuta, lettura sensori in SenML ...")

        payload_testo = crea_pacchetto_senml(self.nome_risorsa + "/",
                                             self.sensori.to_senml_records())
        return aiocoap.Message(payload=payload_testo.encode('utf-8'))
