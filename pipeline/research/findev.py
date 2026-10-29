import sys; sys.path.insert(0, r"C:\CP2077Radio\work")
import glob, os, struct, bnk

def fnv(s):
    h = 2166136261
    for c in s.lower().encode():
        h = ((h * 16777619) & 0xFFFFFFFF) ^ c
    return h

WANT = ['ui_radio_select_channel', 'ui_radio_turn_on', 'ui_radio_turn_off', 'global_menu_radio_open', 'global_menu_radio_close',
        'ui_menu_hover', 'ui_menu_value_up', 'ui_menu_value_down', 'ui_menu_mouse_click', 'ui_radio_01', 'ui_menu_scrolling_start']
ids = {fnv(n): n for n in WANT}
for p in sorted(glob.glob(r'C:\CP2077Radio\work\banks\base\sound\soundbanks\*.bnk')):
    d, s = bnk.parse(p)
    if 'HIRC' not in s: continue
    hits = [(ids[i], t) for t, i, b in bnk.hirc(d, s) if t == 4 and i in ids]
    if hits:
        print(os.path.basename(p), os.path.getsize(p), hits)
