# Arquitectura d'EduTicTac Link

## Visió general

```
Scratch 3 / TurboWarp / EduTicTac Blocs
        │  WebSocket (JSON-RPC 2.0)
        ▼
┌──────────────────────────────────────────────┐
│                EduTicTac Link                 │
│                                              │
│  server/    WebSocket + validació d'origen   │
│  protocol/  JSON-RPC i màquina d'estats      │
│  bluetooth/ backend BLE (bleak) + filtres    │
│  serial/    (fase 2: Bluetooth Classic)      │
│  devices/   perfils d'identificació          │
│  doctor     comprovacions de l'entorn        │
└──────────────────────┬───────────────────────┘
                       │ BlueZ (D-Bus)
                       ▼
                  adaptador BLE  ──▶  micro:bit / WeDo 2.0 / Boost
```

## Idea clau: nucli genèric de transport

El daemon **no** implementa els comandaments de cada dispositiu. Les
extensions estàndard de Scratch (`scratch3_microbit`, `scratch3_wedo2`,
`scratch3_boost`) ja construeixen els bytes concrets i els envien pel
protocol. EduTicTac Link només ha de:

1. **Descobrir** perifèrics i filtrar-los (servei, nom, prefix, dades de
   fabricant).
2. **Connectar** i exposar GATT: llegir, escriure i notificar
   característiques.
3. **Traduir** eixes operacions a missatges JSON-RPC.

Per això el paquet `devices/` **no** són controladors: són perfils
d'identificació, diagnòstic i fixtures de test. Vegeu
[docs/decisions.md](decisions.md) (D-009).

## Mòduls

| Mòdul | Responsabilitat |
|---|---|
| `config.py` | Configuració i lectura de variables d'entorn |
| `protocol/jsonrpc.py` | Construcció i anàlisi de missatges JSON-RPC 2.0 |
| `protocol/session.py` | Màquina d'estats d'una connexió (discover/connect/…) |
| `bluetooth/backend.py` | Interfície abstracció `BleBackend`/`BleConnection` |
| `bluetooth/bleak_backend.py` | Implementació real amb `bleak` |
| `bluetooth/fake_backend.py` | Implementació falsa per a tests |
| `bluetooth/filters.py` | Resolució d'UUID i coincidència de filtres |
| `bluetooth/models.py` | `Peripheral` i `Advertisement` |
| `devices/` | Perfils micro:bit, WeDo 2.0, Boost |
| `server/app.py` | Servidor WebSocket i adaptació del transport |
| `server/origin.py` | Validació de la capçalera `Origin` |
| `doctor.py` | Comprovacions de l'entorn |
| `cli/main.py` | Ordes `run`, `status`, `devices`, `doctor` |

## Flux d'una sessió

1. El navegador obri dos sockets en paral·lel:
   `ws://127.0.0.1:20111/scratch/ble` i el llegat `wss://…:20110`.
   EduTicTac Link atén el primer; el segon no és necessari.
2. El client envia `getVersion` (opcional) i `discover` amb els filtres de
   l'extensió.
3. El backend escaneja amb `bleak`, es filtren els resultats i s'emeten
   notificacions `didDiscoverPeripheral`.
4. El client envia `connect`; s'obri la connexió GATT.
5. `read`/`write`/`startNotifications`/`stopNotifications` es tradueixen a
   operacions GATT. Les notificacions es reenvien com
   `characteristicDidChange`.

## Concurrència

Cada connexió WebSocket crea una `Session` independent amb:

- un **bucle receptor** (llegeix i atén peticions);
- un **fil d'eixida** (una cua `asyncio.Queue` que serialitza els enviaments,
  de manera que respostes i notificacions no es creuen);
- una **tasca de descobriment** en segon pla que cancel·la en connectar.

## Configuració

| Variable | Per defecte | Descripció |
|---|---|---|
| `EDUTICTAC_LINK_HOST` | `127.0.0.1` | Adreça d'escolta |
| `EDUTICTAC_LINK_PORT` | `20111` | Port modern |
| `EDUTICTAC_LINK_SCAN_SECONDS` | `10` | Duració de cada escaneig |
| `EDUTICTAC_LINK_DISCOVER_TIMEOUT` | `15` | Reservat |
| `EDUTICTAC_LINK_ENFORCE_ORIGIN` | `1` | Valida la capçalera `Origin` |
| `EDUTICTAC_LINK_ALLOW_MISSING_ORIGIN` | `1` | Permet clients natius sense origen |
| `EDUTICTAC_LINK_ALLOW_ORIGINS` | llista | Orígens permesos, separats per comes |
| `EDUTICTAC_LINK_DEBUG` | `0` | Missatges de depuració |

## Decisions

Vegeu [docs/decisions.md](decisions.md) per al registre complet (D-001…D-010).
