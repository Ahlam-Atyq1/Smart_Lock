# environment_sensor.py
# Questa classe simula un sensore ambientale: legge temperatura e umidita'
# della zona in cui si trova (es. vicino all'ingresso di casa).

import random


class EnvironmentSensor:

    def leggi_temperatura(self):
        # In un dispositivo vero, qui leggeremmo un sensore fisico di temperatura.
        # Per la simulazione, generiamo un valore casuale realistico (in gradi Celsius).
        temperatura = random.uniform(18.0, 26.0)
        return round(temperatura, 1)

    def leggi_umidita(self):
        # Stessa idea, ma per l'umidita' (in percentuale).
        umidita = random.uniform(30.0, 60.0)
        return round(umidita, 1)