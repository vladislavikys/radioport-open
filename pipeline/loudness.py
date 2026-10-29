"""Measures integrated loudness of every song in <site>/audio (cached in <work>/loudness.json, seeded from data/loudness.json)."""
import glob, json, os, re, shutil, subprocess
from concurrent.futures import ThreadPoolExecutor
from config import DATA, WORK, SITE, FFMPEG

OUT = os.path.join(WORK, "loudness.json")


def lufs(p, cache):
    f = os.path.basename(p)
    if f in cache:
        return f, cache[f]
    o = subprocess.run([FFMPEG, "-hide_banner", "-nostats", "-i", p, "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
    m = re.findall(r"I:\s+(-?[\d.]+) LUFS", o)
    tp = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", o)
    return f, [float(m[-1]), float(tp[-1])] if m and tp else None


def main():
    os.makedirs(WORK, exist_ok=True)
    if not os.path.exists(OUT):
        shutil.copy(os.path.join(DATA, "loudness.json"), OUT)
    cache = json.load(open(OUT))
    files = sorted(glob.glob(os.path.join(SITE, "audio", "*.mp3")))
    with ThreadPoolExecutor(3) as ex:
        for f, v in ex.map(lambda p: lufs(p, cache), files):
            if v:
                cache[f] = v
    json.dump(cache, open(OUT, "w"))
    vals = sorted(v[0] for v in cache.values())
    print("tracks:", len(vals), "min", vals[0], "median", vals[len(vals) // 2], "max", vals[-1])


if __name__ == "__main__":
    main()
