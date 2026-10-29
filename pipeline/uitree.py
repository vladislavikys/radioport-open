import os, struct, bnk, collections, json
from config import WORK

def fnv(s):
    h = 2166136261
    for c in s.lower().encode():
        h = ((h * 16777619) & 0xFFFFFFFF) ^ c
    return h

d, s = bnk.parse(os.path.join(WORK, 'banks', 'base', 'sound', 'soundbanks', 'sfx_container.bnk'))
H = bnk.hirc(d, s)
byid = {i: (t, b) for t, i, b in H}
CONT = {i for t, i, b in H if t in (5, 6, 7, 9)}        # random/seq, switch, actor-mixer, layer
# parent id lives early in NodeBaseParams
children = collections.defaultdict(list)
for t, i, b in H:
    if t in (2, 5, 6, 7, 9):
        seen = set()
        for k in range(0, min(len(b), 80) - 3):
            x = struct.unpack_from('<I', b, k)[0]
            if x in CONT and x != i and x not in seen:
                seen.add(x); children[x].append(i)

def leaves(oid, depth=0, seen=None):
    seen = seen if seen is not None else set()
    if oid in seen or depth > 10 or oid not in byid: return []
    seen.add(oid)
    t, b = byid[oid]
    if t == 2: return [(oid, struct.unpack_from('<I', b, 5)[0], b[4])]
    out = []
    for c in children.get(oid, []): out += leaves(c, depth + 1, seen)
    return out

res = {}
for n in ['ui_radio_select_channel', 'ui_radio_turn_on', 'ui_radio_turn_off', 'ui_menu_hover', 'ui_menu_value_up', 'ui_menu_value_down', 'ui_menu_mouse_click', 'ui_menu_scrolling_start']:
    t, b = byid[fnv(n)]
    acts = [struct.unpack_from('<I', b, 1 + 4 * k)[0] for k in range(b[0])]
    tg = [struct.unpack_from('<I', byid[a][1], 2)[0] for a in acts if a in byid]
    L = []
    for x in tg: L += leaves(x)
    res[n] = L
    print(n, 'targets', [(x, byid[x][0] if x in byid else None) for x in tg], 'leaves', len(L), L[:4])
json.dump(res, open(os.path.join(WORK, 'ui_events.json'), 'w'))
