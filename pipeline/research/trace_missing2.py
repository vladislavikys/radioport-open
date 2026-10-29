import sys; sys.path.insert(0, r"C:\CP2077Radio\work")
import glob, os, struct, bnk, json

# 1) where does the Nebula target object live?
NEB = 1050548145
for p in sorted(glob.glob(r'C:\CP2077Radio\work\banks\base\sound\soundbanks\*.bnk')):
    d, s = bnk.parse(p)
    if 'HIRC' not in s: continue
    for t, i, b in bnk.hirc(d, s):
        if i == NEB: print('Nebula target', NEB, 'is object type', t, 'in', os.path.basename(p), 'len', len(b))

# 2) playlists in cp_music -> sources
d, s = bnk.parse(r'C:\CP2077Radio\work\banks\base\sound\soundbanks\cp_music.bnk')
H = bnk.hirc(d, s); byid = {i: (t, b) for t, i, b in H}
emb = {i: (o, l) for i, o, l in bnk.didx(d, s)}
tracks = {}
for t, i, b in H:
    if t == 11:
        n = struct.unpack_from('<I', b, 1)[0]
        tracks[i] = [struct.unpack_from('<I', b, 1 + 4 + k * 14 + 5)[0] for k in range(n)]
segs = {i: [x for x in set(struct.unpack_from('<I', b, k)[0] for k in range(len(b) - 3)) if x in tracks] for t, i, b in H if t == 10}
res = {}
for name, pl in (('ratatata', 349239916), ('when_its_war', 938440078), ('off_the_leash', 206975410), ('user_friendly', 553022914)):
    b = byid[pl][1]
    ss = [x for x in set(struct.unpack_from('<I', b, k)[0] for k in range(len(b) - 3)) if x in segs]
    src = sorted({w for sg in ss for t in segs[sg] for w in tracks[t]})
    res[name] = src
    print(name, 'segments', len(ss), 'sources', src, 'embedded:', [w in emb for w in src])
json.dump(res, open(r'C:\CP2077Radio\work\custom_sources.json', 'w'))
