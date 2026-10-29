import sys; sys.path.insert(0, r"C:\CP2077Radio\work")
import struct, bnk, collections

def fnv(s):
    h = 2166136261
    for c in s.lower().encode():
        h = ((h * 16777619) & 0xFFFFFFFF) ^ c
    return h

NAMES = {'radio.bnk': ['mus_radio_12_nebula'],
         'cp_music.bnk': ['mus_custom_radio_ratatata', 'mus_custom_radio_when_its_war', 'mus_custom_radio_off_the_leash', 'mus_custom_radio_user_friendly']}
for bank, evs in NAMES.items():
    d, s = bnk.parse(rf'C:\CP2077Radio\work\banks\base\sound\soundbanks\{bank}')
    H = bnk.hirc(d, s); byid = {i: (t, b) for t, i, b in H}
    embedded = {i for i, o, l in bnk.didx(d, s)}
    for n in evs:
        t, b = byid[fnv(n)]
        acts = [struct.unpack_from('<I', b, 1 + 4 * k)[0] for k in range(b[0])]
        print(bank, n, 'actions', len(acts))
        for a in acts:
            at, ab = byid[a]
            tgt = struct.unpack_from('<I', ab, 2)[0]
            tt = byid.get(tgt, (None,))[0]
            print('   action type', at, 'target', tgt, 'target obj type', tt, ab[:12].hex())
            if tt == 10:   # music segment -> track -> source
                sb = byid[tgt][1]
                tracks = {i: struct.unpack_from('<I', bb, 10)[0] for t2, i, bb in H if t2 == 11}
                ch = [x for x in (struct.unpack_from('<I', sb, k)[0] for k in range(len(sb) - 3)) if x in tracks]
                print('      segment -> tracks', ch, 'sources', [tracks[c] for c in ch], 'embedded?', [tracks[c] in embedded for c in ch])
