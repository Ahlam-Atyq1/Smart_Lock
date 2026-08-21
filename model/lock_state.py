# lock_state.py
# Questa classe rappresenta lo stato di UNA serratura (aperta o chiusa).
# Non fa altro che "ricordare" se la porta e' aperta o chiusa.

class LockState:

    def __init__(self, nome_porta):
        # Il nome della porta, es. "Porta Principale" o "Garage"
        self.nome_porta = nome_porta

        # Stato iniziale: la porta parte sempre chiusa
        # True = aperta, False = chiusa
        self.aperta = False

    def apri(self):
        # Metodo semplice: imposta lo stato su "aperta"
        self.aperta = True

    def chiudi(self):
        # Metodo semplice: imposta lo stato su "chiusa"
        self.aperta = False

    def stato_testo(self):
        # Restituisce lo stato come testo leggibile, utile per stamparlo
        if self.aperta:
            return "aperta"
        else:
            return "chiusa"