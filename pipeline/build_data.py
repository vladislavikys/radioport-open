import json, re, collections

T = json.load(open(r'C:\CP2077Radio\work\tracks3.json', encoding='utf8'))

# station number (from event names) -> station
ST = [
    ('none',           'NO STATION',        None,  'no_station', None),
    ('pacific_dreams', 'PACIFIC DREAMS',    '88.9',  'pacific_dreams', '09'),
    ('vexelstrom',     'RADIO VEXELSTROM',  '89.3',  'vexelstrom', '02'),
    ('growl_fm',       'GROWL FM',          '89.7',  'growl_fm', '12'),
    ('royal_blue',     'ROYAL BLUE RADIO',  '91.9',  'royal_blue', '08'),
    ('night_fm',       'NIGHT FM',          '92.9',  'night_fm', '03'),
    ('samizdat',       'SAMIZDAT RADIO',    '95.2',  'samizdat', '06'),
    ('ritual',         'RITUAL FM',         '96.1',  'ritual', '11'),
    ('body_heat',      'BODY HEAT RADIO',   '98.7',  'body_heat', '05'),
    ('impulse',        'IMPULSE',           '99.9',  'impulse', '14'),
    ('the_dirge',      'THE DIRGE',         '101.9', 'the_dirge', '04'),
    ('pebkac',         'RADIO PEBKAC',      '103.5', 'pebkac', '07'),
    ('30_principales', '30 PRINCIPALES',    '106.9', '30_principales', '10'),
    ('morro_rock',     'MORRO ROCK RADIO',  '107.3', 'morro_rock', '01'),
    ('dark_star',      'DARK STAR',         '107.5', 'dark_star', '13'),
]
by_num = {s[4]: s[0] for s in ST if s[4]}

# manual titles for tracks without a localization key
MANUAL = {
    'mus_radio_04_hiphop_yugen_blakrok': 'Blakrok - Yugen',
    'mus_radio_14impls_djset_pyramid_edit': 'Impulse - DJ Set (Pyramid Edit)',
    'mus_radio_14_impulse_djset': 'Impulse - DJ Set',
}

# loudness match: element volume can only go down, so every song is attenuated to the level of a
# fairly quiet one (20th percentile); quieter songs stay as they are
import os
LUFS = json.load(open(r'C:\CP2077Radio\work\loudness.json')) if os.path.exists(r'C:\CP2077Radio\work\loudness.json') else {}
_vals = sorted(v[0] for v in LUFS.values())
TARGET = _vals[len(_vals) // 5] if _vals else None
def gain_db(f):
    if TARGET is None or f not in LUFS: return 0
    return round(min(0.0, TARGET - LUFS[f][0]), 1)

stations = {}
blips = collections.defaultdict(list)
for t in T:
    sid = by_num.get(t['station'])
    if not sid:
        continue
    if 'blips' in t['event']:
        blips[sid].append(t['file'])
        continue
    title = MANUAL.get(t['event']) or t.get('title')
    if not title or t['duration'] < 60:
        continue
    artist, _, name = title.partition(' - ')
    if not name:
        artist, name = '', title
    stations.setdefault(sid, {})
    key = title.lower()
    if key in stations[sid]:
        continue
    stations[sid][key] = {'f': t['file'], 'a': artist, 't': name, 'd': t['duration'], 'g': gain_db(t['file'])}

out = []
for sid, name, freq, logo, _ in ST:
    out.append({
        'id': sid, 'name': name, 'freq': freq, 'logo': logo,
        'tracks': list(stations.get(sid, {}).values()),
        'blips': blips.get(sid, []),
    })
js = 'window.STATIONS = ' + json.dumps(out, ensure_ascii=False, separators=(',', ':')) + ';\n'
open(r'C:\CP2077Radio\site\data\tracks.js', 'w', encoding='utf8').write(js)
print('loudness target (LUFS):', TARGET, '| tracks with attenuation:', sum(1 for s in out for t in s['tracks'] if t['g'] < 0))
for s in out:
    print(s['freq'], s['name'], len(s['tracks']), 'tracks', len(s['blips']), 'blips', round(sum(x['d'] for x in s['tracks']) / 60), 'min')
