"""radio.bnk -> songs.json: for every music event `mus_radio_NN_<name>` find the Wwise segment, its track and
the streamed wem id(s).  Needs map.py to have produced radio_map.json first."""
import sys, os, json, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bnk

WORK = os.environ.get("CP2077_WORK", r"C:\CP2077Radio\work")
m = json.load(open(os.path.join(WORK, "radio_map.json")))
d, s = bnk.parse(os.path.join(WORK, r"raw\base\sound\soundbanks\radio.bnk"))
H = bnk.hirc(d, s)
byid = {i: (t, b) for t, i, b in H}
tracks = {i: struct.unpack_from("<I", b, 10)[0] for t, i, b in H if t == 11}   # music track -> first source id

res = {}
for v in m["events"].values():
    n = v["name"]
    if n and n.startswith("mus_radio") and v["targets"] and v["targets"][0] in byid:
        b = byid[v["targets"][0]][1]            # the event points at a music segment
        ch = [x for x in (struct.unpack_from("<I", b, k)[0] for k in range(len(b) - 3)) if x in tracks]
        res[n] = [tracks[c] for c in ch]
json.dump(res, open(os.path.join(WORK, "songs_regen.json"), "w"), indent=1)
print(len(res), "events resolved")
