import json, os, re, subprocess, sys
V = r'C:\CP2077Radio\tools\vgmstream\vgmstream-cli.exe'
MEDIA = r'C:\CP2077Radio\work\wem\base\sound\soundbanks\media'
OUT = r'C:\CP2077Radio\site\audio'
TMP = r'C:\CP2077Radio\work\tmp.wav'
songs = json.load(open(r'C:\CP2077Radio\work\songs.json'))
os.makedirs(OUT, exist_ok=True)
tracks = []
for name, srcs in sorted(songs.items()):

    m = re.match(r'mus_radio_(\d\d)_?(.*)', name)
    if not m: continue
    st, rest = m.group(1), m.group(2)
    wem = os.path.join(MEDIA, f'{srcs[0]}.wem')
    mp3 = os.path.join(OUT, f'{name[10:]}.mp3')
    if not os.path.exists(mp3):
        subprocess.run([V, '-o', TMP, wem], check=True, capture_output=True)
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', TMP, '-codec:a', 'libmp3lame', '-q:a', '1', mp3], check=True)
    dur = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', mp3], capture_output=True, text=True).stdout)
    tracks.append({'event': name, 'station': st, 'rest': rest, 'wem': srcs[0], 'file': os.path.basename(mp3), 'duration': round(dur, 1)})
json.dump(tracks, open(r'C:\CP2077Radio\work\tracks.json', 'w'), indent=1)
if os.path.exists(TMP): os.remove(TMP)
print(len(tracks))
