// EduTicTac Link — extensió experimental per a TurboWarp (Web Bluetooth)
//
// ESBÓS. Ha d'executar-se sense sandbox. Només Chromium/Edge tenen Web
// Bluetooth. No substitueix el daemon EduTicTac Link.
//
// Carrega des de http://localhost:8000/edutictac-link-bluetooth.js
// o integra-la a un fork de TurboWarp modificant la llista blanca d'URLs.

(function (Scratch) {
  'use strict';

  if (!Scratch.extensions.unsandboxed) {
    throw new Error('EduTicTac Link (Bluetooth) ha de córrer sense sandbox');
  }

  const MICROBIT_SERVICE = 0xf005;
  const MICROBIT_RX = '5261da01-fa7e-42ab-850b-7c80220097cc';
  const MICROBIT_TX = '5261da02-fa7e-42ab-850b-7c80220097cc';

  class EduTicTacBluetooth {
    constructor() {
      this._device = null;
      this._server = null;
      this._rx = null;
    }

    getInfo() {
      return {
        id: 'edutictacLinkBluetooth',
        name: 'EduTicTac Link (BLE)',
        color1: '#0ea5e9',
        blocks: [
          {
            opcode: 'available',
            blockType: Scratch.BlockType.BOOLEAN,
            text: 'Web Bluetooth disponible?'
          },
          {
            opcode: 'connectMicrobit',
            blockType: Scratch.BlockType.COMMAND,
            text: 'connecta el micro:bit'
          },
          {
            opcode: 'deviceName',
            blockType: Scratch.BlockType.REPORTER,
            text: 'nom del dispositiu'
          },
          {
            opcode: 'isConnected',
            blockType: Scratch.BlockType.BOOLEAN,
            text: 'connectat?'
          },
          {
            opcode: 'send',
            blockType: Scratch.BlockType.COMMAND,
            text: 'envia al micro:bit [DATA]',
            arguments: {
              DATA: {type: Scratch.ArgumentType.STRING, defaultValue: '81'}
            }
          }
        ]
      };
    }

    available() {
      return typeof navigator !== 'undefined' && !!navigator.bluetooth;
    }

    async connectMicrobit() {
      if (!navigator.bluetooth) {
        throw new Error('Web Bluetooth no està disponible en este navegador');
      }
      this._device = await navigator.bluetooth.requestDevice({
        filters: [{services: [MICROBIT_SERVICE]}]
      });
      this._server = await this._device.gatt.connect();
      const service = await this._server.getPrimaryService(MICROBIT_SERVICE);
      this._rx = await service.getCharacteristic(MICROBIT_RX);
      await this._rx.startNotifications();
      this._device.addEventListener('gattserverdisconnected', () => {
        this._server = null;
        this._rx = null;
      });
    }

    deviceName() {
      return this._device ? this._device.name || '' : '';
    }

    isConnected() {
      return !!(this._device && this._device.gatt && this._device.gatt.connected);
    }

    async send(args) {
      if (!this._server) {
        throw new Error('No hi ha cap micro:bit connectat');
      }
      const service = await this._server.getPrimaryService(MICROBIT_SERVICE);
      const tx = await service.getCharacteristic(MICROBIT_TX);
      const byte = parseInt(args.DATA, 10) || 0;
      await tx.writeValue(new Uint8Array([byte & 0xff]));
      return byte;
    }
  }

  Scratch.extensions.register(new EduTicTacBluetooth());
})(Scratch);
