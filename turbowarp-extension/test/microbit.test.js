// Tests de la lògica de protocol de l'extensió (Node, sense navegador).
// Executar: node --test turbowarp-extension/test/

'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');

const microbit = require('../edutictac-link-bluetooth.js');

test('encodeCommand anteposa el byte de comando', () => {
  assert.deepEqual(Array.from(microbit.encodeCommand(0x81, [1, 2])), [0x81, 1, 2]);
  assert.deepEqual(Array.from(microbit.encodeCommand(0x82)), [0x82]);
});

test('encodeDisplayText usa charCodeAt i truncat a 19', () => {
  assert.deepEqual(Array.from(microbit.encodeDisplayText('Hi')), [0x81, 72, 105]);
  const long = 'a'.repeat(30);
  const encoded = microbit.encodeDisplayText(long);
  assert.equal(encoded.length, 20); // 1 comando + 19 caràcters
});

test('encodeMatrix codifica les 5 files (LSB = columna esquerra)', () => {
  assert.deepEqual(
    Array.from(microbit.encodeMatrix('1'.padEnd(25, '0'))),
    [0x82, 1, 0, 0, 0, 0]
  );
  assert.deepEqual(
    Array.from(microbit.encodeMatrix('11111'.padEnd(25, '0'))),
    [0x82, 31, 0, 0, 0, 0]
  );
  assert.deepEqual(
    Array.from(microbit.encodeMatrix('0000011111'.padEnd(25, '0'))),
    [0x82, 0, 31, 0, 0, 0]
  );
  assert.deepEqual(Array.from(microbit.encodeClearDisplay()), [0x82, 0, 0, 0, 0, 0]);
});

test('encodeMatrix rebutja longitud distinta de 25', () => {
  assert.throws(() => microbit.encodeMatrix('0101'));
});

test('toSigned16 replica el llindar de Scratch (> 32768)', () => {
  assert.equal(microbit.toSigned16(0xff, 0xf0), -16);
  assert.equal(microbit.toSigned16(0x00, 0x10), 16);
  // 0x8000 = 32768 no es corregeix (cas límit de Scratch)
  assert.equal(microbit.toSigned16(0x80, 0x00), 32768);
});

test('parseMicrobitData llig tots els camps i gestos', () => {
  const data = new Uint8Array([0xff, 0xf0, 0xff, 0xf0, 1, 0, 1, 0, 1, 0b101]);
  const state = microbit.parseMicrobitData(data);
  assert.equal(state.tiltX, -16);
  assert.equal(state.tiltY, -16);
  assert.equal(state.buttonA, true);
  assert.equal(state.buttonB, false);
  assert.deepEqual(state.touchPins, [true, false, true]);
  assert.equal(state.gesture.shaken, true);
  assert.equal(state.gesture.jumped, false);
  assert.equal(state.gesture.moved, true);
});

test('parseMicrobitData amb tot a zero', () => {
  const state = microbit.parseMicrobitData(new Uint8Array(10));
  assert.equal(state.tiltX, 0);
  assert.deepEqual(state.touchPins, [false, false, false]);
  assert.deepEqual(state.gesture, {moved: false, shaken: false, jumped: false});
});

test('detectTransitions: flanc del botó A', () => {
  const previous = microbit.parseMicrobitData(new Uint8Array(10));
  const next = microbit.parseMicrobitData(new Uint8Array([0, 0, 0, 0, 1, 0, 0, 0, 0, 0]));
  assert.deepEqual(microbit.detectTransitions(previous, next), [
    {opcode: 'whenButtonPressed', fields: {BUTTON: 'A'}}
  ]);
});

test('detectTransitions: sense flanc si ja estava premut', () => {
  const pressed = microbit.parseMicrobitData(new Uint8Array([0, 0, 0, 0, 1, 0, 0, 0, 0, 0]));
  assert.deepEqual(microbit.detectTransitions(pressed, pressed), []);
});

test('detectTransitions: gest sacsejat', () => {
  const previous = microbit.parseMicrobitData(new Uint8Array(10));
  const next = microbit.parseMicrobitData(new Uint8Array([0, 0, 0, 0, 0, 0, 0, 0, 0, 0b001]));
  assert.deepEqual(microbit.detectTransitions(previous, next), [
    {opcode: 'whenGesture', fields: {GESTURE: 'shaken'}}
  ]);
});

test('detectTransitions: inclinació a la dreta', () => {
  const previous = microbit.parseMicrobitData(new Uint8Array(10));
  const next = microbit.parseMicrobitData(new Uint8Array([0, 200, 0, 0, 0, 0, 0, 0, 0, 0]));
  const events = microbit.detectTransitions(previous, next);
  assert.ok(events.some(e => e.opcode === 'whenTilted' && e.fields.DIRECTION === 'right'));
  assert.ok(events.some(e => e.opcode === 'whenTilted' && e.fields.DIRECTION === 'any'));
});

test('tiltDirections: cap a l\'esquerra', () => {
  // data[0]=0xff, data[1]=0x38 => tiltX = -200 => angle -20
  const state = microbit.parseMicrobitData(new Uint8Array([0xff, 0x38, 0, 0, 0, 0, 0, 0, 0, 0]));
  const dirs = microbit.tiltDirections(state);
  assert.equal(dirs.left, true);
  assert.equal(dirs.right, false);
  assert.equal(dirs.any, true);
});

