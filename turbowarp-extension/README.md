# Extensió experimental de TurboWarp / EduTicTac Blocs

**Esbós avançat. No forma part del daemon i no el substitueix.**

Conecta un **micro:bit** amb Web Bluetooth directament des del navegador,
sense daemon local.

```
TurboWarp / Blocs ──Web Bluetooth──▶ micro:bit
```

## Què funciona

- micro:bit (amb el firmware de Scratch) via **Web Bluetooth**.
- Blocs: connectar/desconnectar, inclinació X/Y, botons A/B, pins tàctils 0/1/2,
  gestos (moure's/sacsejar-se/saltar), mostrar text, mostrar matriu 5×5 i netejar
  la pantalla.
- El protocol (encoding de comandes i parseig de notificacions) està en funcions
  pures, **testejades amb Node** (7 tests).

## Límits (importants)

- **Només Chromium/Edge.** Firefox i Safari no tenen Web Bluetooth. La via del
  **daemon EduTicTac Link** funciona a tots dos: és la via recomanada.
- **Ha de córrer sense sandbox.** Les extensions carregades per URL només són
  unsandboxed des de `https://extensions.turbowarp.org/` o
  `http://localhost:8000/` exactes. **A EduTicTac Blocs, la galeria local
  `extensions/` ja és de confiança** (vegeu la integració).
- **Sense escaneig automàtic.** Web Bluetooth exigix un gest d'usuari i mostra
  el seu propi selector. Cal executar el bloc «connecta el micro:bit» amb un
  clic; no replica el descobriment automàtic de Scratch Link.
- **Només micro:bit.** WeDo 2.0 / Boost / EV3 no estan implementats en esta
  extensió (els cobrix el daemon, excepte EV3 que hi és experimental).
- **Pocs blocs.** No hi ha temperatura/llum (el firmware de Scratch no els envia).
  WeDo 2.0 / Boost / SPIKE no es fan (LEGO els ha descatalogats i no hi ha
  maquinari per a provar-los); el protocol de micro:bit està complet.

## Blocs

- **Esdeveniments**: `quan es prem el botó [A/B]`, `quan [s'ha mogut/sacsejat/saltat]`, `quan s'inclina [any/amunt/avall/esquerra/dreta]`, `quan el pin [0/1/2] es toca`
- `connecta el micro:bit` · `desconnecta el micro:bit` · `connectat?` · `nom del micro:bit`
- `inclinació X` · `inclinació Y` · `està inclinat [direcció]?`
- `botó [A/B] premut?` · `pin [0/1/2] tocat?` · `[s'ha mogut / s'ha sacsejat / ha saltat]?`
- `mostra el símbol [cor/feliç/trist/fletxes/sí/no]` · `mostra el text [...]` (màx. 19 caràcters) · `mostra la matriu [25 bits]` · `netja la pantalla`

`inclinació X/Y` es dona en graus (dividit per 10, com Scratch). Els blocs
«quan...» detecten el flanc (només s'activen quan la condició passa de falsa a
certa). És un **superconjunt** dels 10 blocs de l'extensió estàndard de Scratch.

## Procediment complet

El pas a pas (gravar el firmware de Scratch, activar Web Bluetooth a Chrome,
carregar l'extensió i connectar) està documentat a
[`docs/microbit-web-bluetooth.md`](../docs/microbit-web-bluetooth.md). Ací
resumix només el desenvolupament.

## Carregar-la a TurboWarp

- Serveix el fitxer en `localhost:8000` (`python3 -m http.server 8000`) i
  carrega `http://localhost:8000/turbowarp-extension/edutictac-link-bluetooth.js`
  amb `?extension=...`, o
- carrega'l des d'un fitxer amb la casella **«Executa l'extensió sense sandbox»**.

## Integració amb EduTicTac Blocs

Blocs substituïx la confiança de TurboWarp per **la seua pròpia galeria local**
(`extensions/`, vegeu `src/blocs/extensions-policy.js` del repo). Per tant:

1. Copia `edutictac-link-bluetooth.js` a la galeria del fork:
   `edutictac-blocs/extensions/edutictac-link-bluetooth.js`.
2. Carrega-la com `https://blocs.edutictac.es/editor?extension=extensions/edutictac-link-bluetooth.js`
   (o des de la galeria local, si s'hi afig).
3. Reconstruïx i redesplega Blocs (`docker compose up -d --build`).

No cal tocar el `SecurityManager`: qualsevol URL baix `extensions/` del mateix
origen ja és de confiança i s'executa sense sandbox.

## Tests

```bash
cd turbowarp-extension
node --test
```

El fitxer de l'extensió és alhora carregable com a `<script>` i com a mòdul
CommonJS: si detecta `module.exports` i no `Scratch`, exporta les funcions pures
per als tests.

## Relació amb el daemon

- **Daemon** (`edutictac-link`): Firefox i Chromium, descoberta automàtica,
  micro:bit/WeDo2/Boost/EV3, sense instal·lar res al navegador.
- **Esta extensió**: només Chromium, sense instal·lar res al sistema, però amb
  connexió manual i només micro:bit.

Vegeu `docs/roadmap.md` (Fase 4).
