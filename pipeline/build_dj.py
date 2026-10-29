import json, re, os, subprocess, glob, collections
from config import WORK, SITE, VGM as V, FFMPEG, FFPROBE

OUT = os.path.join(SITE, 'dj')
TMP = os.path.join(WORK, 'dj_tmp.wav')
os.makedirs(OUT, exist_ok=True)

src = open(os.path.join(SITE, 'data', 'tracks.js'), encoding='utf8').read()
S = json.loads(src[src.index('=') + 1:].strip().rstrip(';'))
norm = lambda s: re.sub(r'[^a-z0-9]', '', s.lower())
by_title = collections.defaultdict(list)
for s in S:
    for t in s['tracks']:
        by_title[norm(t['t'])].append(t['f'])

def entries(path):
    return json.load(open(path, encoding='utf8'))['Data']['RootChunk']['root']['Data']['entries']

def wem_for(h, pat):
    m = glob.glob(os.path.join(WORK, 'dj', '**', f'{pat}*_{h}.wem'), recursive=True)
    return m[0] if m else None

def to_mp3(wem, name):
    mp3 = os.path.join(OUT, name + '.mp3')
    # voice clips are mixed far below the music in the game files: bring them to music level
    subprocess.run([V, '-o', TMP, wem], check=True, capture_output=True)
    subprocess.run([FFMPEG, '-y', '-loglevel', 'error', '-i', TMP, '-af', 'loudnorm=I=-11:TP=-0.5:LRA=6', '-ar', '44100', '-codec:a', 'libmp3lame', '-q:a', '3', mp3], check=True)
    r = subprocess.run([FFPROBE, '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', mp3], capture_output=True, text=True).stdout
    return float(r)

# A: Max Mike song intros / outros
songs = collections.defaultdict(lambda: {'intro': [], 'outro': []})
n_mm = 0
for e in entries(os.path.join(WORK, 'subjson', 'radio_01_conspiracy.json.json')):
    h = format(int(e['stringId']), 'x').zfill(16); t = e['femaleVariant']
    hit = None
    for q in re.findall(r'["\u201c]([^"\u201d]+)["\u201d]', t):
        if norm(q) in by_title: hit = norm(q); break
    if not hit: continue
    w = wem_for(h, 'radio_max_mike')
    if not w: continue
    kind = 'outro' if re.search(r'\b(that was|that is|you just heard|was)\b', t, re.I) else 'intro'
    d = to_mp3(w, 'mm_' + h)
    for f in by_title[hit]:
        songs[f][kind].append({'f': 'dj/mm_' + h + '.mp3', 'd': round(d, 1), 't': t})
    n_mm += 1

# B: Ash (Growl FM) self-contained lines
BAD_START = re.compile(r"^(and|but|or|so|yeah|well|then|plus|because|'cause|\u2019cause|cause|which|that|if|now|also|anyway|still|ok|okay|right)\b", re.I)
ash = []
for e in entries(os.path.join(WORK, 'subjson', 'radio_growl.json.json')):
    h = format(int(e['stringId']), 'x').zfill(16); t = (e['femaleVariant'] or '').strip()
    if len(t) < 28 or BAD_START.match(t.lstrip('"\u201c\u2018\'')) or not re.search(r'[.!?\u2026"\u201d]$', t): continue
    w = wem_for(h, 'ash_radio_growl')
    if not w: continue
    d = to_mp3(w, 'ash_' + h)
    if d < 3 or d > 16: continue
    ash.append({'f': 'dj/ash_' + h + '.mp3', 'd': round(d, 1), 't': t})

js = 'window.DJ = ' + json.dumps({'songs': songs, 'ash': ash}, ensure_ascii=False, separators=(',', ':')) + ';\n'
open(os.path.join(SITE, 'data', 'dj.js'), 'w', encoding='utf8').write(js)
if os.path.exists(TMP): os.remove(TMP)
print('Max Mike lines used:', n_mm, '| songs covered:', len(songs), '| Ash lines kept:', len(ash))
tot = sum(os.path.getsize(p) for p in glob.glob(os.path.join(OUT, '*.mp3')))
print('dj folder MB:', round(tot / 1048576, 1))
for f, v in list(songs.items())[:6]:
    print(' ', f, 'intro', len(v['intro']), 'outro', len(v['outro']))
for a in ash[:6]: print('  ASH', a['d'], a['t'][:90])
