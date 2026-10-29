"""Builds everything the site needs from your own copy of Cyberpunk 2077.

    py build.py --game "D:\\Games\\Cyberpunk 2077"   first run (the path is saved to config.json)
    py build.py                                      run every step that is not done yet
    py build.py --only sfx                           run one step
    py build.py --force dj                           redo one step even if its output exists

Steps that are already done are skipped, so after a failure just run it again.
"""
import argparse, glob, json, os, subprocess, sys, time

ROOT = os.path.dirname(os.path.abspath(__file__))
PIPE = os.path.join(ROOT, "pipeline")
CONFIG = os.path.join(ROOT, "config.json")


def save_config(**kw):
    cfg = json.load(open(CONFIG, encoding="utf8")) if os.path.exists(CONFIG) else {}
    cfg.update({k: v for k, v in kw.items() if v})
    json.dump(cfg, open(CONFIG, "w", encoding="utf8"), indent=2)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--game", help="game folder (contains archive/pc/content)")
    ap.add_argument("--wolvenkit", help="path to WolvenKit.CLI.exe")
    ap.add_argument("--vgmstream", help="path to vgmstream-cli.exe")
    ap.add_argument("--only", help="run only this step")
    ap.add_argument("--force", help="redo this step even if it is done")
    a = ap.parse_args()
    if a.game or a.wolvenkit or a.vgmstream:
        save_config(game=a.game, wolvenkit=a.wolvenkit, vgmstream=a.vgmstream)

    sys.path.insert(0, PIPE)
    import config as C

    problems = C.missing()
    if problems:
        print("Not ready yet:")
        for p in problems:
            print("  -", p)
        print("Step-by-step guide: docs/SETUP.md")
        sys.exit(1)

    tracks = json.load(open(os.path.join(C.DATA, "tracks_manifest.json"), encoding="utf8"))
    media = os.path.join(C.WORK, "wem", "base", "sound", "soundbanks", "media")
    site = lambda *p: os.path.join(C.SITE, *p)

    def wk(arc, out, regex):
        os.makedirs(out, exist_ok=True)
        r = subprocess.run([C.WK, "extract", C.archive(arc), "-o", out, "-r", regex], capture_output=True, text=True)
        if r.returncode:
            sys.exit(f"WolvenKit failed on {arc}:\n{r.stdout[-2000:]}{r.stderr[-2000:]}")

    def script(name):
        r = subprocess.run([sys.executable, os.path.join(PIPE, name)], cwd=PIPE)
        if r.returncode:
            sys.exit(f"{name} failed (exit code {r.returncode})")

    def need_mp3():
        return [t for t in tracks if not os.path.exists(site("audio", t["file"]))]

    def extract_wem():
        ids = sorted({str(t["wem"]) for t in need_mp3() if not os.path.exists(os.path.join(media, f"{t['wem']}.wem"))})
        for i in range(0, len(ids), 60):
            wk("audio_2_soundbanks.archive", os.path.join(C.WORK, "wem"), r"media\\(" + "|".join(ids[i:i + 60]) + r")\.wem$")

    def extract_dj():
        sub, subjson = os.path.join(C.WORK, "sub"), os.path.join(C.WORK, "subjson")
        wk("lang_en_text.archive", sub, r"subtitles\\media\\radio\\(radio_01_conspiracy|radio_growl)\.json$")
        os.makedirs(subjson, exist_ok=True)
        for f in glob.glob(os.path.join(sub, "**", "*.json"), recursive=True):
            subprocess.run([C.WK, "convert", "serialize", f, "-o", subjson], check=True, capture_output=True)
        wk("audio_1_general.archive", os.path.join(C.WORK, "dj"), r"radio_max_mike[^\\]*\.wem$")
        wk("lang_en_voice.archive", os.path.join(C.WORK, "dj"), r"ash_radio_growl[^\\]*\.wem$")
        script("build_dj.py")

    steps = [
        ("wem", "extract songs from the game archives", lambda: not need_mp3() or all(os.path.exists(os.path.join(media, f"{t['wem']}.wem")) for t in need_mp3()), extract_wem),
        ("audio", "convert songs to mp3", lambda: not need_mp3(), lambda: script("convert.py")),
        ("loudness", "measure song loudness", lambda: False, lambda: script("loudness.py")),
        ("data", "write site/data/tracks.js", lambda: False, lambda: script("build_data.py")),
        ("dj", "DJ voice lines", lambda: os.path.exists(site("data", "dj.js")), extract_dj),
        ("sfx", "menu sounds", lambda: len(glob.glob(site("sfx", "*.wav"))) >= 8, lambda: script("extract_ui.py")),
        ("assets", "logos, fonts and icons", lambda: os.path.exists(site("img", "growl_fm.png")) and glob.glob(site("fonts", "*.ttf")), lambda: script("extract_assets.py")),
    ]
    names = [s[0] for s in steps]
    for opt in (a.only, a.force):
        if opt and opt not in names:
            sys.exit(f"unknown step {opt!r}; steps: {', '.join(names)}")

    for n, (name, title, done, run) in enumerate(steps, 1):
        if a.only and name != a.only:
            continue
        label = f"[{n}/{len(steps)}] {name}: {title}"
        if done() and name != a.force:
            print(f"{label} ... already done")
            continue
        print(f"{label} ...", flush=True)
        t0 = time.time()
        run()
        print(f"      done in {time.time() - t0:.0f} s")

    print(f"\nReady. Start the site with:  py site/serve.py 8077   and open http://localhost:8077")


if __name__ == "__main__":
    main()
