import sys; sys.path.insert(0, r"C:\CP2077Radio\work")
import json, os, re, struct, subprocess, glob, time, bnk

WK = r"C:\CP2077Radio\tools\wolvenkit\WolvenKit.CLI.exe"
V = r"C:\CP2077Radio\tools\vgmstream\vgmstream-cli.exe"
ARC = r"D:\Games\Cyberpunk 2077\archive\pc\content\audio_2_soundbanks.archive"
MEDIA = r"C:\CP2077Radio\work\cand\base\sound\soundbanks\media"
OUT = r"C:\CP2077Radio\preview"
LOG = r"C:\CP2077Radio\work\preview_build.log"
os.makedirs(OUT + r"\audio", exist_ok=True)

def log(*a):
    with open(LOG, "a", encoding="utf8") as f: f.write(" ".join(str(x) for x in a) + "\n")

cand = json.load(open(r"C:\CP2077Radio\work\cand_wems.json"))
d = json.load(open(r"C:\CP2077Radio\work\arch_diff.txt", encoding="utf-8-sig"))
size = {int(re.search(r"media\\(\d+)\.wem", f["Name"]).group(1)): f["Size"] for f in d["Files"].values() if f["Name"].endswith(".wem") and "media\\" in f["Name"]}

# hint: which bank mentions each source id (sound objects / music tracks)
log("scanning banks for hints")
hint = {}
cs = set(cand)
for p in sorted(glob.glob(r"C:\CP2077Radio\work\banks\base\sound\soundbanks\*.bnk")):
    name = os.path.basename(p)[:-4]
    dd, s = bnk.parse(p)
    if "HIRC" not in s: continue
    for t, i, b in bnk.hirc(dd, s):
        if t == 2 and len(b) >= 9:
            src = struct.unpack_from("<I", b, 5)[0]
            if src in cs: hint.setdefault(src, set()).add(name)
        elif t == 11:
            n = struct.unpack_from("<I", b, 1)[0]
            if 0 < n < 50:
                for k in range(n):
                    src = struct.unpack_from("<I", b, 1 + 4 + k * 14 + 5)[0]
                    if src in cs: hint.setdefault(src, set()).add(name + " (music)")
log("hints for", len(hint), "of", len(cand))

# extract in batches, convert
rows = []
done = 0
for bi in range(0, len(cand), 80):
    batch = cand[bi:bi + 80]
    rx = r"media\\(" + "|".join(str(x) for x in batch) + r")\.wem$"
    subprocess.run([WK, "extract", ARC, "-o", r"C:\CP2077Radio\work\cand", "-r", rx], capture_output=True)
    for w in batch:
        src = rf"{MEDIA}\{w}.wem"
        mp3 = rf"{OUT}\audio\{w}.mp3"
        try:
            if not os.path.exists(mp3):
                tmp = r"C:\CP2077Radio\work\pv_tmp.wav"
                subprocess.run([V, "-o", tmp, src], check=True, capture_output=True)
                subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", tmp, "-codec:a", "libmp3lame", "-b:a", "128k", mp3], check=True)
            dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", mp3], capture_output=True, text=True).stdout)
            rows.append({"id": w, "d": round(dur, 1), "mb": round(size[w] / 1048576, 2), "bank": sorted(hint.get(w, []))})
        except Exception as e:
            log("FAIL", w, e)
        done += 1
    log("progress", done, "/", len(cand))
rows.sort(key=lambda r: -r["d"])
open(OUT + r"\data.js", "w", encoding="utf8").write("window.CLIPS = " + json.dumps(rows, separators=(",", ":")) + ";\n")
log("DONE", len(rows))
