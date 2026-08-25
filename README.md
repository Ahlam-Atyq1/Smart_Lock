# Smart Lock IoT — Controllo remoto delle serrature via CoAP

Sistema IoT per il controllo a distanza delle serrature di casa (porta principale e garage),
basato sul protocollo di comunicazione **CoAP** (Constrained Application Protocol).

Permette di:
- Verificare se una porta è aperta o chiusa
- Aprire o chiudere una porta a distanza
- Ricevere notifiche in tempo reale quando lo stato di una porta cambia (Observe)
- Consultare lo storico di tutte le azioni effettuate (apertura/chiusura, con data e ora)
- Leggere i sensori di casa (presenza, temperatura, umidità)

Tutti i dati di telemetria viaggiano in formato **SenML+JSON**.

---

## Struttura del progetto

```
Smart_Lock/
├── server.py                     # Avvia il server CoAP e registra i 3 Smart Object
├── client.py                     # Unico client: get / post / put / observe / dashboard
├── model/
│   ├── lock.py                   # Una serratura: stato (aperta/chiusa) + storico azioni
│   ├── sensors.py                # Sensori simulati: presenza, temperatura, umidità
│   └── senml.py                  # Creazione e lettura dei pacchetti SenML+JSON
├── request/
│   └── lock_command_request.py   # Il comando apri/chiudi (scrittura e lettura)
├── resources/
│   ├── door_resource.py          # Risorsa CoAP di una porta (usata per main e garage)
│   └── sensor_resource.py        # Risorsa CoAP dei sensori (solo GET)
├── requirements.txt
└── README.md
```

I tre Smart Object del sistema sono:

| Risorsa CoAP           | Cosa rappresenta       | Metodi supportati        |
|------------------------|------------------------|--------------------------|
| `/main_door`           | Porta principale       | GET, POST, PUT, Observe  |
| `/garage_door`         | Garage                 | GET, POST, PUT, Observe  |
| `/environment_sensor`  | Sensori di casa        | GET                      |

Le due porte usano **la stessa classe** (`DoorResource`), creata due volte con un nome diverso:
per aggiungere una terza serratura basta aggiungere una riga al dizionario `PORTE` in `server.py`.

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

Il server si mette in ascolto su `coap://127.0.0.1:5683`.
Lascia il server acceso in questo terminale mentre usi il client da un altro terminale.

---

## Utilizzo del client

Aprire un secondo terminale, attivare il venv e lanciare i comandi (sempre dalla cartella principale):

| Comando | Descrizione |
|---|---|
| `python3 client.py get main` | Stato attuale e storico della porta principale |
| `python3 client.py get garage` | Stato attuale e storico del garage |
| `python3 client.py get sensori` | Presenza, temperatura e umidità |
| `python3 client.py post main` | Apre subito la porta (comando rapido) |
| `python3 client.py put main apri` | Apre la porta principale |
| `python3 client.py put garage chiudi` | Chiude il garage |
| `python3 client.py observe garage` | Resta in ascolto e avvisa in tempo reale se lo stato cambia |
| `python3 client.py dashboard` | Tabella riassuntiva con tutti e 3 gli Smart Object |

La porta si scrive dopo il comando (`main` o `garage`); se non viene scritta niente viene usata
`main` come default. Lo stesso vale per l'azione del `put` (default: `apri`).

---

## Perché CoAP

CoAP è un protocollo pensato per dispositivi IoT con risorse limitate (poca memoria, poca energia,
rete non sempre stabile). Rispetto ad HTTP, usa messaggi più leggeri e si appoggia su UDP invece
di TCP, risultando più adatto a scenari con molti piccoli dispositivi connessi. Supporta inoltre
in modo nativo il meccanismo di **Observe**, che permette a un client di ricevere notifiche
automatiche quando una risorsa cambia stato, senza dover interrogare continuamente il server.

---

## Possibili estensioni future

- Supporto a un numero arbitrario di serrature (n porte), aggiungendo righe al dizionario `PORTE`
- Autenticazione (PIN o token) per l'apertura da remoto
- Interfaccia grafica (app mobile o web) al posto del client da terminale
