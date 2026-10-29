# Setup guide

This guide builds the full Radioport player from your own copy of Cyberpunk 2077 and starts it on your computer.
Follow the steps in order. Each step ends with a check, so you know it worked before you go on.

**What you get:** 14 radio stations, 164 songs, 40 station jingles, DJ lines, the game's menu sounds, logos and fonts.

| | |
|---|---|
| System | Windows 10 or 11 (64-bit). Linux and macOS are not tested. |
| Game | Cyberpunk 2077 installed from any store (version 2.31 recommended, see below) |
| Free disk space | about 3 GB (1.4 GB for the finished site, 1.5 GB of temporary files) |
| Time | about 10 minutes of setup, then 20–25 minutes of automatic build |

### Tested with

This exact setup was built from scratch on 2026-10-29, following this guide step by step.
The result matched the reference build file for file.

| Component | Version |
|---|---|
| Cyberpunk 2077 | **2.31** (GOG), with Phantom Liberty installed |
| Windows | 10 Pro 22H2, 64-bit |
| Python | 3.15 (any Python 3.10 or newer should work) |
| WolvenKit CLI | 9.1.0 (`WolvenKit.Console-9.1.0.zip`) |
| .NET Runtime | 10.0 |
| vgmstream | r2117 and r2168 |
| ffmpeg | 8.1 |

The song list in this repository (`pipeline/data/tracks_manifest.json`) was made from game version 2.31.
Other versions should work as well: songs that your version does not have are skipped with a warning.
Phantom Liberty is not required: the radio songs are in the base game archives.

> Everything you build stays on your computer. Do not upload the built site to a public server:
> the music belongs to its artists and CD PROJEKT RED.

## 1. Install the prerequisites

You need Python 3, ffmpeg, the .NET 10 Runtime (WolvenKit needs it) and Git.
Open **PowerShell** and run:

```powershell
winget install -e --id Python.Python.3.13
winget install -e --id Gyan.FFmpeg
winget install -e --id Microsoft.DotNet.Runtime.10
winget install -e --id Git.Git
```

Then **close PowerShell and open a new window**, so it picks up the new programs.

If you do not have `winget`, install them by hand:
[Python](https://www.python.org/downloads/) (tick "Add python.exe to PATH"),
[ffmpeg](https://www.gyan.dev/ffmpeg/builds/) (add its `bin` folder to `PATH`),
[.NET 10 Runtime](https://dotnet.microsoft.com/download/dotnet/10.0),
[Git](https://git-scm.com/download/win).

**Check:** each command prints a version number.

```powershell
py --version
ffmpeg -version
dotnet --list-runtimes
```

`dotnet --list-runtimes` must show a line that starts with `Microsoft.NETCore.App 10.`.

## 2. Get the code

```powershell
cd $HOME
git clone https://github.com/vladislavikys/radioport-open.git radioport
cd radioport
```

Without Git: on the repository page, click **Code → Download ZIP**, unpack it and open PowerShell in that folder.

**Check:** `dir` shows `build.py`, `site` and `pipeline`.

## 3. Get WolvenKit CLI and vgmstream

These two tools read the game's archives and decode its audio. Run this in the `radioport` folder:

```powershell
$ProgressPreference = 'SilentlyContinue'   # makes downloads much faster in Windows PowerShell
Invoke-WebRequest https://github.com/WolvenKit/WolvenKit/releases/download/9.1.0/WolvenKit.Console-9.1.0.zip -OutFile wolvenkit.zip
Expand-Archive wolvenkit.zip tools\wolvenkit
Invoke-WebRequest https://github.com/vgmstream/vgmstream/releases/latest/download/vgmstream-win64.zip -OutFile vgmstream.zip
Expand-Archive vgmstream.zip tools\vgmstream
Remove-Item wolvenkit.zip, vgmstream.zip
```

The build finds both tools in `tools\` by itself. It is tested with WolvenKit 9.1.0 and vgmstream r2117 and r2168.

**Check:**

```powershell
Get-ChildItem tools -Recurse -Include WolvenKit.CLI.exe, vgmstream-cli.exe | Select-Object FullName
```

It must list two files.

## 4. Find your game folder

You need the folder that contains `archive\pc\content`. Typical places:

| Store | Folder |
|---|---|
| Steam | `C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077` |
| GOG Galaxy | `C:\Program Files (x86)\GOG Galaxy\Games\Cyberpunk 2077` |
| Epic Games | `C:\Program Files\Epic Games\Cyberpunk2077` |

In Steam you can also right-click the game → **Manage → Browse local files**.

**Check** (put your own path in the quotes):

```powershell
Test-Path "C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\archive\pc\content"
```

It must print `True`.

## 5. Build

```powershell
py build.py --game "C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077"
```

Put your own game path in the quotes. The path is saved to `config.json`, so later runs only need `py build.py`.

The script first checks the setup. If something is missing, it prints what and how to fix it, and stops.
Then it runs seven steps and prints each one with its time:

| Step | What it does |
|---|---|
| `wem` | extracts the songs from the game archives |
| `audio` | converts the songs to mp3: the longest step, most of the 20 minutes |
| `loudness` | measures the loudness of each song |
| `data` | writes the station list |
| `dj` | extracts and converts the DJ lines |
| `sfx` | extracts the menu sounds |
| `assets` | extracts the logos, fonts and icons |

If the build stops with an error, fix the cause and run the same command again: finished steps are skipped.
To redo one step, add `--force <step>`, for example `py build.py --force dj`.

**Check:** the last line says `Ready.`

## 6. Start the player

```powershell
py site\serve.py 8077
```

Open http://localhost:8077 in your browser and press any key. Keep the PowerShell window open while you listen;
press `Ctrl+C` in it to stop the player. Next time, double-click `site\start.bat`: it starts the server and opens the browser.

**Check:** you see 14 stations with names like *89.7 GROWL FM*, and music starts after you choose one.

### Listen on your phone

Your phone must be on the same Wi-Fi network as the computer.

1. Start the server for the local network:
   ```powershell
   py site\serve.py 8077 0.0.0.0
   ```
   If Windows asks whether to allow Python on networks, allow **Private networks** only.
2. Find the computer's address: run `ipconfig` and look for **IPv4 Address**, for example `192.168.1.20`.
3. On the phone, open `http://192.168.1.20:8077`.

On the phone you can add the page to the home screen; it then opens like an app.

## Free up space

After the build you can delete the `work` folder (about 1.5 GB of temporary files). The player only needs `site\`.

## Updating

- **New code:** run `git pull`, then refresh the page in the browser.
- **After a game patch:** run `py build.py` again. It adds whatever is missing.
  To rebuild everything from scratch, delete `site\audio`, `site\dj` and the `work` folder first.

## Troubleshooting

| Message or symptom | Cause and fix |
|---|---|
| `py` or `ffmpeg` is not recognized | The program is not on `PATH`. Open a new PowerShell window after installing. If that does not help, reinstall Python with "Add python.exe to PATH" ticked. |
| `WolvenKit.CLI.exe does not start` | The .NET 10 Runtime is missing: `winget install Microsoft.DotNet.Runtime.10`. |
| `game folder: set "game" in config.json` | The path is wrong. It must be the folder that contains `archive\pc\content` (step 4). Use quotes around a path with spaces. |
| `WolvenKit failed on ... .archive` | The game files are incomplete or the game is updating. In Steam use **Properties → Installed Files → Verify integrity**, then run the build again. |
| `warning: N songs are not in your game files` | Your game version has fewer songs than the list in this repository. The build skips them; the stations play everything else. |
| The page opens but there is no sound | Press a key or click the page first: browsers only start audio after you interact with the page. Check the volume (`A`/`D`). |
| No spectrum, music does not start in the middle of a song | The page was opened as a file. Open it through `serve.py` at `http://localhost:8077`, not by double-clicking `index.html`. |
| Old design after an update | Press `Ctrl+F5` to reload the page without the cache. |
| The phone cannot open the page | Start the server with `0.0.0.0` (see above), check that both devices use the same Wi-Fi, and allow Python in Windows Firewall for private networks. |

Still stuck? [Open an issue](https://github.com/vladislavikys/radioport-open/issues) with the full text that `py build.py` printed.

## Advanced

- **Paths without arguments:** copy `config.example.json` to `config.json` and edit it. Keys: `game`, `wolvenkit`, `vgmstream`, `work`, `site`.
  Environment variables `CP2077_GAME`, `WOLVENKIT`, `VGMSTREAM`, `CP2077_WORK` and `CP2077_SITE` work too.
- **One step only:** `py build.py --only sfx`.
- **Host it on a home server:** see [Hosting at home](../README.md#hosting-at-home). Keep it behind a login.
- **How the extraction works:** [PIPELINE.md](PIPELINE.md).
