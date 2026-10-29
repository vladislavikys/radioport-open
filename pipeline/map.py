import os, struct, re, json, bnk
from config import WORK

def fnv(s):
    h = 2166136261
    for c in s.lower().encode():
        h = ((h * 16777619) & 0xFFFFFFFF) ^ c
    return h

names = {}
raw = open(os.path.join(WORK, "raw", "base", "sound", "event", "eventsmetadata.json"), 'rb').read()
for m in set(re.findall(rb"[A-Za-z0-9_]{4,100}", raw)):
    names[fnv(m.decode())] = m.decode()

d, s = bnk.parse(os.path.join(WORK, "raw", "base", "sound", "soundbanks", "radio.bnk"))
H = bnk.hirc(d, s)
byid = {i: (t, b) for t, i, b in H}
u32 = lambda b: set(struct.unpack_from('<I', b, k)[0] for k in range(len(b) - 3))

tracks = {}   # track id -> source wem id
for t, i, b in H:
    if t == 11:
        tracks[i] = struct.unpack_from('<I', b, 10)[0]

segs = {i: [x for x in u32(b) if x in tracks] for t, i, b in H if t == 10}
pls = {i: [x for x in u32(b) if x in segs] for t, i, b in H if t == 13}

# events -> actions -> target
acts = {}
for t, i, b in H:
    if t == 3:
        acts[i] = (b[0], b[1], struct.unpack_from('<I', b, 2)[0])  # scope, type, target? (v150: u8 scope, u8 type)
ev = {}
for t, i, b in H:
    if t == 4:
        n = b[0] if b[0] < 255 else 0  # v150: varint count
        ids = [struct.unpack_from('<I', b, 1 + 4 * k)[0] for k in range(n)]
        ev[i] = ids

out = {'playlists': {}, 'events': {}}
for p, sg in pls.items():
    out['playlists'][p] = {'name': names.get(p), 'segments': len(sg), 'sources': sorted({tracks[t] for sgm in sg for t in segs[sgm]})}
for e, ids in ev.items():
    tg = [acts[a][2] for a in ids if a in acts]
    out['events'][e] = {'name': names.get(e), 'targets': tg}
json.dump(out, open(os.path.join(WORK, "radio_map.json"), 'w'), indent=1)
print('tracks', len(tracks), 'segs', len(segs), 'playlists', len(pls))
for p, v in out['playlists'].items():
    print(p, v['name'], v['segments'], len(v['sources']))
named = [(e, v['name']) for e, v in out['events'].items() if v['name']]
print('named events', len(named), '/', len(ev))
print([n for _, n in named][:60])
