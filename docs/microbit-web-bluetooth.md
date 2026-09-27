# micro:bit per Web Bluetooth (extensió de Blocs)

Procediment complet per connectar un micro:bit des del navegador amb l'extensió
d'EduTicTac Link, **sense instal·lar res al sistema**. Provat amb un micro:bit
**V1** real a `blocs.edutictac.es` amb Google Chrome (2026-09-27).

## Requisits

- Un micro:bit (V1 o V2) i un cable USB de **dades** (no només càrrega).
- **Chrome o Edge** (Chromium). Firefox i Safari **no** tenen Web Bluetooth;
  per a eixos, usa el daemon `edutictac-link` (vegeu més avall).
- El navegador ha d'estar a la **mateixa màquina** on està connectat el
  micro:bit (Web Bluetooth és local).

## 1. Gravar el firmware de Scratch

Cal el firmware específic de Scratch (servici BLE `0xf005`).

1. Baixa `scratch-microbit-1.2.0.hex` (també és al repositori de Blocs:
   `https://blocs.edutictac.es/microbit/scratch-microbit-1.2.0.hex`).
2. Connecta el micro:bit per USB: apareix una unitat anomenada **`MICROBIT`**.
3. Copia el `.hex` a eixa unitat (arrossegar o `cp`).
4. Quan acabe, el micro:bit mostra el **nom de 5 caràcters** (p. ex. `petov`)
   desplaçant-se per la matriu. Eixe és el nom que apareixerà al selector de
   Bluetooth.

Notes:
- **La cara trista és normal**: el firmware de Scratch la mostra quan està
  desconnectat; en connectar canvia.
- Si el micro:bit ja està **emparellat o connectat** des de la configuració de
  Bluetooth de l'escriptori, desconnecta'l: el firmware només admet **una
  connexió** alhora.

## 2. Activar Web Bluetooth a Chrome (Linux)

A Chrome a Linux, Web Bluetooth sol estar **desactivat per defecte**:

1. Obri `chrome://flags`.
2. Activa **Web Bluetooth** i **Experimental Web Platform Features**.
3. **Relaunch**.
4. Comprova-ho: a qualsevol pestanya, F12 → Console → escriu
   `navigator.bluetooth`. Ha de retornar un objecte (no `undefined`).

## 3. Obrir Blocs amb l'extensió

- **Opció A (recomanada)**: a `https://blocs.edutictac.es`, prem **Afig una
  extensió** i tria **micro:bit (Bluetooth)** de la galeria local.
- **Opció B (directa)**: obri
  ```
  https://blocs.edutictac.es/?extension=https://blocs.edutictac.es/extensions/edutictac/hardware/microbit/edutictac-link.js
  ```

## 4. Connectar

1. Arrastra el bloc `connecta el micro:bit` a l'àrea de treball i **fes clic
   damunt d'ell** (eixe clic és el gest d'usuari que Chrome exigix). També pots
   enganxar-lo davall d'un «quan es prem la bandera verda» per connectar en
   arrancar.
2. Al diàleg de Bluetooth de Chrome, tria **`BBC micro:bit [xxxxx]`**.
3. El bloc `connectat?` ha de retornar `true`.

## 5. Blocs disponibles

**Esdeveniments (quan...):**
- `quan es prem el botó [A/B]`
- `quan [s'ha mogut / s'ha sacsejat / ha saltat]`
- `quan s'inclina [cap a qualsevol costat / amunt / avall / a l'esquerra / a la dreta]`
- `quan el pin [0/1/2] es toca`

**Connexió i sensors:**
- `connecta el micro:bit`, `desconnecta el micro:bit`, `connectat?`, `nom del micro:bit`
- `inclinació X`, `inclinació Y` (en graus, com Scratch), `està inclinat [direcció]?`
- `botó [A/B] premut?`, `pin [0/1/2] tocat?`
- `[s'ha mogut / s'ha sacsejat / ha saltat]?`

**Pantalla:**
- `mostra el símbol [cor/feliç/trist/fletxes/sí/no]`
- `mostra el text [...]` (màx. 19 caràcters), `mostra la matriu [25 bits]`, `netja la pantalla`

És un **superconjunt** dels 10 blocs de l'extensió estàndard de Scratch.
**Encara no hi ha** temperatura ni llum (el firmware de Scratch no envia eixos
valors). WeDo/Boost/SPIKE no està previst (LEGO els ha descatalogats i no hi ha
maquinari per a provar-los). Vegeu `docs/roadmap.md`.

## Solució de problemes

| Símptoma | Causa / solució |
|---|---|
| No apareix al diàleg de Chrome | Firmware no gravat; Web Bluetooth no activat; o la placa està connectada a un altre lloc |
| Apareix però no connecta | La placa està emparellada/ocupada; desconnecta-la de la configuració de Bluetooth |
| Connecta però `mostra el text` no fa res | Assegura't de fer **clic damunt** del bloc (gest); mira la consola (F12) |
| «No hi ha cap micro:bit connectat» | Cal executar `connecta el micro:bit` primer |
| Firefox o Safari | No suporten Web Bluetooth: usa el daemon |
| Canvis no es veuen | `Ctrl+Shift+R` (recàrrega forçada) |

## Alternativa: el daemon d'EduTicTac Link

Funciona a **Firefox i Chromium**, amb descoberta automàtica i més dispositius
(micro:bit, WeDo 2.0, Boost, EV3 experimental):

```bash
pipx install .        # o: sudo apt install edutictac-link
edutictac-link doctor
edutictac-link
```

Després, a Scratch o Blocs/TurboWarp, afig l'extensió **micro:bit** de Scratch
i connecta. Vegeu `docs/validation.md` i `docs/installation-debian.md`.

## Per què dos camins

- **Extensió Web Bluetooth**: zero instal·lació, però només Chromium, connexió
  manual i pocs blocs.
- **Daemon**: cal instal·lar-lo, però funciona a Firefox i Chromium, amb
  descoberta automàtica i tots els blocs.
