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
├── server.py          # Server CoAP: registra i 3 Smart Object e le loro risorse
│                      #   DoorResource   -> una porta (GET, POST, PUT, Observe)
│                      #   SensorResource -> i sensori di casa (solo GET)
├── collector.py       # Data Collector & Manager: GET periodici, Observe, storico
├── client.py          # Unico client: get / post / put / observe / dashboard
├── model.py           # Gli oggetti del sistema, senza dettagli di rete:
│                      #   Lock (stato + storico), EnvironmentSensor, LockCommandRequest
├── senml.py           # Creazione e lettura dei pacchetti SenML+JSON
├── test_progetto.py   # Test automatici (modelli, sensori, SenML, collector, server CoAP)
├── requirements.txt
├── storico.json       # Creato dal collector: storico delle azioni raccolte
└── README.md
```

Il progetto è volutamente compatto: **5 file di codice**, divisi per ruolo.
`model.py` e `senml.py` non sanno niente di CoAP (sono i dati e il formato dei messaggi),
`server.py` è il lato dispositivo, `client.py` e `collector.py` il lato utente.

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

## Data Collector & Manager

Il `collector.py` è il componente centrale del sistema: non è un dispositivo, ma il programma che
tiene insieme i tre Smart Object. Va lanciato in un terzo terminale, con il server già acceso:

```bash
python3 collector.py
```

Appena parte, e senza bisogno di altri comandi:

- **interroga periodicamente (GET)** le due serrature e i sensori ambientali (ogni 15 secondi,
  valore modificabile con `INTERVALLO_GET`)
- **si sottoscrive (Observe) a tutte le serrature insieme**, quindi viene avvisato subito quando
  una porta cambia stato, anche se il comando è arrivato da un altro client
- **raccoglie e mantiene lo storico** delle azioni di ogni porta (data, ora e tipo di azione),
  salvandolo in `storico.json` così da non perderlo quando viene spento e riacceso

Mentre lavora, nello stesso terminale si possono scrivere dei comandi:

| Comando | Descrizione |
|---|---|
| `apri main` | Invia il comando di apertura (PUT) alla porta principale |
| `chiudi garage` | Invia il comando di chiusura (PUT) al garage |
| `stato` | Ultimo stato conosciuto di tutti e 3 gli Smart Object |
| `storico` | Storico delle azioni raccolto dal collector, porta per porta |
| `esci` | Ferma il collector |

Differenza con `client.py`: il client serve a mandare **una** richiesta e vedere la risposta,
il collector invece resta acceso, osserva e conserva i dati nel tempo.

---

## Test

I test automatici controllano da soli che tutto funzioni, senza dover provare i comandi a mano.
Non serve avere il server acceso: i test ne accendono uno loro sulla porta 5684, quindi si possono
lanciare anche mentre il server normale (5683) sta girando.

```bash
python3 -m unittest test_progetto -v
```

Cosa viene verificato:

| Gruppo | Controlli |
|---|---|
| `TestSerratura` | La porta parte chiusa, apri/chiudi cambiano lo stato, ogni azione finisce nello storico con data e ora, le azioni inventate vengono rifiutate |
| `TestSensori` | Presenza vero/falso (e che rilevi sia sì sia no), temperatura fra 18 e 26 °C, umidità fra 30 e 60 %, record SenML con le unità giuste (`Cel`, `%RH`) |
| `TestSenML` | Il pacchetto inizia con il nome base `bn`, lettura di una misura, stampa leggibile |
| `TestComando` | Il comando apri/chiudi viene scritto e riletto correttamente |
| `TestCollector` | Il collector legge lo stato, raccoglie le azioni senza contarle due volte (la stessa azione arriva sia dall'Observe sia dal GET periodico), le tiene in ordine di tempo e non perde lo storico al riavvio |
| `TestSistemaCoAP` | Server e client CoAP veri: GET, POST, PUT, comandi non validi rifiutati (4.00), storico in ordine di tempo, porte indipendenti fra loro, e una notifica **Observe** che arriva davvero quando un altro client apre la porta |

### Prova manuale (demo)

Per la demo dal vivo servono tre terminali, tutti con il venv attivo e nella cartella del progetto:

1. **Terminale 1** — `python3 server.py`
2. **Terminale 2** — `python3 collector.py` (mostra i GET periodici e resta in ascolto)
3. **Terminale 3** — `python3 client.py put main apri`

Nel terminale 2 deve comparire subito la riga `NOTIFICA da /main_door: porta aperta`: è la prova
che l'Observe funziona, cioè che il collector viene avvisato senza aver chiesto niente.
Scrivendo poi `storico` nel terminale 2 si vede l'azione registrata con data e ora.

Per i sensori basta `python3 client.py get sensori` (oppure `dashboard`): ogni lettura dà valori
diversi, perché il sensore di presenza e quello ambientale sono simulati.

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
