import struct, subprocess, os
from config import WORK, SITE, WK, VGM as V, archive

OPUS = os.path.join(WORK, "opus")
BASE = os.path.join(OPUS, "base", "sound", "soundbanks")
ARC = archive("audio_2_soundbanks.archive")
OUT = os.path.join(SITE, "sfx")
UISFX = os.path.join(WORK, "uisfx")
for d in (OUT, UISFX, OPUS):
    os.makedirs(d, exist_ok=True)

WANT = {
    'hover': [435721760], 'up': [439494209], 'down': [672820504], 'click': [142422666], 'scroll': [320535026],
    'tune1': [414259486], 'tune2': [85194135], 'tune3': [1056515661],
}
info = os.path.join(BASE, "sfx_container.opusinfo")
if not os.path.exists(info):
    subprocess.run([WK, "extract", ARC, "-o", OPUS, "-r", r"sfx_container\.opusinfo$"], check=True, capture_output=True)
d = open(info, "rb").read()
n1 = struct.unpack_from("<I", d, 12)[0]; t2 = 20 + 6 * n1
ids = struct.unpack_from("<%dI" % n1, d, 20); packs = struct.unpack_from("<%dH" % n1, d, 20 + 4 * n1)
offs = struct.unpack_from("<%dI" % (n1 + 1), d, t2)

need = {}
for nm, (sid,) in WANT.items():
    i = ids.index(sid); need[nm] = (packs[i], i)
for pk in sorted({p for p, _ in need.values()}):
    path = os.path.join(BASE, f"sfx_container_{pk}.opuspak")
    if not os.path.exists(path):
        subprocess.run([WK, "extract", ARC, "-o", OPUS, "-r", rf"sfx_container_{pk}\.opuspak$"], check=True, capture_output=True)
done = {}
for nm, (pk, i) in need.items():
    pak = open(os.path.join(BASE, f"sfx_container_{pk}.opuspak"), "rb").read()
    a = offs[i]
    nxt = min([o for o, p in zip(offs, packs) if p == pk and o > a] or [len(pak)])
    w = os.path.join(UISFX, f"{nm}.wem")
    open(w, "wb").write(pak[a:nxt])
    wav = os.path.join(OUT, f"{nm}.wav")
    subprocess.run([V, "-o", wav, w], check=True, capture_output=True)
    done[nm] = (pk, nxt - a, os.path.getsize(wav))
print(done)
