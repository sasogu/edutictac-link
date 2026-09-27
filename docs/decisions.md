# Decisions tècniques — EduTicTac Link

## D-001. Base nova derivada de pyscrlink, no fork git

**Decisió:** crear una base de codi nova i modular, adaptant de pyscrlink
(BSD-3-Clause) la lògica de sessió i de coincidència de filtres, i
reescrivint el transport i el servidor.

**Raó:** pyscrlink és monolític (un sol fitxer de 23 KB) i arrossega
`bluepy`, `pybluez` i l'API antiga de `websockets`. Un fork git heretaria
eixa arquitectura i eixes dependències, contra el requisit explícit
d'evitar biblioteques abandonades i disseny modular. Adaptar amb atribució
(vegeu `NOTICE` i `LICENSE.pyscrlink`) és més net i compatible amb AGPL-3.0.

**Alternatives descartades:** fork directe de pyscrlink (deute heretat);
reescriptura total sense reutilitzar (descartada perquè hi ha codi
reutilitzable amb llicència compatible).

## D-002. Llicència AGPL-3.0

Coherent amb la resta de l'ecosistema EduTicTac (EduHoot, recursos). Compatible
amb incloure codi BSD-3-Clause de pyscrlink i dependències MIT/BSD mantenint
l'atribució.

## D-003. Servir `ws://127.0.0.1:20111`, sense TLS

El client de scratch-vm (i per tant Scratch 3, TurboWarp i EduTicTac Blocs)
prova simultàniament `ws://127.0.0.1:20111` i el WSS llegat. Si el modern
funciona, no cal certificat ni instal·lar-lo als NSS DB. Això elimina
`gencert.py`, `pyOpenSSL` i part de la fricció d'instal·lació.

El WSS llegat al port 20110 queda **fora de l'abast del primer cicle** i
documentat com a opció futura per a navegadors antics.

## D-004. Només `localhost` per defecte

Escoltar únicament a `127.0.0.1`. Obrir a la xarxa local requereix una opció
explícita i va acompanyat d'avís. Vegeu `docs/security.md`.

## D-005. Validació d'`Origin` configurable

El WebSocket és accessible des de qualsevol pàgina web del navegador. Per
defecte s'accepten els orígens de Scratch/TurboWarp/Blocs i les connexions
sense `Origin` (client natiu). Es registra l'origen de cada connexió i es pot
endurir o relaxar per configuració.

## D-006. Sense root i sense `setcap`

`bleak` parla amb BlueZ per D-Bus; no calen capacitats ni root, a diferència
del `bluepy_helper` de pyscrlink. No s'instal·len regles udev per al BLE. Per
al futur Bluetooth Classic (EV3) es farà servir el socket RFCOMM estàndard de
Python o D-Bus, sense `pybluez`.

## D-007. Pila de dependències

- `bleak` (BLE, D-Bus/BlueZ)
- `websockets>=12` (servidor, API moderna basada en `async with`)
- `click` (CLI)
- Fase 2: `dbus-next` per a Bluetooth Classic.

Python mínim 3.11; provat a Debian 12/13, Ubuntu LTS i LliureX.

## D-008. Servei de sistema: unitat d'usuari

`systemctl --user enable --now edutictac-link`. S'executa amb l'usuari de
sessió (accés al bus de sistema de BlueZ), sense privilegis. El paquet `.deb`
instal·la una unitat d'usuari a `/usr/lib/systemd/user/`. Perquè arranque
sense sessió iniciada caldria `loginctl enable-linger`, que no és el cas
d'ús d'aula.

## D-009. `devices/` com a perfils, no controladors

El daemon no implementa els comandaments de cada dispositiu (això ho fan les
extensions de scratch-vm). Els perfils serveixen per a `edutictac-link
devices`, diagnòstics, filtres per defecte i fixtures de test. Documentat a
`docs/devices.md` per evitar sobreenginyeria.

## D-010. TurboWarp: via complementària, no substitut

L'extensió de TurboWarp amb Web Bluetooth/Web Serial és experimental i només
Chromium. Es considera arquitectura futura integrada a EduTicTac Blocs
(modificant-ne la llista blanca d'URLs). No substitueix el daemon.
