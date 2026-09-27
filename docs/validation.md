# Validació amb maquinari real

Els tests automàtics cobrixen el protocol amb un **backend BLE fals**, però no
el comportament real de BlueZ amb cada dispositiu. Esta guia servix per validar
EduTicTac Link amb maquinari de debò i documentar-ne el resultat.

## Abans de començar

- Ordinador Linux amb Bluetooth BLE (BlueZ) i `edutictac-link doctor` amb tot
  en `[ ok ]` (l'única línia en `[avís]` acceptable és la de Web Bluetooth).
- Un navegador (Firefox o Chromium).
- El dispositiu encés i a prop (menys d'un metre).

## micro:bit

1. **Firmware**: grava-hi el firmware de Scratch
   (`scratchfoundation/scratch-microbit-firmware`) per USB. La placa ha de
   mostrar un nom de 5 caràcters en engegar-se.
2. Comprova que es veu:
   ```bash
   edutictac-link scan -s 5
   ```
   Hauria d'aparéixer amb `perfil=microbit`.
3. Arranca el daemon:
   ```bash
   edutictac-link
   ```
4. Obri Scratch 3 (`https://scratch.mit.edu`) o TurboWarp, polsa «Afig una
   extensió» i tria **micro:bit**.
5. El dispositiu hauria d'aparéixer a la llista; connecta'l.
6. Prova els blocs: mostrar text, botons A/B, inclinació, sensors.

**Resultat esperat:** connecta i els blocs responen.

## LEGO WeDo 2.0

1. Encén el hub (LED verd intermitent).
2. `edutictac-link scan -s 5` → hauria de mostrar `perfil=wedo2`.
3. Connecta des de Scratch amb l'extensió **WeDo 2.0**.
4. Prova el motor i el sensor de distància/inclinació.

## LEGO Boost

1. Encén el Move Hub.
2. `edutictac-link scan -s 5` → hauria de mostrar `perfil=boost`.
3. Connecta des de Scratch amb l'extensió **Boost**.
4. Prova el motor i el sensor de color.

## Si alguna cosa falla

- Arranca amb depuració i copia les línies rellevants:
  ```bash
  edutictac-link --debug
  ```
- Comprova l'entorn:
  ```bash
  systemctl status bluetooth
  bluetoothctl list
  edutictac-link doctor
  ```
- Si uses una instància pròpia de Scratch/TurboWarp, afig el seu origen a
  `EDUTICTAC_LINK_ALLOW_ORIGINS`.
- Important distingir: **no es veu** (descobriment) vs. **es veu però no
  connecta** (connexió/GATT). Cada cas apunta a una causa distinta.

## Plantilla de resultat

Copia i ompli:

```
- Data:
- Versió d'EduTicTac Link (edutictac-link --version):
- Distribució i versió de Python:
- Navegador:
- Dispositiu i firmware:
- edutictac-link doctor:
- edutictac-link scan -s 5:
- Resultat: connecta? els blocs responen? error exacte?
- Logs (edutictac-link --debug):
```

No inclogues dades personals ni altres dispositius Bluetooth propers.
