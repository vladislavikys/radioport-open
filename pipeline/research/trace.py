import sys; sys.path.insert(0, r"C:\CP2077Radio\work")
import struct, bnk, json

def fnv(s):
    h = 2166136261
    for c in s.lower().encode():
        h = ((h * 16777619) & 0xFFFFFFFF) ^ c
    return h

WANT = ['ui_radio_select_channel', 'ui_radio_turn_on', 'ui_radio_turn_off', 'global_menu_radio_open', 'global_menu_radio_close',
        'ui_menu_hover', 'ui_menu_value_up', 'ui_menu_value_down', 'ui_menu_mouse_click', 'ui_menu_scrolling_start']
d, s = bnk.parse(r'C:\CP2077Radio\work\banks\base\sound\soundbanks\sfx_container.bnk')
H = bnk.hirc(d, s)
byid = {i: (t, b) for t, i, b in H}
print('objects', len(H), {t: sum(1 for x in H if x[0] == t) for t in sorted({x[0] for x in H})})

def u32s(b): return [struct.unpack_from('<I', b, k)[0] for k in range(len(b) - 3)]

def sources(oid, depth=0, seen=None):
    seen = seen if seen is not None else set()
    if oid in seen or oid not in byid or depth > 12: return []
    seen.add(oid)
    t, b = byid[oid]
    out = []
    if t == 2:   # sound sfx: plugin(4) streamType(1) sourceID(4) ...
        out.append((oid, 'sound', struct.unpack_from('<I', b, 5)[0], b[4], b[9] if len(b) > 9 else None))
        # b[0:4] = flags/version, layout: ulPluginID(4) @0? print raw for inspection
    else:
        for x in set(u32s(b)):
            if x in byid and x != oid:
                out += sources(x, depth + 1, seen)
    return out

for n in WANT:
    eid = fnv(n)
    t, b = byid[eid]
    cnt = b[0]
    acts = [struct.unpack_from('<I', b, 1 + 4 * k)[0] for k in range(cnt)]
    res = []
    for a in acts:
        at, ab = byid[a]
        tgt = struct.unpack_from('<I', ab, 2)[0]
        res += sources(tgt)
    print(n, 'actions', len(acts), 'sounds', len(res))
    for r in res[:6]: print('   ', r)
