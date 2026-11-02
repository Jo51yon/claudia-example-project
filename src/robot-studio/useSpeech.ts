import { useCallback, useEffect, useRef, useState } from 'react';
import type { SupabaseClient } from '@supabase/supabase-js';
import { VOICE_LOCALE, chirpVoiceName, isChirpVoice } from './options';

export type SpeechEngine = 'chirp' | 'browser';

/**
 * Speaks text and reports a mouth-opening level (0..1) while it plays.
 * Chirp: the example-robot-speak edge function returns MP3 from Google Cloud Text-to-Speech; the mouth follows the
 * real audio level (Web Audio analyser). Robot: the browser's own speech voice, the mouth follows a rhythm.
 * `chirp` says whether Chirp is available (a probe of the edge function; false when signed out or not configured).
 * When it is not, or a Chirp request fails, the Robot voice speaks instead with no error shown: the page greys out the
 * Chirp voices, so what plays is always what the page says is selected. `engine` reports which voice actually played.
 */
export function useSpeech(supabase: SupabaseClient, SUPABASE_URL: string, SUPABASE_PUBLISHABLE_KEY: string, signedIn: boolean) {
  const [speaking, setSpeaking] = useState(false);
  const [mouth, setMouth] = useState(0);
  const [engine, setEngine] = useState<SpeechEngine | null>(null);
  const [note, setNote] = useState<string | null>(null);
  const [chirp, setChirp] = useState<boolean | null>(null);
  const ctxRef = useRef<AudioContext | null>(null);
  const srcRef = useRef<AudioBufferSourceNode | null>(null);
  const rafRef = useRef<number | null>(null);
  const timerRef = useRef<number | null>(null);
  const runRef = useRef(0);

  const halt = useCallback(() => {
    runRef.current += 1;
    if (rafRef.current) cancelAnimationFrame(rafRef.current);
    if (timerRef.current) window.clearInterval(timerRef.current);
    rafRef.current = null; timerRef.current = null;
    try { srcRef.current?.stop(); } catch { /* already stopped */ }
    srcRef.current = null;
    try { window.speechSynthesis?.cancel(); } catch { /* unsupported */ }
    setSpeaking(false); setMouth(0);
  }, []);
  useEffect(() => halt, [halt]);

  // Is Chirp available? Asked once per sign-in state; any failure (signed out, older function, network) means no.
  useEffect(() => {
    let live = true;
    (async () => {
      if (!signedIn) { setChirp(false); return; }
      try {
        const { data } = await supabase.auth.getSession();
        const token = data.session?.access_token;
        if (!token) { if (live) setChirp(false); return; }
        const res = await fetch(`${SUPABASE_URL}/functions/v1/example-robot-speak`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}`, apikey: SUPABASE_PUBLISHABLE_KEY },
          body: JSON.stringify({ probe: true }),
        });
        const body = res.ok ? await res.json().catch(() => ({})) : {};
        if (live) setChirp(body?.chirp === true);
      } catch { if (live) setChirp(false); }
    })();
    return () => { live = false; };
  }, [supabase, SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY, signedIn]);

  const speakBrowser = useCallback((text: string, run: number) => {
    const synth = window.speechSynthesis;
    if (!synth) { setNote('This browser has no speech voice.'); return; }
    const u = new SpeechSynthesisUtterance(text);
    u.lang = VOICE_LOCALE;
    u.onstart = () => {
      setSpeaking(true); setEngine('browser');
      timerRef.current = window.setInterval(() => setMouth(0.15 + Math.random() * 0.75), 110);
    };
    const done = () => { if (runRef.current === run) halt(); };
    u.onend = done; u.onerror = done;
    synth.speak(u);
  }, [halt]);

  const speak = useCallback(async (text: string, voice: string) => {
    const clean = text.trim().slice(0, 600);
    if (!clean) return;
    halt();
    const run = runRef.current;
    setNote(null);
    if (!chirp || !isChirpVoice(voice)) { speakBrowser(clean, run); return; }
    try {
      const { data } = await supabase.auth.getSession();
      const token = data.session?.access_token;
      if (!token) throw new Error('signed out');
      const res = await fetch(`${SUPABASE_URL}/functions/v1/example-robot-speak`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}`, apikey: SUPABASE_PUBLISHABLE_KEY },
        body: JSON.stringify({ text: clean, voice: chirpVoiceName(voice), language: VOICE_LOCALE }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        if (res.status === 401 || body?.error === 'tts_not_configured') setChirp(false);
        throw new Error(`chirp ${res.status} ${body?.error ?? ''}`);
      }
      const bytes = await res.arrayBuffer();
      if (runRef.current !== run) return;
      const ctx = ctxRef.current ?? (ctxRef.current = new AudioContext());
      await ctx.resume();
      const buffer = await ctx.decodeAudioData(bytes);
      if (runRef.current !== run) return;
      const analyser = ctx.createAnalyser();
      analyser.fftSize = 512;
      const src = ctx.createBufferSource();
      src.buffer = buffer;
      src.connect(analyser); analyser.connect(ctx.destination);
      srcRef.current = src;
      const samples = new Uint8Array(analyser.fftSize);
      const tick = () => {
        analyser.getByteTimeDomainData(samples);
        let sum = 0;
        for (let i = 0; i < samples.length; i++) { const v = (samples[i] - 128) / 128; sum += v * v; }
        setMouth(Math.min(1, Math.sqrt(sum / samples.length) * 5));
        rafRef.current = requestAnimationFrame(tick);
      };
      src.onended = () => { if (runRef.current === run) halt(); };
      setEngine('chirp'); setSpeaking(true);
      src.start();
      rafRef.current = requestAnimationFrame(tick);
    } catch (e) {
      if (runRef.current !== run) return;
      console.info('Robot Studio: Chirp did not answer, the Robot voice spoke instead.', e instanceof Error ? e.message : e);
      speakBrowser(clean, run);
    }
  }, [halt, speakBrowser, chirp, supabase, SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY]);

  return { speak, stop: halt, speaking, mouth, engine, note, chirp };
}
