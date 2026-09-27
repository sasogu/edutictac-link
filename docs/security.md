# Seguretat

## Principis

1. **Només localhost.** El servidor escolta a `127.0.0.1` per defecte. No
   s'exposa a la xarxa local. Obrir-lo requerix una acció explícita.
2. **Sense privilegis.** `bleak` parla amb BlueZ per D-Bus; no cal root, ni
   `setcap`, ni regles udev per al BLE.
3. **Validació d'origen.** Una pàgina web qualsevol del navegador pot
   intentar connectar al port local. Per defecte EduTicTac Link només accepta
   els orígens de Scratch, TurboWarp i EduTicTac Blocs, a més dels clients
   natius sense capçalera `Origin`.
4. **Serveis permesos.** Després de connectar, només es poden usar els serveis
   GATT declarats al descobriment.
5. **Sense secrets.** El projecte no emmagatzema credencials ni claus.

## Superfície d'atac

L'única superfície és el WebSocket local. Els riscos considerats:

| Risc | Mitigació |
|---|---|
| Una web maliciosa controla el daemon | Validació d'`Origin` configurable |
| Accés des d'una altra màquina | Escolta només a `127.0.0.1` |
| Accés a serveis GATT no previstos | Allowlist de serveis del descobriment |
| Escalada de privilegis | El procés no corre com a root |

## Configuració

```bash
# Endurir: no acceptar clients sense origen
EDUTICTAC_LINK_ALLOW_MISSING_ORIGIN=0 edutictac-link

# Afegir un origen propi (p. ex. una instància pròpia de TurboWarp)
EDUTICTAC_LINK_ALLOW_ORIGINS="https://scratch.mit.edu,https://la-meua-aula.example" edutictac-link

# Desactivar la validació (NO recomanat)
EDUTICTAC_LINK_ENFORCE_ORIGIN=0 edutictac-link
```

## Per què no exposar-ho a la xarxa

Si s'escolta a `0.0.0.0`, qualsevol equip de la xarxa podria descobrir i
controlar el maquinari connectat a l'ordinador de l'aula. Per això el valor
per defecte és `127.0.0.1` i canviar-lo és una decisió conscient.

## Vegeu també

- [docs/decisions.md](decisions.md) D-004 i D-005.
- [docs/scratch-link-protocol.md](scratch-link-protocol.md) per a la
  restricció de serveis.
