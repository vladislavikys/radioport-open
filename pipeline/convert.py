"""Converts the songs listed in data/tracks_manifest.json from extracted .wem files to mp3 in <site>/audio."""
import json, os, subprocess, sys
from config import DATA, WORK, SITE, VGM, FFMPEG

MEDIA = os.path.join(WORK, "wem", "base", "sound", "soundbanks", "media")
OUT = os.path.join(SITE, "audio")
TMP = os.path.join(WORK, "convert_tmp.wav")


def main():
    os.makedirs(OUT, exist_ok=True)
    tracks = json.load(open(os.path.join(DATA, "tracks_manifest.json"), encoding="utf8"))
    made = 0
    for t in tracks:
        mp3 = os.path.join(OUT, t["file"])
        if os.path.exists(mp3):
            continue
        wem = os.path.join(MEDIA, f"{t['wem']}.wem")
        if not os.path.exists(wem):
            sys.exit(f"missing {wem}: run the wem extraction step first")
        subprocess.run([VGM, "-o", TMP, wem], check=True, capture_output=True)
        subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-i", TMP, "-codec:a", "libmp3lame", "-q:a", "1", mp3], check=True)
        made += 1
    if os.path.exists(TMP):
        os.remove(TMP)
    print(f"{len(tracks)} tracks, {made} converted now")


if __name__ == "__main__":
    main()
