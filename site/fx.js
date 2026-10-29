/* UI sounds (real game samples, synth fallback) + spectrum analyser. One AudioContext for everything. */
window.FX = (() => {
  let ctx = null, master = null, noise = null, analyser = null, bins = null;
  const buf = {};                       // decoded samples from sfx/*.wav
  const fx = { on: true, level: 0.8 };
  try { fx.on = localStorage.getItem('cp-fx') !== '0'; } catch {}

  const SAMPLES = ['hover', 'click', 'up', 'down', 'tune1', 'tune2', 'tune3'];

  function init(audioEls) {
    if (ctx) return;
    const AC = window.AudioContext || window.webkitAudioContext;
    if (!AC) return;
    ctx = new AC();
    master = ctx.createGain(); master.gain.value = fx.level; master.connect(ctx.destination);

    noise = ctx.createBuffer(1, Math.floor(ctx.sampleRate * 0.3), ctx.sampleRate);
    const d = noise.getChannelData(0);
    for (let i = 0; i < d.length; i++) d[i] = Math.random() * 2 - 1;

    // game samples; until they arrive the synth fallback below plays
    SAMPLES.forEach((n) => {
      fetch(`sfx/${n}.wav`).then((r) => r.arrayBuffer()).then((a) => ctx.decodeAudioData(a)).then((b) => { buf[n] = b; }).catch(() => {});
    });

    // analyser only on http(s): a media element from file:// is cross-origin and would go silent
    const els = [].concat(audioEls || []);
    if (els.length && /^https?:$/.test(location.protocol)) {
      try {
        analyser = ctx.createAnalyser(); analyser.fftSize = 256; analyser.smoothingTimeConstant = 0.78;
        bins = new Uint8Array(analyser.frequencyBinCount);
        analyser.connect(ctx.destination);
        els.forEach((el) => ctx.createMediaElementSource(el).connect(analyser));
      } catch { analyser = null; }
    }
  }

  const ready = () => ctx && fx.on && (ctx.state === 'running' || (ctx.resume(), true));

  function sample(name, gain = 1) {
    const b = buf[name]; if (!b) return false;
    const s = ctx.createBufferSource(), g = ctx.createGain();
    s.buffer = b; g.gain.value = gain; s.connect(g); g.connect(master); s.start();
    return true;
  }
  function tone(freq, dur, gain, type = 'square', when = 0, slide = 0) {
    const t = ctx.currentTime + when, o = ctx.createOscillator(), g = ctx.createGain();
    o.type = type; o.frequency.setValueAtTime(freq, t);
    if (slide) o.frequency.exponentialRampToValueAtTime(freq * slide, t + dur);
    g.gain.setValueAtTime(0.0001, t);
    g.gain.exponentialRampToValueAtTime(gain, t + 0.004);
    g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
    o.connect(g); g.connect(master); o.start(t); o.stop(t + dur + 0.02);
  }
  function staticBurst() {
    const t = ctx.currentTime, s = ctx.createBufferSource(), f = ctx.createBiquadFilter(), g = ctx.createGain();
    s.buffer = noise; f.type = 'bandpass'; f.Q.value = 0.9;
    f.frequency.setValueAtTime(900, t); f.frequency.exponentialRampToValueAtTime(3600, t + 0.2);
    g.gain.setValueAtTime(0.0001, t); g.gain.exponentialRampToValueAtTime(0.45, t + 0.02); g.gain.exponentialRampToValueAtTime(0.0001, t + 0.24);
    s.connect(f); f.connect(g); g.connect(master); s.start(t); s.stop(t + 0.26);
  }

  // station change: one of the three real "radio select" sounds from the game
  fx.static = () => {
    if (!ready()) return;
    const n = 'tune' + (1 + ((Math.random() * 3) | 0));
    if (!sample(n, 0.9)) staticBurst();
  };
  fx.tick = () => { if (ready() && !sample('hover', 0.55)) tone(1900, 0.018, 0.05); };
  fx.confirm = () => { if (ready() && !sample('click', 0.8)) { tone(880, 0.05, 0.1); tone(1320, 0.07, 0.1, 'square', 0.055); } };
  fx.vol = (dir) => { if (ready() && !sample(dir > 0 ? 'up' : 'down', 0.5)) tone(dir > 0 ? 900 : 600, 0.03, 0.07, 'triangle'); };
  fx.setLevel = (v) => { fx.level = v; if (master) master.gain.value = Math.max(0.15, v); };
  fx.toggle = () => {
    fx.on = !fx.on;
    try { localStorage.setItem('cp-fx', fx.on ? '1' : '0'); } catch {}
    if (fx.on) fx.confirm();
    return fx.on;
  };
  fx.resume = () => { if (ctx && ctx.state === 'suspended') ctx.resume(); };
  fx.init = init;

  // returns { bins (0..255), bass 0..1 } or null
  fx.spectrum = () => {
    if (!analyser) return null;
    analyser.getByteFrequencyData(bins);
    let b = 0; for (let i = 1; i < 6; i++) b += bins[i];
    // modern masters sit near full scale in the low bins, so only the part above ~55% counts as a "hit"
    return { bins, bass: Math.max(0, Math.min(1, (b / (5 * 255) - 0.55) / 0.45)) };
  };
  return fx;
})();
