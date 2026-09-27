# Contribuir a EduTicTac Link

Gràcies per l'interés. El projecte és xicotet i busca mantindre's simple.

## Entorn de desenvolupament

```bash
git clone https://git.edutictac.es/Edutictac/edutictac-link.git
cd edutictac-link
python3 -m venv .venv
. .venv/bin/activate
pip install -e '.[dev]'
pytest -q
```

Requisits: Python 3.11 o superior. Els tests **no** necessiten maquinari ni
Bluetooth: fan servir un backend BLE fals (`bluetooth/fake_backend.py`).

## Estil

- Python 3.11+, tipus bàsics, sense dependències noves sense justificar-ho.
- Comentaris i textos d'usuari en **valencià**.
- Seguix l'estructura de mòduls existent (vegeu `docs/architecture.md`).
- No afegis funcionalitat de dispositiu al daemon: el nucli és genèric de
  transport (vegeu `docs/decisions.md` D-009).

## Abans d'enviar canvis

1. `pytest -q` ha de passar.
2. Comprova que no introduïxes dades internes d'infraestructura (IPs,
   usuaris, rutes de servidor) al repositori.
3. Actualitza la documentació afectada (`docs/`).
4. Fes commits xicotets i descriptius.

## Flux de treball

- Si us contribuïs a l'ecosistema EduTicTac, l'upstream és la forja
  `https://git.edutictac.es/Edutictac/edutictac-link` (hi ha un espejo a
  GitHub).
- No feu `force-push` a `main`.
- Obri una incidència o un canvi (merge request) per a canvis grans; per a
  correccions xicotetes, un commit directe està bé.

## Idees on ajudar

- Validació amb maquinari real (micro:bit amb firmware de Scratch, WeDo 2.0,
  Boost) i reportar resultats.
- **EV3 / Bluetooth Classic**: el transport real és experimental; ajudar a
  validar-lo amb un EV3 i refinar l'emparellament i el canal SPP.
- Extensió experimental de TurboWarp (`turbowarp-extension/`).
- Noms simbòlics de servei Bluetooth (taula de números assignats).
