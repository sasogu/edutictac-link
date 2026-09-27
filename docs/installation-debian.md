# Instal·lació a Debian (12/13) i Ubuntu LTS

## Requisits

- Debian 12 (bookworm) o 13 (trixie), o Ubuntu LTS recent.
- Python 3.11 o superior.
- BlueZ (normalment ja instal·lat) i un adaptador Bluetooth amb BLE.
- Un navegador: Firefox o Chromium.

Comprova l'entorn:

```bash
edutictac-link doctor
```

## Opció recomanada: pipx

`pipx` instal·la l'aplicació en un entorn aïllat i l'exposa al `PATH`.

```bash
sudo apt update
sudo apt install pipx python3-venv
pipx ensurepath

git clone https://git.edutictac.es/Edutictac/edutictac-link.git
cd edutictac-link
pipx install .
```

## Opció de sistema: repositori APT d'EduTicTac

El paquet està publicat a `packages.edutictac.es`:

```bash
curl -fsSL https://packages.edutictac.es/edutictac-archive-keyring.gpg \
  | sudo tee /usr/share/keyrings/edutictac.gpg >/dev/null

echo "deb [signed-by=/usr/share/keyrings/edutictac.gpg] https://packages.edutictac.es stable main" \
  | sudo tee /etc/apt/sources.list.d/edutictac.list

sudo apt update
sudo apt install edutictac-link
```

El paquet depén de `python3-bleak`, `python3-websockets` i `python3-click`
(disponibles a Debian 13/trixie). A Debian 12 cal comprovar que les versions
siguen prou recents.

### Construir el .deb localment

Si preferixes construir-lo tu:

```bash
sudo apt install debhelper dh-python pybuild-plugin-pyproject python3-all python3-setuptools
./packaging/build-deb.sh
sudo apt install ./dist/edutictac-link_0.1.0_all.deb
```

## Servei d'usuari systemd

Amb la instal·lació feta (pipx o .deb):

```bash
systemctl --user enable --now edutictac-link
systemctl --user status edutictac-link
```

Amb el paquet `.deb`, la unitat s'instal·la a
`/usr/lib/systemd/user/edutictac-link.service` i apunta a
`/usr/bin/edutictac-link`. Amb pipx, `scripts/install-service.sh` usa
`~/.local/bin/edutictac-link`.

> Nota: una unitat d'usuari només arranca amb la sessió oberta. Per a un
> ordinador d'aula on el professorat inicia sessió, és el comportament
> desitjat.

## Verificació

```bash
edutictac-link doctor        # hauria de mostrar [ ok ] a BlueZ, adaptador i ports
edutictac-link               # arranca el daemon
```

Al navegador, obri Scratch 3 o TurboWarp, afig l'extensió del dispositiu i
connecta.

## Solució de problemes

- **`RuntimeError: no running event loop`** o errors de `bluepy`: estàs usant
  `pyscrlink`. Desinstal·la'l i usa EduTicTac Link.
- **`Falta la biblioteca 'bleak'`**: `pipx install` no va completar les
  dependències. Reexecuta `pipx install .` o `pipx reinstall edutictac-link`.
- **No detecta l'adaptador**: `systemctl status bluetooth` i comprova que el
  servei està actiu.
- **El port 20111 està ocupat**: pot haver-hi una altra instància. Comprova
  `edutictac-link status`.

Vegeu també [docs/security.md](security.md).
