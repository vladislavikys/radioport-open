# Radioport

**English** · [Русский](README.ru.md)

A fan-made web player that recreates the RADIOPORT screen from *Cyberpunk 2077*: 14 stations on a live schedule,
crossfade, DJ voice lines, sleep timer, stats, and support for phones and gamepads.

**[▶ Try the live demo](https://vladislavikys.github.io/radioport-open/)**. It is the same player with six synthesized tracks and no game files.

<p align="center">
  <img src="docs/img/demo.gif" alt="Radioport: switching stations" width="340">
  &nbsp;
  <img src="docs/img/mobile.png" alt="Radioport on a phone" width="220">
</p>

<p align="center">
  <img src="docs/img/desktop-full.jpg" alt="Radioport on a 1080p monitor" width="720">
</p>

> **No game files in this repository.** It contains code and extraction scripts only: no music, voices, logos or fonts
> from the game, and no links to them. The screenshots above show the interface. You build the assets yourself from
> **your own copy** of the game with one command (see [Build from your game](#build-from-your-game)).
> Keep the built site private: the music belongs to its artists and CD PROJEKT RED.
>
> Unofficial fan project, not affiliated with or endorsed by CD PROJEKT RED. *Cyberpunk 2077* is a trademark of CD PROJEKT S.A.

## Features

- **Live radio.** Every station plays on a fixed schedule. When you tune in, you land in the middle of the current song, like a real receiver. The station list shows what each station is playing right now.
- **Sound.** 4.5-second crossfade between songs, loudness matching, the game's own menu sounds, and a spectrum analyser in the station window.
- **DJs.** Max Mike introduces 15 songs, Ash talks on Growl FM, and station jingles play between songs. Toggle with `J`.
- **Extras.** Song history, sleep timer (15 to 90 minutes), station scan, and "SIGNAL LOST" with automatic reconnect when the network drops.
- **Stats** (`V`, separate page): listening time, top songs and stations, a 14-day chart. Stored only on your device.
- **Phone, TV, gamepad.** Three layouts: desktop, phone portrait (from 320 px wide) and phone landscape. Installs as a PWA, works with lock-screen media controls, swipe and gamepad.
- Controls use physical keys, so any keyboard layout works.

## Controls

| Key | Action | Gamepad |
|---|---|---|
| `W` `S` / `↑` `↓` | choose station | D-pad, left stick |
| `F` / `Enter` | tune in | A |
| `A` `D` / `←` `→` | volume ±5 | LB / RB |
| `C` / `Esc` | close / open the panel | B |
| `Y` | history | Y |
| `T` | sleep timer | Start |
| `J` | DJ on / off | Back |
| `X` | scan stations | RT |
| `V` | stats (new tab) | — |
| `M` | interface sounds on / off | — |

## Build from your game

You need an installed copy of Cyberpunk 2077. The build is tested on Windows with game version 2.31 and Phantom Liberty.

1. Install the tools:
   - Python 3 and `ffmpeg` on `PATH`;
   - [WolvenKit CLI](https://github.com/WolvenKit/WolvenKit/releases) 9.1.0;
   - [vgmstream-cli](https://github.com/vgmstream/vgmstream/releases).

   You can put WolvenKit in `tools/wolvenkit/` and vgmstream in `tools/vgmstream/`; the build finds them there.
2. Build everything with one command. The game path is saved to `config.json`:
   ```bash
   py build.py --game "D:\Games\Cyberpunk 2077"
   ```
   If a tool is missing, the script says which one and where to get it. Finished steps are skipped, so after
   an error you can run the same command again. A full build takes about 20 minutes; most of it is mp3 encoding.
3. Start the site and open http://localhost:8077:
   ```bash
   py site/serve.py 8077
   ```

The steps are `wem`, `audio`, `loudness`, `data`, `dj`, `sfx` and `assets`. Run one step with `--only <step>`, redo one with `--force <step>`.
You can also set the paths in `config.json` (copy `config.example.json`) or with environment variables.

Use `serve.py`, not `python -m http.server`: the player needs HTTP Range requests to start a song at the live position.
The spectrum only works over `http://`, not `file://`.

## Run the demo locally

```bash
py demo/assemble.py _site
py _site/serve.py 8078
```

Then open http://localhost:8078. The demo uses the code from `site/` and the files from `demo/assets`.
`demo/generate.py` synthesizes the six tracks note by note and draws the logos, so nothing in the demo comes from the game.
The demo uses the free Rajdhani font. Put `raj-medium.ttf` and `raj-bold.ttf` in `_site/fonts`, or the page uses a system font.
The live demo is published by `.github/workflows/pages.yml` on every push.

## How it works

### Getting the music out of the game

The game keeps its radio in Wwise sound banks. `pipeline/` reads them directly:

1. `radio.bnk` holds one event per song, named `mus_radio_NN_<genre>_<song>`. `NN` is the station number.
   Event names are stored as FNV-1 hashes, so the real names come from `eventsmetadata.json`.
2. Each event points through an action, a music segment and a music track to a streamed media id.
   That id is a file `media\<id>.wem` in `audio_2_soundbanks.archive`.
3. WolvenKit extracts the `.wem` files, vgmstream decodes them, and ffmpeg encodes mp3.
4. Song titles ("artist - title") come from the English localization (`onscreens.json`).
5. DJ lines: the subtitle files give each line's text and id, and the id is the suffix of the voice file name.
6. Menu sounds are cut out of `.opuspak` containers using the offsets in `sfx_container.opusinfo`.

Details with all the commands: [docs/PIPELINE.md](docs/PIPELINE.md) (in Russian).

### The live schedule

There is no server and no stream. Each station shuffles its songs with a fixed seed (the station id), and the position
in the loop comes from the current time. So every device plays the same song at the same moment, and when you come
back to a station, the broadcast has moved on without you.

### The player

`site/` is plain HTML, CSS and JavaScript with no build step and no dependencies.

- Two `<audio>` elements take turns, so the next song can start on the idle one and fade in (equal-power crossfade).
- Web Audio drives the spectrum analyser and the interface sounds. Without sound files it synthesizes the clicks.
- The layout is one fixed-size panel scaled to the screen, with separate arrangements for phone portrait and landscape.

## Project layout

```
build.py              one-command build from your game
site/                 the web app (no build step)
  index.html          main screen
  app.js              player: schedule, two decks + crossfade, DJ, scan, history, stats
  fx.js               interface sounds and spectrum analyser (Web Audio)
  stats.html          stats page
  sw.js, manifest…    PWA
  serve.py            local server with Range support
pipeline/             extraction scripts (Wwise banks, wem → mp3, DJ lines, menu sounds, logos)
  data/               small manifests (song list, loudness), no audio
demo/                 the demo: generate.py (synthesis, logos), assemble.py (demo site), assets/
deploy/               nginx + docker-compose for a home server
docs/PIPELINE.md      how the data is pulled from the game archives
```

## Hosting at home

The site is static. Any web server with Range support works. `deploy/` has an `nginx:alpine` container
with a memory limit and read-only files, plus an optional systemd timer that pulls code updates from git.
See [README.ru.md](README.ru.md#хостинг-дома) for the full setup.

**Do not put the built site on the open internet.** Put it behind a login, for example Cloudflare Tunnel with Cloudflare Access.

## Browser support

Current Chrome, Edge, Firefox and Safari. On phones it works as a PWA and keeps playing in the background with Media Session controls.
The service worker caches only the app shell; music is never cached.

## License

Code: [MIT](LICENSE). The license does not cover game material. Unofficial project, not affiliated with CD PROJEKT RED.
