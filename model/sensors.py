# sensors.py
# Questa classe simula i sensori installati vicino all'ingresso di casa:
# il sensore di presenza (movimento) e il sensore ambientale
# (temperatura e umidita'). In un dispositivo vero qui leggeremmo
# dei sensori fisici, per la simulazione generiamo valori casuali realistici.

import random


class EnvironmentSensor:

    def leggi_presenza(self):
        # Sensore di presenza (es. PIR): True = qualcuno rilevato
        return random.choice([True, False])

    def leggi_temperatura(self):
        # Temperatura in gradi Celsius
        return round(random.uniform(18.0, 26.0), 1)

    def leggi_umidita(self):
        # Umidita' in percentuale
        return round(random.uniform(30.0, 60.0), 1)

    def to_senml_records(self):
        # Ogni sensore diventa un record SenML, con il suo nome,
        # il suo valore e (quando ha senso) la sua unita' di misura
        return [
            {"n": "presenza", "vb": self.leggi_presenza()},
            {"n": "temperatura", "u": "Cel", "v": self.leggi_temperatura()},
            {"n": "umidita", "u": "%RH", "v": self.leggi_umidita()},
        ]
