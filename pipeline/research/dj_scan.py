import json, re, glob, os, subprocess, collections
V = r'C:\CP2077Radio\tools\vgmstream\vgmstream-cli.exe'

def lines(path):
    d = json.load(open(path, encoding='utf8'))
    out = {}
    for x in d['Data']['RootChunk']['root']['Data']['entries']:
        out[format(int(x['stringId']), 'x').zfill(16)] = x['femaleVariant'] or x['maleVariant']
    return out

def dur(w):
    o = subprocess.run([V, '-m', w], capture_output=True, text=True).stdout
    m = re.search(r'play duration: \d+ samples \((\d+):([\d.]+) seconds\)', o)
    return int(m.group(1)) * 60 + float(m.group(2)) if m else 0

res = {}
for label, sub, pat in (('mike', 'radio_01_conspiracy', 'radio_max_mike'), ('ash', 'radio_growl', 'ash_radio_growl')):
    L = lines(rf'C:\CP2077Radio\work\subjson\{sub}.json.json')
    rows = []
    for w in glob.glob(rf'C:\CP2077Radio\work\dj\**\{pat}*.wem', recursive=True):
        h = re.search(r'_([0-9a-f]{16})\.wem$', w).group(1)
        if h in L:
            rows.append({'h': h, 'wem': w, 'text': L[h], 'dur': dur(w)})
    rows.sort(key=lambda r: r['text'])
    res[label] = rows
    tot = sum(r['dur'] for r in rows)
    print(label, len(rows), 'lines matched,', round(tot / 60, 1), 'min total')
    c = collections.Counter('short(<6s)' if r['dur'] < 6 else 'mid(6-15s)' if r['dur'] < 15 else 'long(>15s)' for r in rows)
    print('  ', dict(c))
json.dump(res, open(r'C:\CP2077Radio\work\dj_lines.json', 'w'), ensure_ascii=False, indent=1)
for label in res:
    print('==', label)
    for r in res[label][:14]:
        print(f"  {r['dur']:5.1f}s  {r['text'][:110]}")
    song = [r for r in res[label] if re.search(r'up next|coming up|coming at you|right up|next up|here.s|Silverhand|Samurai|track', r['text'], re.I)]
    print('  -> look like song intros:', len(song))
