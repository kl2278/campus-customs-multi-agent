// Soft one-shot sounds made with the Web Audio API (no audio files).
// Nothing plays until the user has clicked something, and mute is remembered.

const MUTE_KEY = "campus-customs-muted";
const VOLUME = 0.08; // deliberately quiet

let ctx: AudioContext | null = null;
let muted = localStorage.getItem(MUTE_KEY) === "1";

export const sound = {
  /** Call from a click handler. Browsers only allow audio after a user gesture. */
  unlock() {
    if (!ctx) {
      const Ctor = window.AudioContext ?? (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
      if (Ctor) ctx = new Ctor();
    }
    if (ctx && ctx.state === "suspended") void ctx.resume();
  },
  isMuted: () => muted,
  setMuted(value: boolean) {
    muted = value;
    localStorage.setItem(MUTE_KEY, value ? "1" : "0");
  },
  chime: () => notes([[880, 0, 0.35], [1318.5, 0.16, 0.5]], "sine"), // ticket resolved
  blip: () => notes([[660, 0, 0.07]], "sine"), // an agent starts
  ding: () => notes([[1046.5, 0, 0.25]], "triangle"), // approval requested
  coin: () => notes([[392, 0, 0.09], [523.25, 0.08, 0.22]], "triangle", 0.9), // payment went through
  happy: () => notes([[523.25, 0, 0.08], [659.25, 0.07, 0.08], [783.99, 0.14, 0.18]], "sine"), // bone for Dan
};

/** Each entry is [frequency Hz, start offset s, duration s]. Every sound plays exactly once. */
function notes(list: [number, number, number][], type: OscillatorType, level = 1) {
  if (muted || !ctx || ctx.state !== "running") return;
  const audio = ctx;
  const now = audio.currentTime;
  for (const [freq, offset, length] of list) {
    const osc = audio.createOscillator();
    const gain = audio.createGain();
    osc.type = type;
    osc.frequency.value = freq;
    const start = now + offset;
    gain.gain.setValueAtTime(0.0001, start);
    gain.gain.exponentialRampToValueAtTime(VOLUME * level, start + 0.015);
    gain.gain.exponentialRampToValueAtTime(0.0001, start + length);
    osc.connect(gain).connect(audio.destination);
    osc.start(start);
    osc.stop(start + length + 0.03);
  }
}
