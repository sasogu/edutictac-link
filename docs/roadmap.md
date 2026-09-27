# Full de ruta

## Estat del primer cicle (0.1.0)

### Què funciona

- Servidor WebSocket compatible amb Scratch Link a
  `ws://127.0.0.1:20111/scratch/ble`.
- Protocol JSON-RPC 2.0: `getVersion`, `ping`, `discover`, `connect`,
  `getServices`, `read`, `write`, `startNotifications`, `stopNotifications`,
  notificació `characteristicDidChange`.
- Bluetooth Low Energy amb `bleak` (BlueZ/D-Bus).
- Coincidència de filtres: `services`, `name`, `namePrefix`,
  `manufacturerData`.
- Perfils de micro:bit, WeDo 2.0 i Boost.
- Ordes `run`, `status`, `devices`, `doctor`.
- Servei d'usuari systemd.
- 34 tests automàtics amb backend BLE fals.

### Què no funciona encara

- **Bluetooth Classic (EV3)**: implementat i provat amb un backend fals; el
  transport real (RFCOMM/BlueZ) és **experimental i pendent de validació amb
  un EV3**.
- **WSS llegat (:20110)**: no s'ofereix; el socket modern és suficient.
- **Extensió de TurboWarp**: només esquisit i documentació.

### Blocatges tècnics

- **Validació amb maquinari real**: depén de tindre a mà un micro:bit, un
  WeDo 2.0 o un Boost. Els tests cobreixen el protocol amb un backend fals,
  però no el comportament real de BlueZ amb cada dispositiu.
- **Firmware del micro:bit**: cal gravar-lo fora del daemon.

### Següent pas immediat

1. Provar amb un micro:bit real: gravar el firmware, arrancar el daemon i
   connectar des de TurboWarp amb el navegador. Guia:
   [docs/validation.md](validation.md).
2. ~~Publicar el `.deb` a `packages.edutictac.es`~~ **Fet (2026-09-27)**:
   `edutictac-link_0.1.0_all.deb`, signat, a `https://packages.edutictac.es`.
3. Escriure la documentació de contribució. **Fet**: `CONTRIBUTING.md`.

### Enduriment del nucli (0.1.2)

- Detecció de desconnexió inesperada del perifèric: es tanca el socket perquè
  el navegador mostre «s'ha perdut la connexió».
- Temps d'espera a les operacions GATT (`EDUTICTAC_LINK_OPERATION_TIMEOUT`).
- Errors de dispositiu unificats (codi `-32000`).

## Fases següents

### Fase 2 — Bluetooth Classic (EV3) — implementada (experimental)

- Transport RFCOMM amb `socket.AF_BLUETOOTH` + descobriment amb `bluetoothctl`.
- Descobriment per classe de dispositiu i `connect` amb PIN.
- Tests amb un backend fals (`FakeBtBackend`).
- **Pendent:** validar amb un EV3 real i, si cal, refinar l'emparellament i la
  detecció del canal SPP.

### Fase 3 — Empaquetat i distribució

- ~~Publicar a `packages.edutictac.es`~~ **Fet (2026-09-27)**.
- Integració opcional a l'instal·lador d'EduTicTac Commons.

### Fase 4 — Extensió TurboWarp (complementària) — micro:bit fet

- **Fet (0.2.0)**: extensió unsandboxed amb Web Bluetooth per a **micro:bit**
  (`turbowarp-extension/`), amb protocol testejat amb Node (7 tests).
- Integració a EduTicTac Blocs documentada (la galeria local `extensions/` ja és
  de confiança; només cal vendorejar el fitxer i carregar-lo amb `?extension=`).
- **Pendent**: WeDo 2.0 / Boost / SPIKE per Web Bluetooth, Web Serial
  (micro:bit USB; EV3 per SPP) i provar-ho en un navegador real.
- Només Chromium; no substitueix el daemon.

### Fase 5 — Més dispositius

- Vernier Go Direct (perfil ja possible).
- Altres dispositius BLE educatius.
- Suport de noms simbòlics de servei (taula de números assignats).
