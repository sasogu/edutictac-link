# EduTicTac Link

Alternativa lliure a **Scratch Link** per a Linux (Debian, Ubuntu, LliureX i
derivats). Permet que **Scratch 3** i **TurboWarp** parlen amb maquinari
educatiu Bluetooth Low Energy des del teu ordinador, sense dependre de
l'aplicació oficial de Windows/macOS.

```
Scratch 3 / TurboWarp  ──ws://127.0.0.1:20111──▶  EduTicTac Link  ──BLE──▶  micro:bit / WeDo 2.0 / Boost
```

## Quin problema resol

Scratch Link és l'aplicació pont que connecta l'editor de Scratch amb
perifèrics Bluetooth. Només s'ofereix per a Windows i macOS. A Linux, des de
fa anys s'ha fet servir `pyscrlink`, però està sense mantenir i depén de
`bluepy` (abandonada), no funciona amb Python actual i obliga a instal·lar
certificats al navegador.

EduTicTac Link és una reimplementació en Python, modular i mantinguda, que:

- funciona amb **Python 3.11, 3.12 i 3.13**;
- usa **BlueZ via D-Bus** amb la biblioteca `bleak` (sense root ni `setcap`);
- publica el punt d'accés modern **`ws://127.0.0.1:20111`**, sense certificats;
- escolta **només a `localhost`** i valida l'origen de les connexions;
- funciona igual a **Firefox i Chromium**.

## Estat

**Alpha (0.1.0).** El primer cicle implementa el transport Bluetooth Low
Energy i els dispositius següents. La validació amb maquinari real depén del
dispositiu que tingues a mà.

| Dispositiu | Transport | Estat |
|---|---|---|
| BBC micro:bit (amb firmware de Scratch) | BLE | Implementat |
| LEGO WeDo 2.0 | BLE | Implementat |
| LEGO Boost | BLE | Implementat |
| LEGO EV3 | Bluetooth Classic | Pendent (fase 2) |
| LEGO SPIKE Prime | — | Sense extensió a Scratch |
| Vernier Go Direct | BLE | Teòric (perfil estàndard) |

Vegeu [docs/roadmap.md](docs/roadmap.md) per a l'abast complet.

## Instal·lació ràpida (pipx)

```bash
git clone https://git.edutictac.es/Edutictac/edutictac-link.git
cd edutictac-link
pipx install .
```

Després:

```bash
edutictac-link doctor     # comprova Python, BlueZ, adaptador, ports, navegadors
edutictac-link            # arranca el daemon
```

També es pot instal·lar pel repositori APT d'EduTicTac:

```bash
sudo apt install edutictac-link   # vegeu docs/installation-debian.md
```

Obrigues Scratch (o TurboWarp) al navegador, afegir l'extensió del dispositiu
(micro:bit, WeDo 2.0, Boost) i connectar.

## Instal·lació com a servei d'usuari

```bash
./scripts/install-service.sh
systemctl --user status edutictac-link
```

## Ús

```
edutictac-link                 # arranca el daemon
edutictac-link run             # el mateix, explícit
edutictac-link status          # indica si està escoltant
edutictac-link devices         # llista els dispositius coneguts
edutictac-link scan            # escaneja perifèrics BLE propers
edutictac-link doctor          # diagnòstic de l'entorn
```

Opcions: `--host`, `--port`, `--debug`. També es poden configurar amb
variables d'entorn `EDUTICTAC_LINK_*` (vegeu [docs/architecture.md](docs/architecture.md)).

## Solució de problemes

- **Scratch diu «Assegura't que tens Scratch Link instal·lat».** Comprova que
  el daemon està en marxa (`edutictac-link status`) i reinicia el navegador.
- **No troba dispositius.** Comprova que el Bluetooth està actiu
  (`systemctl status bluetooth`), que el micro:bit té el firmware de Scratch,
  i que el dispositiu està engegat i a prop.
- **El micro:bit no apareix.** Cal gravar-li el firmware de Scratch
  (`scratchfoundation/scratch-microbit-firmware`).
- **Permisos.** Normalment no cal root. Si `doctor` ho indica, afig el teu
  usuari al grup `bluetooth`.
- Més detalls a [docs/installation-debian.md](docs/installation-debian.md),
  [docs/security.md](docs/security.md) i la guia de validació amb maquinari
  [docs/validation.md](docs/validation.md).

## Desenvolupament

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e '.[dev]'
pytest -q
```

## Llicència

AGPL-3.0-or-later. Vegeu [LICENSE](LICENSE) i [NOTICE](NOTICE) per a les
atribucions (pyscrlink BSD-3-Clause, documentació del protocol de Scratch
Foundation).
