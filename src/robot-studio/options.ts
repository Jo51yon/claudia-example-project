/**
 * Robot Studio option catalogue: the single list of what can be changed on the robot.
 * The Studio's left pane renders it; the MCP tools (supabase/functions/claudia-mcp/robot.ts) carry a copy that
 * robot_parity.test.ts checks against this file, so a chat cannot ask for something the page cannot draw.
 * Voices: 'Robot' is the browser's own speech voice and always works; the rest are Google Cloud Text-to-Speech Chirp 3 HD
 * voices (name format <locale>-Chirp3-HD-<voice>), offered when the server has Chirp (useSpeech's probe).
 */
export interface RobotAttributes {
  colour: string;
  hair: string;
  glasses: string;
  hat: string;
  neckwear: string;
  voice: string;
}

export const COLOURS: Record<string, string> = {
  teal: '#4C948C',
  brass: '#C9A227',
  coral: '#E0765B',
  violet: '#8B7BD8',
  sky: '#5AA9E6',
  lime: '#8FB84E',
};

export const HAIR = ['none', 'tuft', 'mohawk', 'spikes', 'curl'] as const;
export const GLASSES = ['none', 'round', 'square', 'shades'] as const;
export const HATS = ['none', 'cap', 'tophat', 'beanie', 'crown'] as const;
export const NECKWEAR = ['none', 'bowtie', 'scarf'] as const;

export interface RobotVoice { id: string; label: string; gender: 'female' | 'male' | 'robot'; engine: 'browser' | 'chirp' }
/** Robot (browser voice), then a short, mixed selection of the 30 Chirp 3 HD voices; en-GB is the locale asked for. */
export const VOICES: RobotVoice[] = [
  { id: 'Robot', label: 'Robot', gender: 'robot', engine: 'browser' },
  { id: 'Aoede', label: 'Aoede', gender: 'female', engine: 'chirp' },
  { id: 'Kore', label: 'Kore', gender: 'female', engine: 'chirp' },
  { id: 'Leda', label: 'Leda', gender: 'female', engine: 'chirp' },
  { id: 'Zephyr', label: 'Zephyr', gender: 'female', engine: 'chirp' },
  { id: 'Puck', label: 'Puck', gender: 'male', engine: 'chirp' },
  { id: 'Charon', label: 'Charon', gender: 'male', engine: 'chirp' },
  { id: 'Fenrir', label: 'Fenrir', gender: 'male', engine: 'chirp' },
  { id: 'Orus', label: 'Orus', gender: 'male', engine: 'chirp' },
];
export const VOICE_LOCALE = 'en-GB';
export const chirpVoiceName = (id: string) => `${VOICE_LOCALE}-Chirp3-HD-${id}`;
/** The voice that always works: used whenever Chirp is not available. */
export const BROWSER_VOICE = 'Robot';
export const isChirpVoice = (id: string) => VOICES.some((v) => v.id === id && v.engine === 'chirp');

export const DEFAULT_ROBOT: RobotAttributes = {
  colour: 'teal', hair: 'tuft', glasses: 'round', hat: 'none', neckwear: 'bowtie', voice: 'Aoede',
};

export const CATEGORIES: { key: keyof RobotAttributes; label: string; options: string[] }[] = [
  { key: 'colour', label: 'Colour', options: Object.keys(COLOURS) },
  { key: 'hair', label: 'Hair', options: [...HAIR] },
  { key: 'glasses', label: 'Glasses', options: [...GLASSES] },
  { key: 'hat', label: 'Hat', options: [...HATS] },
  { key: 'neckwear', label: 'Neckwear', options: [...NECKWEAR] },
  { key: 'voice', label: 'Voice', options: VOICES.map((v) => v.id) },
];

/** Keeps only known keys and known values, so stored or chat-supplied state can never break the drawing. */
export function sanitise(input: unknown): Partial<RobotAttributes> {
  const out: Partial<RobotAttributes> = {};
  if (!input || typeof input !== 'object') return out;
  const src = input as Record<string, unknown>;
  for (const c of CATEGORIES) {
    const v = src[c.key];
    if (typeof v === 'string' && c.options.includes(v)) (out as Record<string, string>)[c.key] = v;
  }
  return out;
}
