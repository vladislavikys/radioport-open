"""Makes the demo assets in demo/assets: three synthesized songs, station logos, app icons and data files.

Nothing here comes from the game. The songs are generated note by note below, the logos are
SVG drawings rendered to PNG. Needs ffmpeg (mp3 encoding) and Chrome or Edge (SVG to PNG).

    py demo/generate.py

The output is committed, so this only needs to run again after changing the music or the logos.
"""
import array, math, os, random, shutil, subprocess, sys, tempfile, wave

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "assets")
SR = 44100
CYAN = "#5ef2ff"


def hz(midi):
    return 440.0 * 2 ** ((midi - 69) / 12)


class Mix:
    def __init__(self, seconds):
        self.n = int(seconds * SR)
        self.l = array.array("f", bytes(4 * self.n))
        self.r = array.array("f", bytes(4 * self.n))

    def add(self, start, buf, gain=1.0, pan=0.0):
        i0 = int(start * SR)
        gl, gr = gain * (1 - pan) / 2 * 2 ** 0.5, gain * (1 + pan) / 2 * 2 ** 0.5
        l, r, n = self.l, self.r, self.n
        for k, v in enumerate(buf):
            i = i0 + k
            if i >= n:
                break
            l[i] += v * gl
            r[i] += v * gr

    def write(self, path):
        peak = max(max(map(abs, self.l)), max(map(abs, self.r))) or 1
        k = 0.89 / peak
        pcm = array.array("h", bytes(4 * self.n))
        for i in range(self.n):
            pcm[2 * i] = int(self.l[i] * k * 32767)
            pcm[2 * i + 1] = int(self.r[i] * k * 32767)
        with wave.open(path, "wb") as w:
            w.setnchannels(2)
            w.setsampwidth(2)
            w.setframerate(SR)
            w.writeframes(pcm.tobytes())


# instruments: each returns a mono list of samples for one hit or note

def kick(punch=1.0):
    out = []
    for i in range(int(0.38 * SR)):
        t = i / SR
        ph = 2 * math.pi * (46 * t + 95 * punch / 32 * (1 - math.exp(-32 * t)))
        out.append(math.sin(ph) * math.exp(-7 * t))
    return out


def noise_hit(length, decay, rng, bright=True):
    out, prev = [], 0.0
    for i in range(int(length * SR)):
        x = rng.uniform(-1, 1)
        v = x - prev if bright else (x + prev) / 2
        prev = x
        out.append(v * math.exp(-decay * i / SR))
    return out


def snare(rng):
    body = [math.sin(2 * math.pi * 185 * i / SR) * math.exp(-28 * i / SR) for i in range(int(0.2 * SR))]
    return [a * 0.6 + b * 0.7 for a, b in zip(body, noise_hit(0.2, 20, rng))]


def synth(freq, length, wave_="saw", cutoff=1800, attack=0.005, decay=3.0, detune=0.0):
    """Saw or square with a one-pole low-pass and an attack/exponential-decay envelope."""
    out, y = [], 0.0
    a = 1 - math.exp(-2 * math.pi * cutoff / SR)
    freqs = [freq] if not detune else [freq * 2 ** (-detune / 1200), freq, freq * 2 ** (detune / 1200)]
    phases = [random.random() for _ in freqs]
    steps = [f / SR for f in freqs]
    n = int(length * SR)
    rel = int(0.03 * SR)
    for i in range(n):
        x = 0.0
        for j in range(len(freqs)):
            phases[j] = (phases[j] + steps[j]) % 1.0
            p = phases[j]
            x += (2 * p - 1) if wave_ == "saw" else (1.0 if p < 0.5 else -1.0)
        x /= len(freqs)
        y += a * (x - y)
        t = i / SR
        env = min(1.0, t / attack) * math.exp(-decay * t)
        if i > n - rel:
            env *= (n - i) / rel
        out.append(y * env)
    return out


def bell(freq, length):
    out = []
    for i in range(int(length * SR)):
        t = i / SR
        m = math.sin(2 * math.pi * freq * 3.5 * t) * 2.2 * math.exp(-4 * t)
        out.append(math.sin(2 * math.pi * freq * t + m) * math.exp(-2.6 * t) * min(1.0, t / 0.004))
    return out


# the three demo songs

def neon_drift():
    """Synthwave, 100 BPM, A minor: arpeggio, saw bass, wide pad, gated snare."""
    rng = random.Random(1)
    bpm, bars = 100, 24
    beat = 60 / bpm
    m = Mix(bars * 4 * beat + 2)
    chords = [[57, 60, 64], [53, 57, 60], [48, 52, 55], [55, 59, 62]]   # Am F C G
    k, s = kick(), snare(rng)
    hat = noise_hit(0.06, 70, rng)
    for bar in range(bars):
        t0 = bar * 4 * beat
        ch = chords[(bar // 2) % 4]
        for root in ch:
            m.add(t0, synth(hz(root), 4 * beat, cutoff=900, attack=0.6, decay=0.15, detune=14), 0.11, pan=(root % 3 - 1) * 0.5)
        for b in range(4):
            if bar >= 2:
                m.add(t0 + b * beat, k, 0.9)
            if bar >= 4 and b in (1, 3):
                m.add(t0 + b * beat, s, 0.45)
            if bar >= 4:
                m.add(t0 + (b + 0.5) * beat, hat, 0.12, pan=0.3)
        for e in range(8):
            m.add(t0 + e * beat / 2, synth(hz(ch[0] - 24), beat / 2 * 0.9, cutoff=420, decay=2.5), 0.5)
        if bar >= 8:
            arp = ch + [ch[0] + 12]
            for e in range(16):
                note = arp[e % 4] + (12 if (e // 4) % 2 else 0)
                m.add(t0 + e * beat / 4, synth(hz(note), beat / 4, "square", cutoff=2600, decay=9), 0.13, pan=0.5 if e % 2 else -0.5)
    return m


def static_pulse():
    """Techno, 126 BPM: four-on-the-floor, off-beat hats, rolling bass, minor stab."""
    rng = random.Random(2)
    bpm, bars = 126, 32
    beat = 60 / bpm
    m = Mix(bars * 4 * beat + 2)
    k = kick(1.2)
    hat_c, hat_o = noise_hit(0.05, 80, rng), noise_hit(0.22, 14, rng)
    clap = noise_hit(0.15, 24, rng, bright=False)
    stab = [52, 55, 59, 62]
    for bar in range(bars):
        t0 = bar * 4 * beat
        root = 40 if (bar // 4) % 2 == 0 else 43
        for b in range(4):
            m.add(t0 + b * beat, k, 1.0)
            if bar >= 4:
                m.add(t0 + (b + 0.5) * beat, hat_o, 0.10, pan=0.2)
            if bar >= 8:
                m.add(t0 + (b + 0.25) * beat, hat_c, 0.07, pan=-0.4)
                m.add(t0 + (b + 0.75) * beat, hat_c, 0.07, pan=0.4)
            if bar >= 8 and b in (1, 3):
                m.add(t0 + b * beat, clap, 0.35)
            for e in (1, 2, 3):
                m.add(t0 + (b + e / 4) * beat, synth(hz(root), beat / 4 * 0.8, cutoff=300 + 60 * (bar % 8), decay=6), 0.42)
        if bar >= 12 and bar % 2 == 0:
            for off in (1.75, 3.25):
                cut = 1200 + 140 * (bar % 16)
                for n in stab:
                    m.add(t0 + off * beat, synth(hz(n + (3 if (bar // 8) % 2 else 0)), 0.35, cutoff=cut, decay=7, detune=10), 0.09, pan=-0.3)
    return m


def low_orbit():
    """Ambient downtempo, 80 BPM, D major 7: slow pads, soft kick, FM bell melody."""
    rng = random.Random(3)
    bpm, bars = 80, 20
    beat = 60 / bpm
    m = Mix(bars * 4 * beat + 4)
    chords = [[50, 54, 57, 61], [47, 50, 54, 57], [43, 47, 50, 54], [45, 49, 52, 57]]   # Dmaj7 Bm7 Gmaj7 A
    melody = [74, 73, 69, 71, 74, 76, 73, 69]
    k = kick(0.6)
    shaker = noise_hit(0.09, 35, rng)
    for bar in range(bars):
        t0 = bar * 4 * beat
        ch = chords[(bar // 2) % 4]
        if bar % 2 == 0:
            for i, n in enumerate(ch):
                m.add(t0, synth(hz(n), 8 * beat, cutoff=700, attack=1.5, decay=0.1, detune=9), 0.10, pan=-0.6 + 0.4 * i)
        m.add(t0, synth(hz(ch[0] - 12), 3.5 * beat, cutoff=260, attack=0.05, decay=0.5), 0.45)
        if bar >= 4:
            m.add(t0, k, 0.55)
            m.add(t0 + 2.5 * beat, k, 0.4)
            for e in range(8):
                m.add(t0 + e * beat / 2, shaker, 0.05 + 0.03 * (e % 2), pan=0.5)
        if bar >= 6:
            for e in range(2):
                n = melody[(bar * 2 + e) % len(melody)]
                m.add(t0 + e * 2 * beat + (0.5 * beat if e else 0), bell(hz(n), 2.5), 0.16, pan=0.25)
    return m


SONGS = [
    ("neon_fm", "NEON FM", "90.1", "neon_drift", "Neon Drift", neon_drift),
    ("static_pulse", "STATIC PULSE", "94.7", "static_pulse", "Grid Lock", static_pulse),
    ("low_orbit", "LOW ORBIT", "101.3", "low_orbit", "Satellite Hum", low_orbit),
]


# logos: plain line drawings in the panel's cyan, rendered to transparent PNG

def svg(w, h, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
            f'<g fill="none" stroke="{CYAN}" stroke-width="6" stroke-linecap="round" stroke-linejoin="round">{body}</g></svg>')


def label(x, y, text, size=34):
    return (f'<text x="{x}" y="{y}" fill="{CYAN}" stroke="none" text-anchor="middle" '
            f'font-family="Bahnschrift, Arial Narrow, sans-serif" font-weight="700" font-size="{size}" letter-spacing="3">{text}</text>')


LOGOS = {
    "neon_fm": svg(300, 220, '<path d="M60 150 L150 40 L240 150"/><path d="M90 150 L150 78 L210 150"/>'
                   '<line x1="40" y1="150" x2="260" y2="150"/>' + label(150, 200, "NEON FM")),
    "static_pulse": svg(300, 220, '<path d="M30 100 H90 L110 50 L135 150 L160 30 L185 130 L200 100 H270"/>'
                        + label(150, 200, "STATIC PULSE", 30)),
    "low_orbit": svg(300, 220, '<circle cx="150" cy="95" r="34"/><ellipse cx="150" cy="95" rx="110" ry="34" transform="rotate(-18 150 95)"/>'
                     '<circle cx="250" cy="70" r="7" fill="#5ef2ff"/>' + label(150, 200, "LOW ORBIT")),
    "no_station": svg(220, 220, '<circle cx="110" cy="110" r="70"/><line x1="61" y1="159" x2="159" y2="61"/>'),
    "favorites": svg(260, 220, '<path d="M130 185 L50 105 A42 42 0 0 1 130 55 A42 42 0 0 1 210 105 Z"/>'),
}


def icon_svg(size, pad):
    s, c = size, size / 2
    r = (s - 2 * pad) / 2
    arcs = "".join(f'<path d="M{c - r * f} {c + r * f * 0.2} A{r * f} {r * f} 0 0 1 {c + r * f} {c + r * f * 0.2}"/>' for f in (0.35, 0.6, 0.85))
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{s}" height="{s}" viewBox="0 0 {s} {s}">'
            f'<rect width="{s}" height="{s}" fill="#1a0507"/>'
            f'<g fill="none" stroke="{CYAN}" stroke-width="{s / 24:.1f}" stroke-linecap="round">{arcs}</g>'
            f'<circle cx="{c}" cy="{c + r * 0.2}" r="{s / 22:.1f}" fill="{CYAN}"/></svg>')


def find_browser():
    for p in (shutil.which("chrome"), shutil.which("msedge"), shutil.which("google-chrome"), shutil.which("chromium"),
              r"C:\Program Files\Google\Chrome\Application\chrome.exe",
              r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"):
        if p and os.path.exists(p):
            return p
    sys.exit("Chrome or Edge not found (needed to render the logos)")


def render(browser, svg_text, w, h, out, tmp):
    src = os.path.join(tmp, os.path.basename(out) + ".svg")
    open(src, "w", encoding="utf8").write(svg_text)
    subprocess.run([browser, "--headless=new", "--disable-gpu", "--hide-scrollbars", f"--screenshot={out}",
                    f"--window-size={w},{h}", "--default-background-color=00000000",
                    "file:///" + src.replace("\\", "/")], check=True, capture_output=True)


def main():
    if not shutil.which("ffmpeg"):
        sys.exit("ffmpeg not found on PATH")
    for d in ("audio", "img", "icons", "data"):
        os.makedirs(os.path.join(OUT, d), exist_ok=True)
    tmp = tempfile.mkdtemp()
    try:
        stations = [{"id": "none", "name": "NO STATION", "freq": None, "logo": "no_station", "tracks": [], "blips": []}]
        for sid, name, freq, fname, title, make in SONGS:
            print(f"synthesizing {title} ...", flush=True)
            random.seed(sid)
            wav = os.path.join(tmp, fname + ".wav")
            make().write(wav)
            mp3 = os.path.join(OUT, "audio", fname + ".mp3")
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", wav, "-af",
                            "aecho=0.8:0.6:90|170:0.22|0.12,loudnorm=I=-14:TP=-1.5",
                            "-c:a", "libmp3lame", "-b:a", "128k", mp3], check=True)
            d = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", mp3],
                                     check=True, capture_output=True, text=True).stdout)
            stations.append({"id": sid, "name": name, "freq": freq, "logo": sid, "blips": [],
                             "tracks": [{"f": fname + ".mp3", "a": "Radioport Demo", "t": title, "d": round(d, 1), "g": 0.0}]})

        browser = find_browser()
        for name, body in LOGOS.items():
            w, h = (int(v) for v in body.split('viewBox="0 0 ')[1].split('"')[0].split())
            render(browser, body, w, h, os.path.join(OUT, "img", name + ".png"), tmp)
        render(browser, icon_svg(192, 30), 192, 192, os.path.join(OUT, "icons", "icon-192.png"), tmp)
        render(browser, icon_svg(512, 80), 512, 512, os.path.join(OUT, "icons", "icon-512.png"), tmp)
        render(browser, icon_svg(512, 130), 512, 512, os.path.join(OUT, "icons", "icon-512-maskable.png"), tmp)

        import json
        js = "window.STATIONS = " + json.dumps(stations, ensure_ascii=False) + ";\n"
        open(os.path.join(OUT, "data", "tracks.js"), "w", encoding="utf8").write(js)
        open(os.path.join(OUT, "data", "dj.js"), "w", encoding="utf8").write('window.DJ = {"songs":{},"ash":[]};\n')
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("done:", OUT)


if __name__ == "__main__":
    main()
