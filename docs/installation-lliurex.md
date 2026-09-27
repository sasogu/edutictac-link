# Instal·lació a LliureX 23 i posteriors

LliureX està basat en Ubuntu/Debian, així que el procediment és el mateix que
a [docs/installation-debian.md](installation-debian.md), amb dos matisos:
la versió de Python i els paquets del sistema.

## Requisits previs

```bash
python3 --version          # ha de ser 3.11 o superior
systemctl status bluetooth
bluetoothctl list          # hauria de mostrar un controlador
```

Si `python3` és anterior a 3.11, instal·la un Python més nou des dels
repositoris de LliureX/Ubuntu o fes servir `pipx` amb una versió moderna.

## Instal·lació

```bash
sudo apt update
sudo apt install pipx python3-venv
pipx ensurepath

git clone https://git.edutictac.es/Edutictac/edutictac-link.git
cd edutictac-link
pipx install .
edutictac-link doctor
```

## Servei d'usuari

```bash
./scripts/install-service.sh
systemctl --user status edutictac-link
```

## Navegadors a LliureX

- **Firefox**: funciona la via del daemon. No suporta Web Bluetooth ni Web
  Serial (per tant, no la futura extensió de TurboWarp).
- **Chromium/Chrome**: funciona la via del daemon i, a més, Web Bluetooth i
  Web Serial.

Recomanació per a l'aula: Firefox per defecte si només s'usa EduTicTac Link.

## Notes del centre

- No cal obrir cap port al tallafoc: el daemon només escolta a `127.0.0.1`.
- No cal Docker.
- Si es desplega per imatge d'aula, `pipx install` i
  `systemctl --user enable edutictac-link` es poden incloure a la imatge.

## Verificació

```bash
edutictac-link devices    # hauria de llistar microbit, wedo2 i boost
edutictac-link doctor
```

Amb el maquinari encés, arranca el daemon i connecta des de Scratch o
TurboWarp.
