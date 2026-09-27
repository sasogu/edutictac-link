# Extensió experimental de TurboWarp

**Esbós del primer cicle. No forma part del daemon i no substitueix
EduTicTac Link.**

## Què és

Una via complementària per connectar maquinari educatiu directament des de
TurboWarp, sense daemon local, fent servir **Web Bluetooth** (i en el futur
**Web Serial**).

```
TurboWarp ──Web Bluetooth/Web Serial──▶ hardware
```

## Limitacions (importants)

- **Només Chromium/Edge.** Web Bluetooth i Web Serial no estan disponibles a
  Firefox ni Safari. Esta via no substituïx el daemon, que funciona a tots
  dos.
- **Ha de ser unsandboxed.** Les extensions carregades per URL només corren
  sense sandbox des de `https://extensions.turbowarp.org/` o
  `http://localhost:8000/` exactes. Per a servir-la des de
  `blocs.edutictac.es` cal modificar la llista blanca en el fork
  EduTicTac Blocs (que ja té el modal d'extensions personalitzades) o
  carregar-la des d'un fitxer amb la casella «sense sandbox».
- **Sense escaneig automàtic.** Web Bluetooth requerix un gest d'usuari i
  mostra el seu propi selector de dispositius; no replica l'experiència de
  descobriment de Scratch Link.
- **Cobertura per protocol:**
  - micro:bit, WeDo 2.0, Boost, SPIKE Prime → BLE GATT → Web Bluetooth.
  - EV3 → Bluetooth Classic → **no** per Web Bluetooth; possible per Web
    Serial si el sistema exposa el port SPP (`/dev/rfcomm0`).

## Fitxers

- `edutictac-link-bluetooth.js` — esbós d'extensió unsandboxed amb blocs per
  comprovar la disponibilitat de Web Bluetooth i connectar amb un micro:bit.

## Provar-ho

1. Serveix el fitxer per HTTP en `localhost:8000`:
   ```bash
   cd turbowarp-extension
   python3 -m http.server 8000
   ```
2. Obri TurboWarp (o EduTicTac Blocs) amb l'extensió:
   `http://localhost:8000/edutictac-link-bluetooth.js`.
3. Comprova el bloc «Web Bluetooth disponible?» i el de connexió.

## Estat

Experimental. L'objectiu del primer cicle és només documentar la viabilitat i
deixar un punt de partida. La integració real a EduTicTac Blocs i el suport
complet de blocs és treball de fases posteriors (vegeu
`docs/roadmap.md`).
