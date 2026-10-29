"""Extract the UI assets the site needs from your own copy of the game:
fonts (Blender Pro, Rajdhani), station logos (cropped from the game's radio icon atlas and tinted cyan),
PWA icons and the "MY MIX" logo.

    py extract_assets.py [--out <site dir>]

Paths and tools come from config.py (config.json in the repo root, or environment variables).
"""
import argparse, json, os, shutil, struct, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
from config import GAME, WK, SITE, archive
ARCHIVES = [archive(n) for n in ("basegame_1_engine.archive", "basegame_4_gamedata.archive")]

# atlas part name in the game -> file name used by the site
LOGOS = {"30_principales": "30_principales", "body_heat": "body_heat", "dark_star": "dark_star", "growl_fm": "growl_fm",
         "impulse_999": "impulse", "morro_rock": "morro_rock", "night_fm": "night_fm", "no_station": "no_station",
         "pacific_dreams": "pacific_dreams", "radio_pebkac": "pebkac", "radio_samizdat": "samizdat", "ritual": "ritual",
         "royal_blue": "royal_blue", "the_dirge": "the_dirge", "vexElsTrom": "vexelstrom"}
FONTS = ["blender/bold/blenderpro-bold", "blender/book/blenderpro-book", "raj/raj-bold", "raj/raj-medium"]
CYAN = "colorchannelmixer=rr=0.34:gg=0.95:bb=0.97"   # white logo -> cyan, alpha is kept

def run(*a):
    r = subprocess.run(a, capture_output=True, text=True)
    if r.returncode: sys.exit(f"command failed: {' '.join(a)}\n{r.stdout}{r.stderr}")
    return r.stdout

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default=SITE); a = ap.parse_args()
    out = a.out
    for d in ("img", "fonts", "icons"): os.makedirs(os.path.join(out, d), exist_ok=True)
    tmp = tempfile.mkdtemp(prefix="cp2077_assets_")
    ex = os.path.join(tmp, "ex")

    print("1/5 extracting from the game archives ...")
    for arc in ARCHIVES:
        run(WK, "extract", arc, "-o", ex, "-r", r"(radiostations_icons\.(xbm|inkatlas)|fonts\\(blender|raj)\\.*\.fnt)$")

    print("2/5 fonts ...")
    os.makedirs(os.path.join(tmp, "fonts"), exist_ok=True)      # WolvenKit refuses an output dir that does not exist
    for f in FONTS:
        src = os.path.join(ex, "base", "gameplay", "gui", "fonts", *f.split("/")) + ".fnt"
        run(WK, "export", src, "-o", os.path.join(tmp, "fonts"), "-gp", GAME)
        shutil.copy(os.path.join(tmp, "fonts", os.path.basename(f) + ".ttf"), os.path.join(out, "fonts"))

    print("3/5 logo atlas ...")
    icons = os.path.join(ex, "base", "gameplay", "gui", "common", "icons")
    run(WK, "export", os.path.join(icons, "radiostations_icons.xbm"), "-o", tmp, "-gp", GAME, "--uext", "png")
    atlas_png = os.path.join(tmp, "radiostations_icons.png")
    os.makedirs(os.path.join(tmp, "j"), exist_ok=True)
    run(WK, "convert", "serialize", os.path.join(icons, "radiostations_icons.inkatlas"), "-o", os.path.join(tmp, "j"))
    j = json.load(open(os.path.join(tmp, "j", "radiostations_icons.inkatlas.json"), encoding="utf-8-sig"))
    parts = j["Data"]["RootChunk"]["slots"]["Elements"][0]["parts"]
    W, H = struct.unpack(">II", open(atlas_png, "rb").read(24)[16:24])

    print("4/5 cropping and tinting logos ...")
    n = 0
    for p in parts:
        name = LOGOS.get(p["partName"]["$value"])
        if not name: continue
        c = p["clippingRectInUVCoords"]
        x, y, w, h = int(c["Left"] * W), int(c["Top"] * H), int((c["Right"] - c["Left"]) * W), int((c["Bottom"] - c["Top"]) * H)
        run("ffmpeg", "-y", "-loglevel", "error", "-i", atlas_png, "-vf", f"crop={w}:{h}:{x}:{y},format=rgba,{CYAN}", os.path.join(out, "img", name + ".png"))
        n += 1
    print(f"   {n} logos")

    print("5/5 icons and the MY MIX logo ...")
    ring = os.path.join(out, "img", "no_station.png")
    for size, logo, fn in ((512, 300, "icon-512.png"), (512, 240, "icon-512-maskable.png")):
        run("ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", f"color=c=0x1a0507:s={size}x{size}", "-i", ring,
            "-filter_complex", f"[1:v]scale={logo}:-1[l];[0:v][l]overlay=(W-w)/2:(H-h)/2", "-frames:v", "1", os.path.join(out, "icons", fn))
    run("ffmpeg", "-y", "-loglevel", "error", "-i", os.path.join(out, "icons", "icon-512.png"), "-vf", "scale=192:192", os.path.join(out, "icons", "icon-192.png"))
    ft = os.path.join(out, "fonts", "blenderpro-bold.ttf").replace("\\", "/").replace(":", r"\:")
    run("ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "color=c=black@0:s=360x220,format=rgba", "-vf",
        f"drawtext=fontfile='{ft}':text='MY MIX':fontcolor=0x57f0f7:fontsize=96:x=(w-text_w)/2:y=34,"
        f"drawtext=fontfile='{ft}':text='FAVORITES':fontcolor=0x57f0f7:fontsize=40:x=(w-text_w)/2:y=150,"
        "drawbox=x=40:y=138:w=280:h=3:color=0x57f0f7@1:t=fill", "-frames:v", "1", os.path.join(out, "img", "favorites.png"))
    shutil.rmtree(tmp, ignore_errors=True)
    print("done ->", out)

if __name__ == "__main__":
    main()
