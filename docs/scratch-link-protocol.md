# Protocol de Scratch Link implementat

EduTicTac Link implementa la part del protocol de Scratch Link necessària per
als perifèrics Bluetooth Low Energy. El protocol original està documentat per
Scratch Foundation a `scratchfoundation/scratch-link` (carpeta
`Documentation/`). Ací se'n descriu la versió que implementem, reescrita.

## Transport

- **WebSocket** amb missatges **JSON-RPC 2.0** en marcs de text o binaris
  (UTF-8).
- Dos punts d'accés:
  - `/scratch/ble` — Bluetooth Low Energy (implementat)
  - `/scratch/bt` — Bluetooth Classic (implementat; vegeu la secció final)
- Una connexió = un perifèric. Per a dos perifèrics calen dos WebSockets.

## Connexió des del navegador

El client de `scratch-vm` prova dos sockets al mateix temps i fa servir el
primer que connecta:

| URL | Estat |
|---|---|
| `ws://127.0.0.1:20111/scratch/ble` | Modern, sense TLS (EduTicTac Link) |
| `wss://device-manager.scratch.mit.edu:20110/scratch/ble` | Llegat, amb TLS |

Com que EduTicTac Link atén el primer, no cal cap certificat.

## Estats de la sessió

```
initial ──discover──▶ discovery ──connect──▶ connected ──▶ (fi)
```

- **initial**: només s'accepta `discover`.
- **discovery**: s'accepten `didDiscoverPeripheral` (servidor→client) i
  `connect`.
- **connected**: s'accepten `read`, `write`, `startNotifications`,
  `stopNotifications`, `getServices`.

`getVersion` i `ping` es poden enviar en qualsevol estat.

## Mètodes

### `getVersion`

Resposta: `{"protocol": "1.3"}`.

### `ping`

Resposta: `42`. Serveix de senyal de vida.

### `discover`

Paràmetres: `filters` (llista, almenys un filtre no trivial) i
`optionalServices` (opcional).

Un filtre pot contindre:

- `name` — nom exacte;
- `namePrefix` — prefix del nom;
- `services` — tots els UUID declarats han d'estar anunciats;
- `manufacturerData` — per ID de fabricant, amb `dataPrefix` i `mask`.

Els UUID es poden donar com a enter (`0xF005`), hex curt (`"f005"`) o UUID de
128 bits. Es normalitzen a minúscules.

Resposta: `null`. A continuació s'emeten notificacions
`didDiscoverPeripheral`:

```json
{"jsonrpc":"2.0","method":"didDiscoverPeripheral",
 "params":{"peripheralId":0,"name":"BBC micro:bit","rssi":-55}}
```

### `connect`

Paràmetre: `peripheralId` (el valor rebut a `didDiscoverPeripheral`).
Resposta: `null` en cas d'èxit; si falla, `error` i la sessió continua en
estat de descobriment.

### `getServices`

Resposta: llista d'UUID de servei permesos (els de `services` i
`optionalServices` del descobriment).

### `read`

Paràmetres: `serviceId` (opcional), `characteristicId`,
`startNotifications` (opcional).

Resposta:

```json
{"message":"cG9uZw==","encoding":"base64"}
```

### `write`

Paràmetres: `serviceId` (opcional), `characteristicId`, `message`,
`encoding` (opcional; `base64` o text), `withResponse` (opcional).

Resposta: nombre de bytes escrits. Si `withResponse` no s'indica, s'escriu
sense resposta quan la característica ho suporta.

### `startNotifications` / `stopNotifications`

Paràmetres: `serviceId` (opcional), `characteristicId`.

Les notificacions del perifèric s'emeten com:

```json
{"jsonrpc":"2.0","method":"characteristicDidChange",
 "params":{"serviceId":"...","characteristicId":"...",
           "message":"cG9uZw==","encoding":"base64"}}
```

### Errors

Resposta d'error estàndard:

```json
{"jsonrpc":"2.0","id":3,"error":{"code":-32602,"message":"..."}}
```

Codis emprats: `-32600` petició invàlida, `-32601` mètode desconegut,
`-32602` paràmetres invàlids, `-32000` error de dispositiu (per exemple,
servei no permés pel descobriment o error de connexió).

## Bluetooth Classic (`/scratch/bt`)

Màquina d'estats idèntica (initial → discovery → connected), però amb mètodes
propis:

### `discover`

Paràmetres: `majorDeviceClass` i `minorDeviceClass` (classe de dispositiu
Bluetooth). Per a l'EV3: `8` i `1`. El daemon descobrix, filtra per classe i
emet `didDiscoverPeripheral`.

### `connect`

Paràmetres: `peripheralId` i, opcionalment, `pin` (PIN d'emparellament; l'EV3
fa servir `1234`).

### `send`

Paràmetres: `message`, `encoding` (com en BLE). Resposta: nombre de bytes
enviats.

### `didReceiveMessage`

Notificació del daemon cap al client quan arriben dades:

```json
{"jsonrpc":"2.0","method":"didReceiveMessage",
 "params":{"message":"cGluZw==","encoding":"base64"}}
```

**Estat:** implementat i provat amb un backend fals; el transport real
(RFCOMM/BlueZ) és experimental i pendent de validació amb maquinari.

## Seguretat del protocol

Els serveis accessibles després de connectar queden limitats als declarats al
descobriment. Qualsevol intent d'accedir a un servei no declarat es rebutja.
Vegeu [docs/security.md](security.md).
