"""Puts together the demo site: the player code from site/ plus the synthesized assets from demo/assets.

    py demo/assemble.py _site              then:  py _site/serve.py 8078   and open http://localhost:8078

Fonts: the game fonts are not available here, so the demo uses Rajdhani (SIL Open Font License).
Put Rajdhani-Medium.ttf and Rajdhani-Bold.ttf into <out>/fonts as raj-medium.ttf and raj-bold.ttf;
without them the page falls back to a system font. The Pages workflow downloads them.
"""
import os, re, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.join(os.path.dirname(HERE), "site")
ASSETS = os.path.join(HERE, "assets")
CODE = (".html", ".js", ".css", ".webmanifest")


def patch(path, pairs):
    s = open(path, encoding="utf8").read()
    for a, b in pairs:
        n = len(re.findall(a, s))
        if not n:
            sys.exit(f"{os.path.basename(path)}: pattern not found: {a}")
        s = re.sub(a, b, s)
    open(path, "w", encoding="utf8", newline="\n").write(s)


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    out = os.path.abspath(sys.argv[1])
    os.makedirs(out, exist_ok=True)
    for f in os.listdir(SITE):
        if f.endswith(CODE) or f == "serve.py":
            shutil.copy2(os.path.join(SITE, f), out)
    shutil.copytree(ASSETS, out, dirs_exist_ok=True)
    os.makedirs(os.path.join(out, "fonts"), exist_ok=True)

    # one free font family stands in for both game fonts
    patch(os.path.join(out, "style.css"), [
        (r"fonts/blenderpro-book\.ttf", "fonts/raj-medium.ttf"),
        (r"fonts/blenderpro-bold\.ttf", "fonts/raj-bold.ttf"),
    ])
    patch(os.path.join(out, "stats.html"), [
        (r"fonts/blenderpro-book\.ttf", "fonts/raj-medium.ttf"),
        (r"fonts/blenderpro-bold\.ttf", "fonts/raj-bold.ttf"),
    ])
    patch(os.path.join(out, "sw.js"), [(r"'fonts/blenderpro-[a-z]+\.ttf', ", "")])
    patch(os.path.join(out, "index.html"), [
        (r"<title>Radioport</title>", "<title>Radioport demo</title>"),
        (r"RADIOPORT // CITY-WIDE BROADCAST", "RADIOPORT // DEMO BROADCAST: SYNTH TRACKS, NO GAME FILES"),
    ])
    print("demo site:", out)


if __name__ == "__main__":
    main()
