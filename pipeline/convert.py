"""Converts the songs listed in data/tracks_manifest.json from extracted .wem files to mp3 in <site>/audio."""
import json, os, subprocess
from config import DATA, WORK, SITE, VGM, FFMPEG

MEDIA = os.path.join(WORK, "wem", "base", "sound", "soundbanks", "media")
OUT = os.path.join(SITE, "audio")
TMP = os.path.join(WORK, "convert_tmp.wav")


def main():
    os.makedirs(OUT, exist_ok=True)
    tracks = json.load(open(os.path.join(DATA, "tracks_manifest.json"), encoding="utf8"))
    made, missing = 0, []
    for t in tracks:
        mp3 = os.path.join(OUT, t["file"])
        if os.path.exists(mp3):
            continue
        wem = os.path.join(MEDIA, f"{t['wem']}.wem")
        if not os.path.exists(wem):
            missing.append(t["file"])            # not in this version of the game: the site just leaves the song out
            continue
        subprocess.run([VGM, "-o", TMP, wem], check=True, capture_output=True)
        subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-i", TMP, "-codec:a", "libmp3lame", "-q:a", "1", mp3], check=True)
        made += 1
    if os.path.exists(TMP):
        os.remove(TMP)
    print(f"{len(tracks)} tracks, {made} converted now")
    if missing:
        print(f"warning: {len(missing)} songs are not in your game files and are skipped: {', '.join(missing[:5])}"
              + (" ..." if len(missing) > 5 else ""))


if __name__ == "__main__":
    main()
