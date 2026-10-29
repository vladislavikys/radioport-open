import struct, subprocess, os, glob, json
BASE = r"C:\CP2077Radio\work\opus\base\sound\soundbanks"
WK = r"C:\CP2077Radio\tools\wolvenkit\WolvenKit.CLI.exe"
ARC = r"D:\Games\Cyberpunk 2077\archive\pc\content\audio_2_soundbanks.archive"
V = r"C:\CP2077Radio\tools\vgmstream\vgmstream-cli.exe"
OUT = r"C:\CP2077Radio\site\sfx"
os.makedirs(OUT, exist_ok=True)

WANT = {
    'hover': [435721760], 'up': [439494209], 'down': [672820504], 'click': [142422666], 'scroll': [320535026],
    'tune1': [414259486], 'tune2': [85194135], 'tune3': [1056515661],
}
d = open(BASE + r"\sfx_container.opusinfo", "rb").read()
n1 = struct.unpack_from("<I", d, 12)[0]; t2 = 20 + 6 * n1
ids = struct.unpack_from("<%dI" % n1, d, 20); packs = struct.unpack_from("<%dH" % n1, d, 20 + 4 * n1)
offs = struct.unpack_from("<%dI" % (n1 + 1), d, t2)

need = {}
for nm, (sid,) in WANT.items():
    i = ids.index(sid); need[nm] = (packs[i], i)
for pk in sorted({p for p, _ in need.values()}):
    path = BASE + rf"\sfx_container_{pk}.opuspak"
    if not os.path.exists(path):
        subprocess.run([WK, "extract", ARC, "-o", r"C:\CP2077Radio\work\opus", "-r", rf"sfx_container_{pk}\.opuspak$"], check=True, capture_output=True)
done = {}
for nm, (pk, i) in need.items():
    pak = open(BASE + rf"\sfx_container_{pk}.opuspak", "rb").read()
    a = offs[i]
    nxt = min([o for o, p in zip(offs, packs) if p == pk and o > a] or [len(pak)])
    w = rf"C:\CP2077Radio\work\uisfx\{nm}.wem"
    open(w, "wb").write(pak[a:nxt])
    subprocess.run([V, "-o", rf"{OUT}\{nm}.wav", w], check=True, capture_output=True)
    done[nm] = (pk, nxt - a, os.path.getsize(rf"{OUT}\{nm}.wav"))
print(done)
