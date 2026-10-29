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
> **your own copy** of the game with a one-click installer (see [Build from your game](#build-from-your-game)).
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

You need Windows 10/11, Cyberpunk 2077 installed (tested with game version 2.31) and about 3 GB of free space.

1. **Download** [radioport-open-main.zip](https://github.com/vladislavikys/radioport-open/archive/refs/heads/main.zip) and extract it (right-click → **Extract All**).
2. **Double-click `Install.bat`.**

The installer asks before installing missing programs (Python, ffmpeg, .NET 10 Runtime), downloads WolvenKit CLI
and vgmstream, **finds your game** in Steam, GOG Galaxy, Epic Games or on any drive, builds the player
(20–25 minutes), puts a **Radioport** shortcut on your desktop and opens the player.
If it cannot find the game, it asks you to choose the folder.

**`Install.bat` is optional.** It is a plain script that runs the manual steps for you: it only reads the game files,
changes nothing in Windows settings and sends nothing anywhere.
[What it does, exactly](docs/SETUP.md#what-installbat-does-exactly) ·
[do it by hand instead](docs/SETUP.md#manual-setup) · [tested versions and troubleshooting](docs/SETUP.md).

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
Install.bat           one-click installer (runs install.ps1)
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
docs/SETUP.md         step-by-step setup guide
docs/HOSTING.md       phone, Tailscale, home server, own domain with Cloudflare
docs/PIPELINE.md      how the data is pulled from the game archives
```

## Listening on your phone and away from home

**📖 [docs/HOSTING.md](docs/HOSTING.md)** compares four options and walks through each:

| Option | Works where | Cost |
|---|---|---|
| Phone on the same Wi-Fi | at home | free |
| **Tailscale** (recommended) | anywhere, on your own devices, with HTTPS | free |
| Always-on home server (`deploy/`: nginx in Docker) | 24/7 without your PC | spare hardware |
| Your own domain with Cloudflare Tunnel + Access | anywhere, in any browser, behind a login | domain, about $10–12 a year |

**Do not put the built site on the open internet.** Keep it on your own devices or behind a login.

## Browser support

Current Chrome, Edge, Firefox and Safari. On phones it works as a PWA and keeps playing in the background with Media Session controls.
The service worker caches only the app shell; music is never cached.

## License

Code: [MIT](LICENSE). The license does not cover game material. Unofficial project, not affiliated with CD PROJEKT RED.
