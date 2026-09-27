# Dispositius suportats

El daemon és **genèric de transport**: les extensions de Scratch construeixen
els comandaments concrets de cada dispositiu. EduTicTac Link només descobreix,
connecta i intercanvia dades GATT. Els perfils de `src/edutictac_link/devices/`
servixen per a identificar perifèrics, alimentar `edutictac-link devices` i
servir de fixtures.

## Bluetooth Low Energy (implementat)

### BBC micro:bit

- Filtre: `services: [0xf005]`
- Característiques:
  - RX (notificacions): `5261da01-fa7e-42ab-850b-7c80220097cc`
  - TX (escriptura): `5261da02-fa7e-42ab-850b-7c80220097cc`
- **Firmware**: cal gravar el firmware de Scratch
  (`scratchfoundation/scratch-microbit-firmware`). No és responsabilitat del
  daemon.

### LEGO WeDo 2.0

- Filtre: `services: [00001523-1212-efde-1523-785feabcd123]`
- `optionalServices`: `00004f0e-1212-efde-1523-785feabcd123`
- Característiques: `00001527`, `00001528` (dispositiu); `00001560`,
  `00001563`, `00001565` (E/S).

### LEGO Boost

- Filtre: servei `00001623-1212-efde-1623-785feabcd123` **més**
  `manufacturerData` de LEGO (`0x0397`) amb prefix `00 40`.
- Característica única: `00001624-1212-efde-1623-785feabcd123`.

### Vernier Go Direct (GDX-FOR)

- Filtre: `namePrefix: "GDX-FOR"`
- Servei: `d91714ef-28b9-4f91-ba16-f0d9a604f112`
- No és objectiu del primer cicle, però el nucli genèric ja el pot descobrir.

## Bluetooth Classic (pendent, fase 2)

### LEGO EV3

- Transport: `/scratch/bt` (RFCOMM/SPP)
- Filtre: `majorDeviceClass 8`, `minorDeviceClass 1`; PIN `1234`
- Requereix implementar el transport Bluetooth Classic (socket RFCOMM natiu o
  D-Bus), sense `pybluez`.

## Altres

- **LEGO SPIKE Prime**: no hi ha extensió a `scratch-vm`; el suport viu a
  projectes de tercers.
- **Makey Makey**: HID, no passa pel daemon.

## Provar-ho

```bash
edutictac-link devices     # llista els perfils i els filtres
edutictac-link doctor      # comprova adaptador i permisos
```

Per a depurar un dispositiu concret, arranca el daemon amb `--debug` i mira
els missatges de descobriment i connexió.
