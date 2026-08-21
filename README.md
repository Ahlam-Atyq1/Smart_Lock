# Smart Lock IoT — Controllo remoto delle serrature via CoAP

Sistema IoT per il controllo a distanza delle serrature di casa (porta principale e garage),
basato sul protocollo di comunicazione **CoAP** (Constrained Application Protocol).

Permette di:
- Verificare se una porta è aperta o chiusa
- Aprire o chiudere una porta a distanza
- Ricevere notifiche in tempo reale quando lo stato di una porta cambia (Observe)
- Consultare lo storico di tutte le azioni effettuate (apertura/chiusura, con data e ora)

---

## Struttura del progetto

```
smart_lock_IoT/
├── server.py                              # Avvia il server CoAP
├── client/
│   ├── coap_get_client_process.py         # Legge stato + storico di una porta
│   ├── coap_post_client_process.py        # Apertura rapida (comando semplice)
│   ├── coap_put_client_process.py         # Apri/chiudi a scelta (apri | chiudi)
│   └── coap_observing_client_process.py   # Ascolto in tempo reale (Observe)
├── model/
│   ├── lock_state.py                      # Stato di una serratura (aperta/chiusa)
│   └── lock_history.py                    # Storico delle azioni effettuate
├── request/
│   └── lock_command_request.py            # Descrive il comando apri/chiudi
├── resources/
│   ├── main_door_resource.py              # Risorsa CoAP: porta principale
│   └── garage_door_resource.py            # Risorsa CoAP: garage
├── requirements.txt
└── README.md
```

---

## Requisiti

- Python 3.9 o superiore
- Libreria `aiocoap` (vedi `requirements.txt`)

---

## Installazione

1. Crea l'ambiente virtuale (solo la prima volta):
   ```bash
   python3 -m venv venv
   ```

2. Attiva l'ambiente virtuale:
   ```bash
   source venv/bin/activate        # Mac / Linux
   venv\Scripts\activate           # Windows
   ```

3. Installa le dipendenze:
   ```bash
   pip install -r requirements.txt
   ```

---

## Avvio del server

Dalla cartella principale del progetto:

```bash
python3 server.py
```

Il server si mette in ascolto su `coap://127.0.0.1:5683` ed espone due risorse:
- `/main_door` — porta principale
- `/garage_door` — garage

Lascia il server acceso in questo terminale mentre usi i client da un altro terminale.

---

## Utilizzo dei client

Aprire un secondo terminale, attivare il venv e lanciare i comandi (sempre dalla cartella principale):

| Comando | Descrizione |
|---|---|
| `python3 -m client.coap_get_client_process` | Legge lo stato attuale e lo storico della porta principale |
| `python3 -m client.coap_post_client_process` | Apre subito la porta (comando rapido) |
| `python3 -m client.coap_put_client_process apri` | Apre la porta |
| `python3 -m client.coap_put_client_process chiudi` | Chiude la porta |
| `python3 -m client.coap_observing_client_process` | Resta in ascolto e avvisa in tempo reale se lo stato cambia |

Per default i client puntano alla porta principale (`/main_door`). Per usare il garage, modificare
la variabile `uri` in cima al file scelto, sostituendo `/main_door` con `/garage_door`.

---

## Perché CoAP

CoAP è un protocollo pensato per dispositivi IoT con risorse limitate (poca memoria, poca energia,
rete non sempre stabile). Rispetto ad HTTP, usa messaggi più leggeri e si appoggia su UDP invece
di TCP, risultando più adatto a scenari con molti piccoli dispositivi connessi. Supporta inoltre
in modo nativo il meccanismo di **Observe**, che permette a un client di ricevere notifiche
automatiche quando una risorsa cambia stato, senza dover interrogare continuamente il server.

---

## Possibili estensioni future

- Supporto a un numero arbitrario di serrature (n porte), aggiungendo nuove risorse nel server
- Autenticazione (PIN o token) per l'apertura da remoto
- Interfaccia grafica (app mobile o web) al posto dei client da terminale# Smart_Lock
