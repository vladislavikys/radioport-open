import glob, json, os, re, subprocess
from concurrent.futures import ThreadPoolExecutor
OUT = r"C:\CP2077Radio\preview\levels.js"
cache = {}
if os.path.exists(r"C:\CP2077Radio\work\levels.json"):
    cache = json.load(open(r"C:\CP2077Radio\work\levels.json"))

def level(p):
    i = os.path.basename(p)[:-4]
    if i in cache: return i, cache[i]
    # middle 60 s of the clip is more representative than the intro
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p], capture_output=True, text=True).stdout or 0)
    ss = max(0, dur / 2 - 30)
    o = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-ss", str(ss), "-t", "60", "-i", p, "-af", "volumedetect", "-f", "null", "-"], capture_output=True, text=True).stderr
    m = re.search(r"mean_volume: (-?[\d.]+) dB", o); x = re.search(r"max_volume: (-?[\d.]+) dB", o)
    return i, [float(m.group(1)), float(x.group(1))] if m and x else None

files = [p for p in glob.glob(r"C:\CP2077Radio\preview\audio\*.mp3") if os.path.getsize(p) > 1000]
with ThreadPoolExecutor(2) as ex:
    for i, v in ex.map(level, files):
        if v: cache[i] = v
json.dump(cache, open(r"C:\CP2077Radio\work\levels.json", "w"))
open(OUT, "w").write("window.LEVELS = " + json.dumps(cache, separators=(",", ":")) + ";\n")
print("levels:", len(cache))
