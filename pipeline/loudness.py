import glob, json, os, re, subprocess
from concurrent.futures import ThreadPoolExecutor
OUT = r"C:\CP2077Radio\work\loudness.json"
cache = json.load(open(OUT)) if os.path.exists(OUT) else {}

def lufs(p):
    f = os.path.basename(p)
    if f in cache: return f, cache[f]
    o = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", p, "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
    m = re.findall(r"I:\s+(-?[\d.]+) LUFS", o); tp = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", o)
    return f, [float(m[-1]), float(tp[-1])] if m and tp else None

files = sorted(glob.glob(r"C:\CP2077Radio\site\audio\*.mp3"))
with ThreadPoolExecutor(3) as ex:
    for f, v in ex.map(lufs, files):
        if v: cache[f] = v
json.dump(cache, open(OUT, "w"))
vals = sorted(v[0] for v in cache.values())
print("tracks:", len(vals), "min", vals[0], "p10", vals[len(vals) // 10], "median", vals[len(vals) // 2], "p90", vals[-len(vals) // 10], "max", vals[-1])
