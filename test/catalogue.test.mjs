// Catalogue checks for Robot Studio (runs on the built package: npm run build && npm test).
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { CATEGORIES, VOICES, DEFAULT_ROBOT, BROWSER_VOICE, sanitise, isChirpVoice, chirpVoiceName } from '../dist/robot-studio/options.js';

test('every default value is in its category', () => {
  for (const c of CATEGORIES) assert.ok(c.options.includes(DEFAULT_ROBOT[c.key]), `${c.key}=${DEFAULT_ROBOT[c.key]}`);
});
test('Robot is the browser voice and is not a Chirp voice; the rest are Chirp', () => {
  assert.equal(VOICES[0].id, BROWSER_VOICE);
  assert.equal(isChirpVoice(BROWSER_VOICE), false);
  for (const v of VOICES.slice(1)) assert.ok(isChirpVoice(v.id), v.id);
  assert.equal(chirpVoiceName('Puck'), 'en-GB-Chirp3-HD-Puck');
});
test('sanitise keeps only known keys and values', () => {
  assert.deepEqual(sanitise({ hat: 'crown', glasses: 'nope', extra: 'x', voice: 7 }), { hat: 'crown' });
  assert.deepEqual(sanitise(null), {});
});
