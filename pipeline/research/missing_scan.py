import sys; sys.path.insert(0, r"C:\CP2077Radio\work")
import glob, os, re, struct, json, collections, bnk

def fnv(s):
    h = 2166136261
    for c in s.lower().encode():
        h = ((h * 16777619) & 0xFFFFFFFF) ^ c
    return h

raw = open(r"C:\CP2077Radio\work\raw\base\sound\event\eventsmetadata.json", "rb").read()
names = {fnv(m.decode()): m.decode() for m in set(re.findall(rb"[A-Za-z0-9_]{4,100}", raw))}
radio_ev = {i: n for i, n in names.items() if re.match(r"mus_(custom_)?radio", n, re.I)}
print("music-ish event names in metadata:", len(radio_ev))
have = set(json.load(open(r"C:\CP2077Radio\work\songs.json")).keys())

found = collections.defaultdict(list)
for p in sorted(glob.glob(r"C:\CP2077Radio\work\banks\base\sound\soundbanks\*.bnk")):
    d, s = bnk.parse(p)
    if "HIRC" not in s: continue
    for t, i, b in bnk.hirc(d, s):
        if t == 4 and i in radio_ev:
            found[radio_ev[i]].append(os.path.basename(p))
extra = {n: b for n, b in found.items() if n not in have}
print("events found in any bank:", len(found), "| already extracted:", len(found) - len(extra), "| NOT yet extracted:", len(extra))
for n, b in sorted(extra.items()): print("  ", n, b)
nobank = [n for n in radio_ev.values() if n not in found]
print("events named in metadata but in NO extracted bank:", len(nobank))
for n in sorted(nobank)[:60]: print("   ", n)
