# presence_sensor.py
# Questa classe simula un sensore di presenza: rileva se c'e' movimento
# nell'area monitorata (es. vicino all'ingresso di casa).

import random


class PresenceSensor:

    def leggi_presenza(self):
        # In un dispositivo vero, qui leggeremmo un sensore fisico (es. PIR).
        # Per la simulazione, scegliamo a caso True (presenza rilevata)
        # o False (nessuna presenza), cosi' ogni richiesta puo' dare un risultato diverso.
        return random.choice([True, False])