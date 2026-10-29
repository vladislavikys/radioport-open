(() => {
  'use strict';
  const S = window.STATIONS;
  const $ = (s) => document.querySelector(s);
  const decks = [$('#au'), $('#au2')];
  const el = {
    scaler: $('#scaler'), ui: $('#ui'), list: $('#list'), thumb: $('#sb-thumb'), title: $('#np-title'),
    vol: $('#vol-val'), artImg: $('#art-img'), artMeta: $('#art-meta'), boot: $('#boot'),
    mini: $('#mini'), miniImg: $('#mini-img'), miniTitle: $('#mini-title'),
    hist: $('#hist'), histRows: $('#hist-rows'), histThumb: $('#hist-thumb'), histCount: $('#hist-count'),
    btnSleep: $('#btn-sleep'), sleepTxt: $('#sleep-txt'),
    btnDj: $('#btn-dj'), djTxt: $('#dj-txt'),
  };
  const ROW_H = 50;
  let ROWS = 8, HROWS = 7, layoutReady = false;     // visible rows depend on the layout mode (desktop / phone portrait / phone landscape)
  const XFADE = 4.5;                       // seconds of overlap between two songs
  const SLEEP_STEPS = [0, 15, 30, 45, 60, 90];
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const DJ = window.DJ || { songs: {}, ash: [] };

  const st = {
    hi: 0, cur: -1, vol: 80, open: false, started: false, nowText: '',
    order: null, idx: 0, token: 0, failed: 0, track: null,
    d: 0,                // index of the active deck
    xf: 0,               // crossfade run id (changes cancel a running fade)
    inGap: false,
    xfDone: false,       // crossfade/gap decision already taken for this song
    gap: [],             // clips (DJ lines / jingle) to play after the current song instead of crossfading
    voice: false,        // a DJ clip is playing (gets a small level boost: the clips are quieter than the music)
    dj: true,
    view: 'stations', hh: 0, hscroll: 0,
    sleepStep: 0, sleepAt: 0, sleeping: false,
    scanning: false, scanT: 0, lost: false, retryT: 0, waitT: 0,
  };
  const gain = [1, 0];                     // per-deck level (crossfade)
  const norm = [1, 1];                     // per-deck loudness match (songs are mastered from -8 to -14 LUFS)
  let fade = 1;                            // station fade-in / sleep fade-out
  const deck = () => decks[st.d];

  // persistence
  const load = (k, def) => { try { const v = JSON.parse(localStorage.getItem(k)); return v == null ? def : v; } catch { return def; } };
  const save = (k, v) => { try { localStorage.setItem(k, JSON.stringify(v)); } catch {} };
  const store = {
    get() { return load('cp-radio', {}); },
    set() { save('cp-radio', { vol: st.vol, station: S[st.cur] ? S[st.cur].id : S[st.hi].id }); },
  };
  st.dj = load('cp-dj', true) !== false;
  // "MY FAVORITES" is a fixed list that is the same on every device: the Cyberpunk anime (Edgerunners) songs
  // that exist in the game's radio files. Nothing can be added or removed by hand.
  const FAVORITES = ['05_pop_i_want_to_stay_at_your_house.mp3'];
  try { localStorage.removeItem('cp-fav'); localStorage.removeItem('cp-fav-seed'); } catch {}   // leftovers of the old manual list
  let hist = load('cp-hist', []);          // [{f, ts, sid}] newest first

  // track index + the "my favorites" pseudo station
  const TRK = new Map();
  S.forEach((s) => s.tracks.forEach((t) => TRK.set(t.f, Object.assign({ sid: s.id, freq: s.freq, sname: s.name }, t))));
  const favStation = {
    id: 'favorites', name: 'MY FAVORITES', freq: '', logo: 'favorites', blips: [], ver: 0,
    get tracks() { return FAVORITES.map((f) => TRK.get(f)).filter(Boolean); },
  };
  S.splice(1, 0, favStation);              // right under NO STATION

  // layout: pick desktop / phone-portrait / phone-landscape, then scale the stage to the viewport
  const PANEL_W = { desk: 586, port: 400, land: 780 };
  const PANEL_H = { desk: 872, port: 770, land: 420 };      // used until the real height can be measured
  function fit() {
    const w = innerWidth, h = innerHeight, root = document.documentElement;
    const mode = h <= 520 && w > h ? 'land' : (w <= 720 && h > w * 0.9 ? 'port' : 'desk');
    root.classList.toggle('m-port', mode === 'port'); root.classList.toggle('m-land', mode === 'land');
    // phone portrait: the panel is narrow, so on a tall screen there is room for all 8 rows; short screens get fewer
    const rows = mode === 'land' ? 6 : mode === 'port' ? (h >= 740 ? 8 : h >= 640 ? 7 : 6) : 8;
    const changed = rows !== ROWS;
    ROWS = rows; HROWS = rows - 1;
    root.style.setProperty('--rows', rows);
    const ph = el.ui.offsetHeight || PANEL_H[mode];        // measured once the panel is visible
    el.scaler.style.height = ph + 'px';
    const k = Math.min(w / (PANEL_W[mode] + 24), h / (ph + 24), mode === 'desk' ? 1.4 : 1.5);
    root.style.setProperty('--k', k.toFixed(4));
    if (layoutReady && changed) { paintList(); if (st.view === 'history') paintHist(); }
  }
  addEventListener('resize', fit); addEventListener('orientationchange', () => setTimeout(fit, 120)); fit();

  // fps readout (real)
  (() => {
    const n = $('#fps-n'), ms = $('#fps-ms');
    let frames = 0, last = performance.now();
    (function loop(t) {
      frames++;
      if (t - last >= 500) {
        n.textContent = Math.round(frames * 1000 / (t - last));
        ms.textContent = ((t - last) / frames).toFixed(1) + 'ms';
        frames = 0; last = t;
      }
      requestAnimationFrame(loop);
    })(last);
  })();

  // station list
  const rows = S.map((s, i) => {
    const li = document.createElement('li');
    li.className = 'row'; li.setAttribute('role', 'option'); li.dataset.i = i;
    li.innerHTML = `<span class="ico"></span><span class="txt"><span>${s.freq ? s.freq + ' ' : ''}${s.name}</span><span class="sub"></span></span>`;
    el.list.appendChild(li);
    return li;
  });
  S.forEach((s) => { new Image().src = `img/${s.logo}.png`; });
  let scroll = 0;

  function paintList() {
    rows.forEach((r, i) => {
      r.classList.toggle('on', i === st.hi);
      r.classList.toggle('live', i === st.cur && i !== st.hi);
      r.setAttribute('aria-selected', i === st.hi);
    });
    if (st.hi < scroll) scroll = st.hi;
    if (st.hi >= scroll + ROWS) scroll = st.hi - ROWS + 1;
    scroll = Math.max(0, Math.min(scroll, S.length - ROWS));
    el.list.style.transform = `translateY(${-scroll * ROW_H}px)`;
    const h = Math.max(24, 100 * ROWS / S.length);
    el.thumb.style.height = h + '%';
    el.thumb.style.transform = `translateY(${S.length > ROWS ? ROWS * ROW_H * (1 - h / 100) * scroll / (S.length - ROWS) : 0}px)`;
  }

  // art box (follows the highlight, like the game)
  function paintArt(animate) {
    const s = S[st.hi];
    el.artImg.src = `img/${s.logo}.png`;
    el.artMeta.textContent = `IMAGE NAME: ${s.id.toUpperCase()}-0.10.${st.hi + 3}\nIMAGE TYPE: BOOT ROM KERNEL IMAGE\nLZW COMPRESSED\nLOAD ADDRESS: 0x${(0x4000 + st.hi * 0x110).toString(16).toUpperCase().padStart(8, '0')}`;
    if (animate && !reduce) {
      el.artImg.animate(
        [{ opacity: 0, transform: 'translateX(-4px)', filter: 'brightness(2)' }, { opacity: 1, transform: 'translateX(2px)', offset: 0.5 }, { opacity: 1, transform: 'none' }],
        { duration: 160, easing: 'cubic-bezier(0.23, 1, 0.32, 1)' }
      );
    }
  }

  // title scramble on track change
  let scrambleId = 0;
  function setTitle(text) {
    st.nowText = text;
    el.miniTitle.textContent = text;
    const id = ++scrambleId;
    if (st.lost) return;                    // "SIGNAL LOST" stays on screen until the stream is back
    if (reduce || !text) { el.title.textContent = text; return; }
    const GL = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789#$%&/<>';
    const t0 = performance.now(), dur = 420;
    (function tick(now) {
      if (id !== scrambleId) return;
      const p = Math.min(1, (now - t0) / dur), keep = Math.floor(text.length * p);
      el.title.textContent = text.slice(0, keep) + [...text.slice(keep)].map((c) => (c === ' ' ? ' ' : GL[(Math.random() * GL.length) | 0])).join('');
      if (p < 1) requestAnimationFrame(tick); else el.title.textContent = text;
    })(t0);
  }

  // volume (master * fade * per-deck crossfade level)
  const applyVol = () => {
    const base = Math.pow(st.vol / 100, 1.6) * fade * (st.voice ? 1.2 : 1);
    decks.forEach((a, i) => { a.volume = Math.max(0, Math.min(1, base * gain[i] * norm[i])); });
  };
  function paintVol(bump) {
    el.vol.textContent = st.vol + '%';
    applyVol();
    FX.setLevel(st.vol / 100);
    if (bump) { el.vol.classList.add('bump'); clearTimeout(paintVol.t); paintVol.t = setTimeout(() => el.vol.classList.remove('bump'), 120); }
  }
  function volBy(d) {
    const was = st.vol;
    st.vol = Math.max(0, Math.min(100, st.vol + d));
    paintVol(true); store.set();
    if (st.vol !== was) FX.vol(d);
  }
  // new station fades in under the "tune" sound
  function fadeIn() {
    if (reduce) { fade = 1; applyVol(); return; }
    const t0 = performance.now(), delay = 120, dur = 260;
    fade = 0; applyVol();
    (function step(now) {
      if (st.sleeping) return;
      const p = Math.max(0, Math.min(1, (now - t0 - delay) / dur));
      fade = p * p; applyVol();
      if (p < 1) requestAnimationFrame(step);
    })(t0);
  }

  // track popup: only while the panel is closed
  const toast = { box: $('#toast'), img: $('#toast-img'), title: $('#toast-title'), t: 0 };
  function showToast(text, logo) {
    if (st.open) return;
    const s = S[st.cur];
    text = text || st.nowText; logo = logo || (s && s.logo);
    if (!text || !logo) return;
    toast.img.src = `img/${logo}.png`;
    toast.title.textContent = text;
    toast.box.classList.add('show');
    clearTimeout(toast.t);
    toast.t = setTimeout(() => toast.box.classList.remove('show'), 4200);
  }

  // broadcast schedule: each station is a looping "live" feed
  function rng(seed) { let a = seed >>> 0; return () => { a = (a + 0x6D2B79F5) >>> 0; let t = a; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; }
  function hash(s) { let h = 2166136261; for (const c of s) h = Math.imul(h ^ c.charCodeAt(0), 16777619); return h >>> 0; }
  const sched = new Map();
  function schedule(s) {
    const key = s.id + ':' + (s.ver || 0);
    if (sched.has(key)) return sched.get(key);
    const r = rng(hash(s.id + ':night-city')), order = s.tracks.slice();
    for (let i = order.length - 1; i > 0; i--) { const j = (r() * (i + 1)) | 0; [order[i], order[j]] = [order[j], order[i]]; }
    const v = { order, total: order.reduce((a, t) => a + t.d, 0) };
    sched.set(key, v);
    return v;
  }
  function whereNow(s) {
    const { order, total } = schedule(s);
    let pos = ((Date.now() / 1000) % total + total) % total;
    for (let i = 0; i < order.length; i++) { if (pos < order[i].d) return { idx: i, off: pos }; pos -= order[i].d; }
    return { idx: 0, off: 0 };
  }

  // "on air now" line under every station
  const label = (t) => (t.a ? t.a + ' - ' : '') + t.t;
  function onAirText(s) {
    if (s.id === 'none') return '';
    if (S[st.cur] === s && st.track) return label(st.track);          // exactly what is playing
    if (!s.tracks.length) return '';
    return label(schedule(s).order[whereNow(s).idx]);                  // the schedule is deterministic, so every station's "now" is known
  }
  function paintOnAir() {
    rows.forEach((r, i) => { const el2 = r.querySelector('.sub'), t = onAirText(S[i]); if (el2.textContent !== t) el2.textContent = t; });
  }
  setInterval(() => { if (st.started) paintOnAir(); }, 8000);

  // history
  function pushHistory(t, s) {
    if (hist[0] && hist[0].f === t.f && Date.now() - hist[0].ts < 60000) return;
    hist.unshift({ f: t.f, ts: Date.now(), sid: s.id });
    hist = hist.slice(0, 60);
    save('cp-hist', hist);
  }
  const hhmm = (ts) => new Date(ts).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  const esc = (x) => String(x).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

  function renderHist() {
    const items = hist.map((h) => ({ h, t: TRK.get(h.f) })).filter((x) => x.t);
    el.histCount.textContent = items.length ? String(items.length) : '';
    if (!items.length) {
      el.histRows.innerHTML = '<li class="hist-empty">NOTHING PLAYED YET.<br>TUNE A STATION AND COME BACK.</li>';
      st.hh = 0; paintHist(); return;
    }
    st.hh = Math.min(st.hh, items.length - 1);
    el.histRows.innerHTML = items.map(({ h, t }, i) => {
      const s = S.find((x) => x.id === h.sid);
      return `<li class="hrow" data-i="${i}"><time>${hhmm(h.ts)}</time>` +
        `<span class="ht">${esc((t.a ? t.a + ' - ' : '') + t.t)}</span><span class="hs">${s && s.freq ? s.freq : ''}</span></li>`;
    }).join('');
    paintHist();
  }
  function paintHist() {
    const rowsEl = [...el.histRows.querySelectorAll('.hrow')];
    rowsEl.forEach((r, i) => r.classList.toggle('on', i === st.hh));
    if (st.hh < st.hscroll) st.hscroll = st.hh;
    if (st.hh >= st.hscroll + HROWS) st.hscroll = st.hh - HROWS + 1;
    st.hscroll = Math.max(0, Math.min(st.hscroll, Math.max(0, rowsEl.length - HROWS)));
    el.histRows.style.transform = `translateY(${-st.hscroll * ROW_H}px)`;
    const n = Math.max(1, rowsEl.length), h = Math.max(12, Math.min(100, 100 * HROWS / n));
    el.histThumb.parentElement.style.visibility = n > HROWS ? 'visible' : 'hidden';
    el.histThumb.style.height = h + '%';
    el.histThumb.style.transform = `translateY(${n > HROWS ? HROWS * ROW_H * (1 - h / 100) * st.hscroll / (n - HROWS) : 0}px)`;
  }
  function setView(v) {
    st.view = v;
    el.hist.hidden = v !== 'history';
    el.list.hidden = v === 'history';
    $('.list-wrap > .sb').hidden = v === 'history';
    $('#btn-hist').classList.toggle('on', v === 'history');
    if (v === 'history') { st.hh = 0; st.hscroll = 0; renderHist(); }
  }

  function paintDj() {
    el.btnDj.classList.toggle('on', st.dj);
    el.djTxt.textContent = st.dj ? 'DJ ON' : 'DJ OFF';
  }
  function toggleDj() {
    st.dj = !st.dj; save('cp-dj', st.dj); paintDj(); FX.confirm();
  }

  // scan: a few seconds of every station, like a real tuner
  const SCAN_MS = 4500;
  const btnScan = $('#btn-scan'), scanTxt = $('#scan-txt');
  function paintScan() { btnScan.classList.toggle('on', st.scanning); scanTxt.textContent = st.scanning ? 'SCANNING' : 'SCAN'; }
  function scanStep() {
    let i = st.cur < 0 ? st.hi : st.cur, n = S.length;
    do { i = (i + 1) % S.length; } while (!S[i].tracks.length && --n);
    st.hi = i; paintList(); paintArt(true); tune(i);
  }
  function startScan() { st.scanning = true; paintScan(); scanStep(); st.scanT = setInterval(scanStep, SCAN_MS); }
  function stopScan() { if (!st.scanning) return; st.scanning = false; clearInterval(st.scanT); paintScan(); }

  // listening statistics (invisible here; shown on stats.html)
  // seconds of real playback per device / day / song / station; DJ clips, pauses and lost signal do not count
  const dev = load('cp-dev', null) || (() => { const d = Math.random().toString(36).slice(2, 8); save('cp-dev', d); return d; })();
  const statsRows = load('cp-stats', {});
  let statsDirty = false, lastStatTick = performance.now();
  const today = () => { const d = new Date(); return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`; };
  setInterval(() => {
    const now = performance.now(), dt = Math.min(10, (now - lastStatTick) / 1000); lastStatTick = now;
    if (!st.started || !st.track || st.inGap || st.lost || st.sleeping || document.hidden && deck().paused) return;
    const a = deck(); if (a.paused || a.readyState < 3) return;
    const info = TRK.get(st.track.f); if (!info) return;
    const k = `${dev}|${today()}|${st.track.f}|${info.sid}`;
    statsRows[k] = +((statsRows[k] || 0) + dt).toFixed(1); statsDirty = true;
  }, 5000);
  setInterval(() => { if (statsDirty) { save('cp-stats', statsRows); statsDirty = false; } }, 20000);
  addEventListener('pagehide', () => { if (statsDirty) { save('cp-stats', statsRows); statsDirty = false; } });

  // lost signal: stalled or offline stream -> glitch + automatic reconnect to the live position
  function signalLost() {
    if (st.lost || st.cur < 0 || !S[st.cur] || !S[st.cur].tracks.length) return;
    st.lost = true; scrambleId++;
    el.title.classList.add('lost'); el.title.textContent = 'SIGNAL LOST - RECONNECTING';
    FX.static(); retryLoop();
  }
  function retryLoop() {
    clearTimeout(st.retryT);
    st.retryT = setTimeout(() => {
      if (!st.lost) return;
      if (navigator.onLine !== false) reconnect();
      retryLoop();
    }, 4000);
  }
  function reconnect() {                    // silent re-tune to where the broadcast is "now"
    const s = S[st.cur]; if (!s || !s.tracks.length) return;
    const w = whereNow(s); startOn(st.d, s, w.idx, w.off);
  }
  function signalBack() {
    clearTimeout(st.waitT);
    if (!st.lost) return;
    st.lost = false; clearTimeout(st.retryT);
    el.title.classList.remove('lost'); el.title.textContent = st.nowText;
  }
  addEventListener('offline', () => { if (st.started && !deck().paused) signalLost(); });
  addEventListener('online', () => { if (st.lost) reconnect(); });

  // sleep timer
  function paintSleep() {
    const on = st.sleepAt > 0;
    el.btnSleep.classList.toggle('on', on);
    if (!on) { el.sleepTxt.textContent = 'SLEEP'; return; }
    const m = Math.max(1, Math.ceil((st.sleepAt - Date.now()) / 60000));
    el.sleepTxt.textContent = `SLEEP ${m}M`;
  }
  function cycleSleep() {
    st.sleepStep = (st.sleepStep + 1) % SLEEP_STEPS.length;
    const m = SLEEP_STEPS[st.sleepStep];
    st.sleepAt = m ? Date.now() + m * 60000 : 0;
    FX.confirm(); paintSleep();
    if (!m) showToast('SLEEP TIMER OFF');
  }
  function sleepNow() {
    st.sleeping = true; st.sleepAt = 0; st.sleepStep = 0; paintSleep();
    if (document.hidden) { decks.forEach((a) => a.pause()); st.sleeping = false; fade = 1; applyVol(); return; }
    const t0 = performance.now(), dur = 8000;
    (function step(now) {
      if (!st.sleeping) return;
      const p = Math.min(1, (now - t0) / dur);
      fade = 1 - p; applyVol();
      if (p < 1) return requestAnimationFrame(step);
      decks.forEach((a) => a.pause());
      st.sleeping = false; fade = 1; applyVol();
    })(t0);
  }
  setInterval(() => {
    if (!st.sleepAt) return;
    if (Date.now() >= st.sleepAt) sleepNow(); else paintSleep();
  }, 1000);

  // playback: two decks, crossfade between songs
  function setCurrentTrack(s, t) {
    st.track = t;
    setTitle((t.a ? t.a + ' - ' : '') + t.t);
    pushHistory(t, s);
    paintOnAir();
    if (st.view === 'history') renderHist();
    showToast();
    if ('mediaSession' in navigator) {
      try { navigator.mediaSession.metadata = new MediaMetadata({ title: t.t, artist: t.a, album: s.freq ? `${s.freq} ${s.name}` : s.name, artwork: [{ src: 'icons/icon-512.png', sizes: '512x512', type: 'image/png' }] }); } catch {}
    }
  }

  // DJ mode: song intros/outros (Max Mike) and Growl FM chatter (Ash)
  const rand = (arr) => arr[(Math.random() * arr.length) | 0];
  const recentAsh = [];
  function pickAsh() {
    const pool = DJ.ash.filter((x) => !recentAsh.includes(x.f));
    const c = rand(pool.length ? pool : DJ.ash);
    recentAsh.push(c.f); if (recentAsh.length > 30) recentAsh.shift();
    return c.f;
  }
  // what plays in the gap between the current song and the next one (empty = plain crossfade)
  function planGap(s) {
    const cur = st.track, nxt = st.order[(st.idx + 1) % st.order.length];
    const gap = [];
    if (st.dj) {
      const out = cur && DJ.songs[cur.f] && DJ.songs[cur.f].outro, intro = nxt && DJ.songs[nxt.f] && DJ.songs[nxt.f].intro;
      const o = out && out.length ? rand(out).f : null, i = intro && intro.length ? rand(intro).f : null;
      if (o && Math.random() < 0.7) gap.push(o);
      if (i && Math.random() < 0.7) gap.push(i);
      if (!gap.length && (o || i)) gap.push(o || i);
      if (!gap.length && s.id === 'growl_fm' && DJ.ash.length && Math.random() < 0.55) gap.push(pickAsh());
    }
    if (!gap.length && s.blips.length && Math.random() < 0.45) gap.push('audio/' + rand(s.blips));
    return gap;
  }
  // play clips one after another on the current deck, then continue with `done`
  function playGap(a, urls, done) {
    const token = ++st.token; let i = 0;
    st.inGap = true;                        // the deck-level 'ended' handler must ignore these clips
    const step = () => {
      if (token !== st.token) return;
      if (i >= urls.length) { st.inGap = false; st.voice = false; applyVol(); return done(); }
      st.voice = urls[i].startsWith('dj/');
      norm[decks.indexOf(a)] = 1; applyVol();            // clips are already levelled
      a.src = urls[i++];
      a.addEventListener('ended', step, { once: true });
      const p = a.play(); if (p) p.catch(step);
    };
    step();
  }

  // start a song on deck `di`; `off` = seconds into it (live position)
  function startOn(di, s, idx, off) {
    const { order } = schedule(s);
    const t = order[idx], a = decks[di], token = ++st.token;
    st.order = order; st.idx = idx; st.xfDone = false; st.gap = []; st.inGap = false; st.voice = false;
    norm[di] = Math.pow(10, (t.g || 0) / 20); applyVol();
    a.src = 'audio/' + t.f;
    a.addEventListener('loadedmetadata', () => {
      if (token !== st.token) return;
      if (off > 1 && off < (a.duration || t.d) - 4) { try { a.currentTime = off; } catch {} }
      const p = a.play(); if (p) p.catch(() => {});
    }, { once: true });
    a.load();
    setCurrentTrack(s, t);
  }

  function tune(i) {
    const s = S[i];
    st.xf++; st.cur = i; st.failed = 0; st.gap = []; st.inGap = false; st.voice = false;
    FX.static(); fadeIn();
    st.sleeping = false;
    decks.forEach((a, k) => { if (k !== st.d) { a.pause(); } });
    gain[st.d] = 1; gain[1 - st.d] = 0; applyVol();
    el.miniImg.src = `img/${s.logo}.png`;
    const list = s.tracks;
    if (!list.length) {
      st.token++; deck().pause(); st.order = null; st.track = null;
      setTitle('');
      paintList(); store.set(); return;
    }
    const w = whereNow(s);
    startOn(st.d, s, w.idx, w.off);
    paintList(); store.set();
  }

  // equal-power crossfade into the next song on the idle deck
  function crossfadeToNext() {
    const s = S[st.cur]; if (!s || !st.order) return;
    const from = st.d, to = 1 - from, run = ++st.xf;
    st.d = to;                             // the new song is "current" from now on
    gain[to] = 0; applyVol();
    startOn(to, s, (st.idx + 1) % st.order.length, 0);
    if (document.hidden) {                 // rAF is frozen in the background: cut instead of fade
      decks[from].pause(); gain[from] = 0; gain[to] = 1; applyVol();
      return;
    }
    const t0 = performance.now(), dur = XFADE * 1000;
    (function step(now) {
      if (run !== st.xf) return;
      const p = Math.min(1, (now - t0) / dur);
      gain[to] = Math.sin(p * Math.PI / 2); gain[from] = Math.cos(p * Math.PI / 2); applyVol();
      if (p < 1) return requestAnimationFrame(step);
      decks[from].pause(); gain[from] = 0; gain[to] = 1; applyVol();
    })(t0);
  }

  decks.forEach((a, di) => {
    a.addEventListener('timeupdate', () => {
      if (di !== st.d || st.xfDone || !st.order || !isFinite(a.duration)) return;
      if (a.duration - a.currentTime > XFADE + 0.4) return;
      st.xfDone = true;
      const s = S[st.cur];
      st.gap = planGap(s);                 // DJ lines or a jingle play between the songs instead of a crossfade
      if (st.gap.length || reduce) return; // (reduced motion: plain cut)
      crossfadeToNext();
    });
    a.addEventListener('ended', () => {
      if (di !== st.d || st.inGap) return; // the faded-out deck / a DJ clip finishing is not "song over"
      const s = S[st.cur]; if (!s || !st.order) return;
      const next = () => startOn(st.d, s, (st.idx + 1) % st.order.length, 0);
      if (st.gap.length) { const urls = st.gap; st.gap = []; playGap(a, urls, next); } else next();
    });
    a.addEventListener('error', () => {
      if (di !== st.d) return;
      const s = S[st.cur]; if (!s || !st.order) return;
      if (navigator.onLine === false || (a.error && a.error.code === 2)) return signalLost();   // network problem: keep retrying this station
      if (++st.failed > st.order.length) return;
      setTimeout(() => startOn(st.d, s, (st.idx + 1) % st.order.length, 0), 400);               // a broken file: skip it
    });
    // buffering for more than 3 s counts as a lost signal
    const stall = () => { if (di !== st.d || a.paused) return; clearTimeout(st.waitT); st.waitT = setTimeout(() => { if (a.readyState < 3 && !a.paused && di === st.d) signalLost(); }, 3000); };
    a.addEventListener('waiting', stall); a.addEventListener('stalled', stall);
    a.addEventListener('playing', () => { if (di === st.d) { clearTimeout(st.waitT); signalBack(); } });
  });

  // open / close
  function setOpen(v) {
    st.open = v;
    el.scaler.hidden = !v; el.mini.hidden = v;
    if (v) fit();                                          // now the panel has a real height
    if (v) { el.ui.classList.remove('in'); void el.ui.offsetWidth; el.ui.classList.add('in'); }
  }

  // input
  function move(d) {
    // single steps wrap around (the list is endless); page jumps stop at the ends
    const next = (cur, n) => (Math.abs(d) === 1 ? (cur + d + n) % n : Math.max(0, Math.min(n - 1, cur + d)));
    if (st.view === 'history') {
      const n = el.histRows.querySelectorAll('.hrow').length;
      if (!n) return;
      const nh = next(st.hh, n);
      if (nh !== st.hh) { const wrap = Math.abs(nh - st.hh) > 1; st.hh = nh; if (wrap) el.histRows.style.transition = 'none'; paintHist(); if (wrap) { void el.histRows.offsetWidth; el.histRows.style.transition = ''; } FX.tick(); }
      return;
    }
    const n = next(st.hi, S.length);
    if (n === st.hi) return;
    const wrap = Math.abs(n - st.hi) > 1 && Math.abs(d) === 1;   // jumped from one end to the other: no long slide
    st.hi = n;
    if (wrap) { el.list.style.transition = 'none'; el.thumb.style.transition = 'none'; }
    paintList(); paintArt(true);
    if (wrap) { void el.list.offsetWidth; el.list.style.transition = ''; el.thumb.style.transition = ''; }
    FX.tick();
  }
  function select() {
    stopScan();
    if (st.view === 'history') return;      // the history is read-only
    FX.confirm(); tune(st.hi);
  }

  // one place for every input device; returns true when the key was used
  function act(k) {
    if (k === 'm') { FX.toggle(); return true; }
    if (k === 'c' || k === 'escape') {
      if (st.open && st.view === 'history') { setView('stations'); FX.confirm(); return true; }
      setOpen(!st.open); return true;
    }
    if (!st.open) { if (k === 'enter' || k === 'f') { setOpen(true); return true; } return false; }
    if (k === 'v') { window.open('stats.html', '_blank'); return true; }     // separate screen: the player keeps playing here
    if (k === 'x') { st.scanning ? stopScan() : startScan(); FX.confirm(); return true; }
    if (st.scanning && !['a', 'd', 'arrowleft', 'arrowright'].includes(k)) {      // any key except volume ends the scan, staying on this station
      stopScan(); FX.confirm(); if (k === 'f' || k === 'enter' || k === ' ') return true;
    }
    if (k === 'w' || k === 'arrowup') move(-1);
    else if (k === 's' || k === 'arrowdown') move(1);
    else if (k === 'a' || k === 'arrowleft') volBy(-5);
    else if (k === 'd' || k === 'arrowright') volBy(5);
    else if (k === 'f' || k === 'enter' || k === ' ') select();
    else if (k === 'y') { setView(st.view === 'history' ? 'stations' : 'history'); FX.confirm(); }
    else if (k === 't') cycleSleep();
    else if (k === 'j') toggleDj();
    else if (k === 'pagedown') move(st.view === 'history' ? HROWS : ROWS); else if (k === 'pageup') move(-(st.view === 'history' ? HROWS : ROWS));
    else return false;
    return true;
  }

  addEventListener('keydown', (e) => {
    if (e.ctrlKey || e.metaKey || e.altKey) return;
    if (!st.started) { start(); e.preventDefault(); return; }
    // physical keys first, so the Russian layout (ф/в/ы/ц/а/с/ь/р/н/е) works too
    const CODES = { KeyW: 'w', KeyS: 's', KeyA: 'a', KeyD: 'd', KeyF: 'f', KeyC: 'c', KeyM: 'm', KeyY: 'y', KeyT: 't', KeyJ: 'j', KeyX: 'x', KeyV: 'v' };
    const RU = { 'ц': 'w', 'ы': 's', 'ф': 'a', 'в': 'd', 'а': 'f', 'с': 'c', 'ь': 'm', 'н': 'y', 'е': 't', 'о': 'j', 'ч': 'x', 'м': 'v', 'і': 's', 'ї': 'd' };
    const key = e.key.toLowerCase();
    if (act(CODES[e.code] || RU[key] || key)) e.preventDefault();
  });

  // gamepad: d-pad browses, A tunes, B opens/closes, bumpers = volume, X/Y/Start = tools
  const padHeld = {};
  const PAD = { 12: 'arrowup', 13: 'arrowdown', 14: 'arrowleft', 15: 'arrowright', 0: 'f', 1: 'c', 3: 'y', 9: 't', 8: 'j', 7: 'x', 4: 'a', 5: 'd' };
  const PAD_REPEAT = new Set([12, 13, 14, 15, 4, 5]);
  function pollPad(now) {
    const pads = navigator.getGamepads ? navigator.getGamepads() : [];
    for (const p of pads) {
      if (!p) continue;
      const stickY = Math.abs(p.axes[1]) > 0.6 ? Math.sign(p.axes[1]) : 0;
      const pressed = (i) => (p.buttons[i] && p.buttons[i].pressed) || (i === 12 && stickY < 0) || (i === 13 && stickY > 0);
      for (const b in PAD) {
        const key = p.index + ':' + b, h = padHeld[key];
        if (pressed(+b)) {
          if (!h) {
            padHeld[key] = { next: now + 380 };
            if (!st.started) start(); else act(PAD[b]);
          } else if (PAD_REPEAT.has(+b) && now >= h.next) { h.next = now + 110; if (st.started) act(PAD[b]); }
        } else if (h) delete padHeld[key];
      }
    }
  }

  // spectrum in the art box
  const spec = $('#art-spec'), sctx = spec.getContext('2d'), artBox = $('#art');
  const BARS = 28;
  function drawSpec() {
    const d = FX.spectrum();
    if (!d) return;
    const w = spec.width, h = spec.height, bw = w / BARS;
    sctx.clearRect(0, 0, w, h);
    sctx.fillStyle = '#5ef0f6';
    for (let i = 0; i < BARS; i++) {
      // log-ish bin mapping so the bass is not squeezed into two bars
      const bin = Math.min(d.bins.length - 1, Math.floor(Math.pow(i / BARS, 1.6) * 70) + 1);
      const v = d.bins[bin] / 255, bh = Math.max(1, v * h);
      sctx.globalAlpha = 0.35 + v * 0.65;
      sctx.fillRect(i * bw + 1, h - bh, bw - 3, bh);
    }
    sctx.globalAlpha = 1;
    artBox.style.setProperty('--bass', d.bass.toFixed(3));
  }

  (function frame(now) {
    pollPad(now);
    if (st.open && st.started && !deck().paused && !reduce && !document.hidden) drawSpec();
    requestAnimationFrame(frame);
  })(performance.now());

  // pointer input
  el.list.addEventListener('click', (e) => {
    const r = e.target.closest('.row'); if (!r) return;
    const i = +r.dataset.i;
    if (i !== st.hi) { st.hi = i; paintList(); paintArt(true); }
    select();
  });
  el.histRows.addEventListener('click', (e) => {
    const r = e.target.closest('.hrow'); if (!r) return;
    st.hh = +r.dataset.i; paintHist();
  });
  $('.list-wrap').addEventListener('wheel', (e) => { e.preventDefault(); move(e.deltaY > 0 ? 1 : -1); }, { passive: false });
  $('#vol-dn').addEventListener('click', () => volBy(-5));
  $('#vol-up').addEventListener('click', () => volBy(5));
  $('#btn-sel').addEventListener('click', select);
  $('#btn-close').addEventListener('click', () => act('c'));
  $('#btn-hist').addEventListener('click', () => act('y'));
  el.btnSleep.addEventListener('click', () => act('t'));
  el.btnDj.addEventListener('click', () => act('j'));
  btnScan.addEventListener('click', () => act('x'));
  $('#btn-stats').addEventListener('click', () => act('v'));
  el.mini.addEventListener('click', () => setOpen(true));
  el.boot.addEventListener('click', start);

  // phone: swipe the list, lock-screen controls, keep the screen awake
  (() => {
    const wrap = $('.list-wrap'); let y0 = null, acc = 0;
    wrap.addEventListener('touchstart', (e) => { y0 = e.touches[0].clientY; acc = 0; }, { passive: true });
    wrap.addEventListener('touchmove', (e) => {
      if (y0 === null) return;
      const k = parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--k')) || 1;
      const dy = (y0 - e.touches[0].clientY) / k;       // finger up = list goes down
      const steps = Math.trunc((dy - acc) / ROW_H);
      if (steps) { move(steps); acc += steps * ROW_H; }
    }, { passive: true });
    wrap.addEventListener('touchend', () => { y0 = null; });

    if ('mediaSession' in navigator) {
      const set = (a, f) => { try { navigator.mediaSession.setActionHandler(a, f); } catch {} };
      const step = (d) => { // next / previous station that has music
        let i = st.cur < 0 ? st.hi : st.cur, n = S.length;
        do { i = (i + d + S.length) % S.length; } while (!S[i].tracks.length && --n);
        st.hi = i; paintList(); paintArt(true); tune(i);
      };
      set('play', () => { st.sleeping = false; fade = 1; applyVol(); deck().play().catch(() => {}); });
      set('pause', () => decks.forEach((a) => a.pause()));
      set('nexttrack', () => step(1));
      set('previoustrack', () => step(-1));
      const state = () => { try { navigator.mediaSession.playbackState = decks.some((a) => !a.paused) ? 'playing' : 'paused'; } catch {} };
      decks.forEach((a) => { a.addEventListener('playing', state); a.addEventListener('pause', state); });
    }

    let lock = null;
    const grab = async () => { try { if (navigator.wakeLock && !lock && st.open && !deck().paused) { lock = await navigator.wakeLock.request('screen'); lock.addEventListener('release', () => { lock = null; }); } } catch {} };
    document.addEventListener('visibilitychange', () => { if (!document.hidden) grab(); });
    decks.forEach((a) => a.addEventListener('playing', grab));
  })();

  if ('serviceWorker' in navigator && (location.protocol === 'https:' || location.hostname === 'localhost')) {
    addEventListener('load', () => navigator.serviceWorker.register('sw.js').catch(() => {}));
  }

  // boot
  function start() {
    if (st.started) return;
    st.started = true;
    FX.init(matchMedia('(pointer: coarse)').matches ? [] : decks);   // phones: plain <audio> so it keeps playing in the background
    el.boot.classList.add('gone'); setTimeout(() => (el.boot.hidden = true), 240);
    const saved = store.get();
    if (typeof saved.vol === 'number') st.vol = saved.vol;
    const si = S.findIndex((s) => s.id === saved.station);
    const def = S.findIndex((s) => s.id === 'dark_star');
    st.hi = si > 1 || (si === 1 && favStation.tracks.length) ? si : def >= 0 ? def : S.findIndex((s) => s.tracks.length);
    paintVol(false); paintList(); paintArt(false); paintSleep(); paintDj(); paintScan(); paintOnAir();
    setOpen(true);
    tune(st.hi);
  }

  paintVol(false); paintList(); paintArt(false); paintSleep(); paintDj();
  layoutReady = true;
})();
