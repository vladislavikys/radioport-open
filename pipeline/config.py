"""Paths and tools shared by every pipeline script.

Each value comes from config.json in the repo root, then from the environment, then from a default:

    game   CP2077_GAME    folder that contains archive/pc/content (your own copy of the game)
    work   CP2077_WORK    scratch folder for extracted files (default: <repo>/work)
    site   CP2077_SITE    where the generated audio, images and data go (default: <repo>/site)
    wolvenkit  WOLVENKIT  WolvenKit.CLI.exe
    vgmstream  VGMSTREAM  vgmstream-cli.exe
"""
import json, os, shutil

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(HERE, "data")

_cfg_path = os.path.join(ROOT, "config.json")
_cfg = json.load(open(_cfg_path, encoding="utf8")) if os.path.exists(_cfg_path) else {}


def _get(key, env, default=None):
    return _cfg.get(key) or os.environ.get(env) or default


def _tool(key, env, exe, *local):
    found = _get(key, env)
    if found:
        return found
    for rel in local:
        p = os.path.join(ROOT, "tools", *rel.split("/"), exe)
        if os.path.exists(p):
            return p
    return shutil.which(exe)


GAME = _get("game", "CP2077_GAME")
WORK = _get("work", "CP2077_WORK", os.path.join(ROOT, "work"))
SITE = _get("site", "CP2077_SITE", os.path.join(ROOT, "site"))
WK = _tool("wolvenkit", "WOLVENKIT", "WolvenKit.CLI.exe", "wolvenkit")
VGM = _tool("vgmstream", "VGMSTREAM", "vgmstream-cli.exe", "vgmstream")
FFMPEG = shutil.which("ffmpeg")
FFPROBE = shutil.which("ffprobe")


def archive(name):
    return os.path.join(GAME or "", "archive", "pc", "content", name)


def missing():
    """Human-readable list of what is not set up yet (empty when everything is ready)."""
    out = []
    if not GAME or not os.path.isdir(os.path.join(GAME, "archive", "pc", "content")):
        out.append("game folder: set \"game\" in config.json (the folder that contains archive/pc/content)")
    if not WK or not os.path.exists(WK):
        out.append("WolvenKit.CLI.exe: https://github.com/WolvenKit/WolvenKit/releases (set \"wolvenkit\" in config.json or put it in tools/wolvenkit)")
    if not VGM or not os.path.exists(VGM):
        out.append("vgmstream-cli.exe: https://github.com/vgmstream/vgmstream/releases (set \"vgmstream\" in config.json or put it in tools/vgmstream)")
    if not FFMPEG or not FFPROBE:
        out.append("ffmpeg and ffprobe on PATH: https://ffmpeg.org/download.html")
    return out
