# Investigació prèvia — EduTicTac Link

Data: 2026-09-27. Fonts consultades directament (codi i documentació oficial).

## 1. Protocol de Scratch 3 ↔ Scratch Link

- **JSON-RPC 2.0 sobre WebSocket**, amb dos punts d'accés separats:
  - `/scratch/ble` → Bluetooth Low Energy (GATT)
  - `/scratch/bt`  → Bluetooth Classic (RFCOMM/SPP)
- Documentat per Scratch Foundation a `scratchfoundation/scratch-link`,
  carpeta `Documentation/` (`NetworkProtocol.md`, `BluetoothLE.md`,
  `Bluetooth.md`).
- Màquina d'estats per connexió: **initial → discover → discovery →
  connect → connected**. Una connexió = un perifèric.
- Mètodes: `getVersion`, `discover`, `connect`, `getServices`, `read`,
  `write` (amb `withResponse`), `startNotifications`, `stopNotifications`.
- Notificacions del daemon cap al client: `didDiscoverPeripheral`,
  `characteristicDidChange`. En BT: `didReceiveMessage`.
- El client pot enviar `ping`; el client de scratch-vm respon `42`.
- Les dades binàries viatgen en base64 (`{"message": "...", "encoding":
  "base64"}`).

### Com connecta el navegador (scratch-vm)

`src/util/scratch-link-websocket.js` obri **dos sockets alhora** i guanya el
primer que connecta:

| Socket | URL |
|---|---|
| Modern (sense TLS) | `ws://127.0.0.1:20111/scratch/ble` |
| Llegat (amb TLS) | `wss://device-manager.scratch.mit.edu:20110/scratch/ble` |

La contrasenya de 15 s del socket es considera error només si tots dos fallen.
Si el modern funciona, no cal cap certificat.

### Filtres de descobriment (`discover.params`)

`filters` (almenys un filtre no trivial) i `optionalServices` opcional. Un
filtre conté una o més condicions; el perifèric ha de complir **totes** les
condicions d'algun filtre.

- `name` (coincidència exacta), `namePrefix` (prefix)
- `services` (tots els UUID declarats han d'estar anunciats)
- `manufacturerData` (per ID de fabricant, amb `dataPrefix`/`mask`)

Els noms de servei poden ser UUID complets, IDs curts (0xXXXX) o noms de la
taula assignada per Bluetooth. Web Bluetooth `resolveUuidName`.

## 2. Estat de pyscrlink

`kawasaki/pyscrlink` — **BSD-3-Clause**, 127 estrelles, 34 forks, darrer push
**2023-09**, 16 issues obertes, 2 PR oberts. Un únic fitxer
`pyscrlink/scratch_link.py` (23 KB).

### Què implementa del protocol

`/scratch/ble` i `/scratch/bt` (buit), estats initial/discovery/connected,
`discover` (només filtres `services` i `namePrefix`), `connect`, `read`,
`write`, `startNotifications`, `stopNotifications`, notificacions
`didDiscoverPeripheral` i `characteristicDidChange`. **No** implementa
`getVersion`, `getServices`, ni els filtres `name`/`manufacturerData`
(aquest últim el necessita LEGO Boost).

### Problemes amb Python modern

1. **`bluepy`** (release 2018-12-03, sense manteniment). En Python 3.12+ falla
   la instal·lació per la retirada de `distutils` (PEP 632) i perquè empaqueta
   un BlueZ 5.47 antic i compila `bluepy-helper`.
2. Requereix `bluepy_helper_cap` + `setcap cap_net_raw,cap_net_admin` manual
   sobre `bluepy-helper` (cal root una volta).
3. **API de `websockets` antiga**: fa `websockets.serve(...)` fora del bucle i
   després `run_until_complete` → `RuntimeError: no running event loop` amb
   `websockets>=11/12` (issues #43 i #45). La signatura del manegador
   `ws_handler(websocket, path)` també és obsoleta.
4. Serveix **només WSS al port 20110** amb un certificat autogenerat que
   s'ha d'instal·lar als NSS DB de Firefox i Chrome (`gencert.py`), i cal
   que `device-manager.scratch.mit.edu` resolga a 127.0.0.1.
5. Coincidència de notificacions fràgil: escriu el descriptor CCCD a
   `handle + 1`, suposant que sempre és el handle següent.
6. **Bluetooth Classic (EV3) eliminat** des de la v0.2.6 (pybluez no es
   manté).

### Dependències

`requirements.txt`: `websockets`, `bluepy`, `pybluez` (**obsolet**),
`pyOpenSSL`. `setup.py`: `websockets`, `bluepy`, `pyOpenSSL`.

### Forks i PRs

- `deric/pyscrlink`, branca `bleak` (PR #44 obert): canvia bluepy per bleak i
  afig Intelino. No fusionat.
- PR #46 de `fpuga` (obert): correccions per a Ubuntu 24.04 / Python 3.13.
- `FrankFirsching/pyscrlink` (2024): còpia sense canvis propis.

**Cap fork està mantingut ni fusionat a l'original.**

## 3. Dispositius i transport

| Dispositiu | Transport | Filtre de descobriment principal |
|---|---|---|
| micro:bit | BLE | `services: [0xf005]`; RX `5261da01-…`, TX `5261da02-…` |
| LEGO WeDo 2.0 | BLE | `services: [00001523-1212-efde-1523-785feabcd123]`, optional `00004f0e-…` |
| LEGO Boost | BLE | `services: [00001623-…]` + `manufacturerData 0x0397` |
| LEGO EV3 | **Bluetooth Classic** | `majorDeviceClass 8`, `minorDeviceClass 1`, PIN `1234` |
| SPIKE Prime | — | no hi ha extensió a scratch-vm |
| Vernier Go Direct | BLE | `namePrefix: 'GDX-FOR'` |

El micro:bit necessita el firmware de Scratch
(`scratchfoundation/scratch-microbit-firmware`); el flasheig no és
responsabilitat del daemon.

**Conclusió important:** el daemon és **genèric de transport**. Les extensions
de scratch-vm construeixen els comandaments concrets de cada dispositiu; el
daemon només fa GATT (descobrir/connectar/llegir/escriure/notificar) i
coincidència de filtres. Per això `devices/` són perfils d'identificació i
diagnòstic, no controladors de protocol.

## 4. Navegadors

- La via daemon (WebSocket) funciona a **Firefox i Chromium**.
- **Web Bluetooth**: Chrome/Edge sí; Firefox i Safari no. Context segur +
  gestió d'usuari.
- **Web Serial**: Chrome/Edge sí; Safari no. Firefox 151+ segons caniuse.
- Una extensió TurboWarp amb Web Bluetooth **ha de ser unsandboxed**, i les
  carregades per URL només corren unsandboxed des de
  `https://extensions.turbowarp.org/` o `http://localhost:8000/` exactes. Una
  instància pròpia (p. ex. EduTicTac Blocs) pot modificar la seua llista
  blanca.

## 5. Llicències

| Projecte | Llicència | Ús a EduTicTac Link |
|---|---|---|
| pyscrlink | BSD-3-Clause | Referència/adaptació amb atribució |
| scratch-link | AGPL-3.0 | Només la documentació del protocol |
| scratch-vm | AGPL-3.0 | Consulta del client i dels filtres |
| bleak | MIT | Dependència |
| websockets | BSD-3-Clause | Dependència |
| click | BSD-3-Clause | Dependència |
| pybluez | GPL-2.0 (abandonat) | **No s'usa** |

## Bibliografia

- https://github.com/scratchfoundation/scratch-link
- https://github.com/kawasaki/pyscrlink
- https://github.com/deric/pyscrlink/tree/bleak
- https://github.com/scratchfoundation/scratch-vm
- https://docs.turbowarp.org/development/extensions/unsandboxed
- https://github.com/hbldh/bleak
- https://caniuse.com/web-bluetooth · https://caniuse.com/web-serial
