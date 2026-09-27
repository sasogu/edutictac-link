// EduTicTac Link — extensió experimental per a TurboWarp / EduTicTac Blocs.
//
// Conecta un micro:bit amb Web Bluetooth directament, sense daemon local.
// Cal executar-se SENSE sandbox (Web Bluetooth no està disponible en workers).
// Només Chromium/Edge. No substitueix el daemon EduTicTac Link.
//
// El fitxer és alhora carregable com a <script> (TurboWarp) i com a mòdul
// CommonJS per als tests de Node: si detecta `module.exports` i no `Scratch`,
// exporta les funcions pures i no registra l'extensió.

(function (Scratch) {
  'use strict';

  // ---- Protocol pur micro:bit (testable sense navegador) ----------------

  const CMD_PIN_CONFIG = 0x80;
  const CMD_DISPLAY_TEXT = 0x81;
  const CMD_DISPLAY_LED = 0x82;

  const MICROBIT_SERVICE = '0000f005-0000-1000-8000-00805f9b34fb';
  const RX_CHARACTERISTIC = '5261da01-fa7e-42ab-850b-7c80220097cc';
  const TX_CHARACTERISTIC = '5261da02-fa7e-42ab-850b-7c80220097cc';

  const MAX_TEXT_LENGTH = 19;
  const BLETimeout = 4500;

  const clampText = text => String(text).substring(0, MAX_TEXT_LENGTH);

  const encodeCommand = (command, payload) => {
    const body = payload || [];
    const out = new Uint8Array(body.length + 1);
    out[0] = command & 0xff;
    for (let i = 0; i < body.length; i++) out[i + 1] = body[i] & 0xff;
    return out;
  };

  const encodeDisplayText = text => {
    const value = clampText(text);
    const bytes = new Array(value.length);
    for (let i = 0; i < value.length; i++) bytes[i] = value.charCodeAt(i) & 0xff;
    return encodeCommand(CMD_DISPLAY_TEXT, bytes);
  };

  const encodeMatrix = symbol => {
    const clean = String(symbol).replace(/\s/g, '');
    if (clean.length !== 25) {
      throw new Error('La matriu ha de tindre 25 caràcters (0/1)');
    }
    let value = 0;
    for (let i = 0; i < 25; i++) {
      if (clean[i] !== '0') value += Math.pow(2, i);
    }
    const rows = new Uint8Array(5);
    for (let r = 0; r < 5; r++) rows[r] = (value >> (5 * r)) & 0x1f;
    return encodeCommand(CMD_DISPLAY_LED, rows);
  };

  const encodeClearDisplay = () => encodeCommand(CMD_DISPLAY_LED, [0, 0, 0, 0, 0]);

  const toSigned16 = (high, low) => {
    const value = low | (high << 8);
    return value > (1 << 15) ? value - (1 << 16) : value;
  };

  const parseMicrobitData = data => {
    const bytes = data instanceof Uint8Array ? data : new Uint8Array(data);
    const gesture = bytes[9] || 0;
    return {
      tiltX: toSigned16(bytes[0], bytes[1]),
      tiltY: toSigned16(bytes[2], bytes[3]),
      buttonA: !!bytes[4],
      buttonB: !!bytes[5],
      touchPins: [!!bytes[6], !!bytes[7], !!bytes[8]],
      gesture: {
        moved: !!((gesture >> 2) & 1),
        shaken: !!(gesture & 1),
        jumped: !!((gesture >> 1) & 1)
      }
    };
  };

  const exportedApi = {
    CMD_PIN_CONFIG,
    CMD_DISPLAY_TEXT,
    CMD_DISPLAY_LED,
    MICROBIT_SERVICE,
    RX_CHARACTERISTIC,
    TX_CHARACTERISTIC,
    clampText,
    encodeCommand,
    encodeDisplayText,
    encodeMatrix,
    encodeClearDisplay,
    toSigned16,
    parseMicrobitData
  };

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = exportedApi;
    return;
  }
  if (!Scratch) {
    return;
  }

  // ---- Extensió de TurboWarp -------------------------------------------

  class MicrobitBluetooth {
    constructor() {
      this._device = null;
      this._server = null;
      this._rx = null;
      this._tx = null;
      this._state = parseMicrobitData(new Uint8Array(10));
      this._timeoutId = null;
    }

    getInfo() {
      return {
        id: 'edutictacLinkMicrobit',
        name: 'EduTicTac Link (micro:bit)',
        color1: '#0ea5e9',
        color2: '#0284c7',
        blocks: [
          {opcode: 'connect', blockType: Scratch.BlockType.COMMAND, text: 'connecta el micro:bit'},
          {opcode: 'disconnect', blockType: Scratch.BlockType.COMMAND, text: 'desconnecta el micro:bit'},
          {opcode: 'isConnected', blockType: Scratch.BlockType.BOOLEAN, text: 'connectat?'},
          {opcode: 'deviceName', blockType: Scratch.BlockType.REPORTER, text: 'nom del micro:bit'},
          '---',
          {opcode: 'tiltX', blockType: Scratch.BlockType.REPORTER, text: 'inclinació X'},
          {opcode: 'tiltY', blockType: Scratch.BlockType.REPORTER, text: 'inclinació Y'},
          {
            opcode: 'isButtonPressed',
            blockType: Scratch.BlockType.BOOLEAN,
            text: 'botó [BUTTON] premut?',
            arguments: {
              BUTTON: {type: Scratch.ArgumentType.STRING, menu: 'BUTTONS', defaultValue: 'A'}
            }
          },
          {
            opcode: 'isTouched',
            blockType: Scratch.BlockType.BOOLEAN,
            text: 'pin [PIN] tocat?',
            arguments: {
              PIN: {type: Scratch.ArgumentType.NUMBER, menu: 'PINS', defaultValue: 0}
            }
          },
          {
            opcode: 'isGesture',
            blockType: Scratch.BlockType.BOOLEAN,
            text: '[GESTURE]?',
            arguments: {
              GESTURE: {type: Scratch.ArgumentType.STRING, menu: 'GESTURES', defaultValue: 'shaken'}
            }
          },
          '---',
          {
            opcode: 'displayText',
            blockType: Scratch.BlockType.COMMAND,
            text: 'mostra el text [TEXT]',
            arguments: {
              TEXT: {type: Scratch.ArgumentType.STRING, defaultValue: 'Hola'}
            }
          },
          {
            opcode: 'displayMatrix',
            blockType: Scratch.BlockType.COMMAND,
            text: 'mostra la matriu [MATRIX]',
            arguments: {
              MATRIX: {
                type: Scratch.ArgumentType.STRING,
                defaultValue: '0'.repeat(25)
              }
            }
          },
          {opcode: 'clearDisplay', blockType: Scratch.BlockType.COMMAND, text: 'netja la pantalla'}
        ],
        menus: {
          BUTTONS: {acceptReporters: false, items: ['A', 'B']},
          PINS: {acceptReporters: false, items: ['0', '1', '2']},
          GESTURES: {
            acceptReporters: false,
            items: [
              {text: 's\'ha mogut', value: 'moved'},
              {text: 's\'ha sacsejat', value: 'shaken'},
              {text: 'ha saltat', value: 'jumped'}
            ]
          }
        }
      };
    }

    // -- connexió --------------------------------------------------------

    async connect() {
      if (typeof navigator === 'undefined' || !navigator.bluetooth) {
        throw new Error('Web Bluetooth no està disponible (cal Chromium/Edge i HTTPS)');
      }
      const device = await navigator.bluetooth.requestDevice({
        filters: [{services: [MICROBIT_SERVICE]}]
      });
      const server = await device.gatt.connect();
      const service = await server.getPrimaryService(MICROBIT_SERVICE);
      const rx = await service.getCharacteristic(RX_CHARACTERISTIC);
      const tx = await service.getCharacteristic(TX_CHARACTERISTIC);
      this._device = device;
      this._server = server;
      this._rx = rx;
      this._tx = tx;
      console.info(
        '[EduTicTac Link] connectat; TX props:',
        Array.from(tx.properties || []),
        'RX props:',
        Array.from(rx.properties || [])
      );
      rx.addEventListener('characteristicvaluechanged', event => {
        this._onData(event.target.value);
      });
      device.addEventListener('gattserverdisconnected', () => this._handleDisconnected());
      try {
        await rx.startNotifications();
        console.info('[EduTicTac Link] notificacions activades');
      } catch (err) {
        console.warn("[EduTicTac Link] no s'han pogut activar les notificacions:", err);
      }
      // El firmware de Scratch necessita un moment abans d'acceptar ordes.
      await new Promise(resolve => setTimeout(resolve, 300));
      this._armTimeout();
    }

    async disconnect() {
      this._clearTimeout();
      if (this._device && this._device.gatt && this._device.gatt.connected) {
        this._device.gatt.disconnect();
      }
      this._handleDisconnected();
    }

    isConnected() {
      return !!(this._device && this._device.gatt && this._device.gatt.connected);
    }

    deviceName() {
      return this._device ? (this._device.name || '') : '';
    }

    // -- sensors ---------------------------------------------------------

    tiltX() {
      return Math.round(this._state.tiltX / 10);
    }

    tiltY() {
      return Math.round(this._state.tiltY / 10);
    }

    isButtonPressed(args) {
      const button = String(args.BUTTON).toUpperCase();
      if (button === 'A') return this._state.buttonA;
      if (button === 'B') return this._state.buttonB;
      return false;
    }

    isTouched(args) {
      const pin = Number(args.PIN);
      return !!this._state.touchPins[pin];
    }

    isGesture(args) {
      return !!this._state.gesture[String(args.GESTURE)];
    }

    // -- pantalla --------------------------------------------------------

    async displayText(args) {
      await this._write(encodeDisplayText(args.TEXT));
    }

    async displayMatrix(args) {
      await this._write(encodeMatrix(args.MATRIX));
    }

    async clearDisplay() {
      await this._write(encodeClearDisplay());
    }

    // -- intern ----------------------------------------------------------

    _write(bytes) {
      const tx = this._tx;
      if (!tx) {
        throw new Error('No hi ha cap micro:bit connectat');
      }
      const attempt = () => {
        if (typeof tx.writeValueWithResponse === 'function') {
          return tx.writeValueWithResponse(bytes);
        }
        return tx.writeValue(bytes);
      };
      const fallback = () => {
        if (typeof tx.writeValueWithoutResponse === 'function') {
          return tx.writeValueWithoutResponse(bytes);
        }
        return tx.writeValue(bytes);
      };
      return attempt().catch(err => {
        console.warn(
          "[EduTicTac Link] escriptura amb resposta fallida; prove sense resposta",
          err
        );
        return fallback();
      });
    }

    _onData(value) {
      const bytes = new Uint8Array(
        value.buffer, value.byteOffset, value.byteLength
      );
      this._state = parseMicrobitData(bytes);
      this._armTimeout();
    }

    _armTimeout() {
      this._clearTimeout();
      this._timeoutId = setTimeout(() => this._handleLost(), BLETimeout);
    }

    _clearTimeout() {
      if (this._timeoutId !== null) {
        clearTimeout(this._timeoutId);
        this._timeoutId = null;
      }
    }

    _handleLost() {
      this._state = parseMicrobitData(new Uint8Array(10));
      if (this._device && this._device.gatt && this._device.gatt.connected) {
        this._device.gatt.disconnect();
      }
      this._handleDisconnected();
    }

    _handleDisconnected() {
      this._clearTimeout();
      this._rx = null;
      this._tx = null;
      this._server = null;
      this._device = null;
    }
  }

  Scratch.extensions.register(new MicrobitBluetooth());
})(typeof Scratch !== 'undefined' ? Scratch : undefined);
