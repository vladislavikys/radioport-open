# Setup guide

This guide builds the full Radioport player from your own copy of Cyberpunk 2077 and starts it on your computer.

**What you get:** 14 radio stations, 164 songs, 40 station jingles, DJ lines, the game's menu sounds, logos and fonts.

| | |
|---|---|
| System | Windows 10 or 11 (64-bit). Linux and macOS are not tested. |
| Game | Cyberpunk 2077 installed from any store (version 2.31 recommended, see [Tested with](#tested-with)) |
| Free disk space | about 3 GB (1.4 GB for the finished player, 1.5 GB of temporary files) |
| Time | a few minutes of your time, then 20–25 minutes of automatic build |

> Everything you build stays on your computer. Do not upload the built player to a public server:
> the music belongs to its artists and CD PROJEKT RED.

**There are two ways to set it up. Both give the same result.**

- **[Quick install](#quick-install):** double-click `Install.bat`. It runs the manual steps for you.
- **[Manual setup](#manual-setup):** you run every step yourself, with a check after each one.

`Install.bat` is only a convenience. You do not need it: the manual steps do exactly the same thing.

## Quick install

1. **Download** the code: [radioport-open-main.zip](https://github.com/vladislavikys/radioport-open/archive/refs/heads/main.zip).
   Right-click the file → **Extract All** → **Extract**.
2. **Double-click `Install.bat`** in the extracted folder.
   Windows may show "Windows protected your PC": it shows this for every script downloaded from the internet
   that is not signed by a company. Click **More info → Run anyway**, or use the [manual setup](#manual-setup) instead.

A black window shows each step as it runs. If programs are missing, it lists them and asks before installing anything.
At the end, the player opens in your browser, and a **Radioport** shortcut is on your desktop for next time.
Keep the shortcut's black window open while you listen.

If something goes wrong, the window says what to do. After fixing it, run `Install.bat` again: finished parts are skipped.

### What Install.bat does, exactly

`Install.bat` only starts `install.ps1`, a plain PowerShell script of about 170 lines. You can open both in Notepad
and read them before running. The script does the four steps of the manual setup, in the same order:

| Step | What the script does | Same as manual step |
|---|---|---|
| 1. Programs | Checks for Python, ffmpeg and the .NET 10 Runtime. If any are missing, it lists them, **asks you**, and installs them with `winget`, the package manager built into Windows. | [1](#1-install-the-prerequisites) |
| 2. Tools | Downloads WolvenKit CLI 9.1.0 and vgmstream from their official GitHub release pages into the `tools` folder. | [3](#3-get-wolvenkit-cli-and-vgmstream) |
| 3. Game folder | Looks for the game where the launchers record it: Steam (registry and library list), GOG Galaxy (registry), Epic Games (its install list). Then it checks folder names two levels deep on your drives. If it finds nothing, it asks you to choose the folder. | [4](#4-find-your-game-folder) |
| 4. Build | Runs `py build.py --game "<your game folder>"`, the same command as in the manual setup. | [5](#5-build) |
| End | Creates the **Radioport** desktop shortcut to `site\start.bat` and starts it. | [6](#6-start-the-player) |

**What changes on your PC:**

- the programs from step 1, only if they were missing and you agreed;
- inside the Radioport folder: `tools\`, `work\`, the built player in `site\`, and `config.json` with your game path;
- one shortcut on the desktop.

**What it never does:**

- it does not change, move or delete game files: it only reads them;
- it does not change Windows settings or write to the registry (it only reads where the launchers installed the game);
- it does not send anything anywhere: the only downloads are `winget` packages and the two tools from GitHub;
- it does not need administrator rights. Windows may ask for permission only when `winget` installs a program.

**To remove everything:** delete the Radioport folder and the desktop shortcut.
The programs from step 1 can be removed in **Settings → Apps** if you do not need them.

To reach the player from your phone or from outside your home: [HOSTING.md](HOSTING.md).

## Manual setup

Use this if you prefer to do every step yourself or if `Install.bat` does not work on your system.
Follow the steps in order. Each step ends with a check, so you know it worked before you go on.

### Tested with

This setup was built from scratch on 2026-10-29, both by following these steps and with `Install.bat`.
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
The build reads only the base game archives (`archive\pc\content`), so Phantom Liberty should not be needed,
but a copy without it was not tested.

## 1. Install the prerequisites

You need Python 3, ffmpeg and the .NET 10 Runtime (WolvenKit needs it). Git is optional: it is only for `git clone` in step 2.
Open **PowerShell** and run:

```powershell
winget install -e --id Python.Python.3.13
winget install -e --id Gyan.FFmpeg
winget install -e --id Microsoft.DotNet.Runtime.10
winget install -e --id Git.Git        # optional
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

Without Git: download [radioport-open-main.zip](https://github.com/vladislavikys/radioport-open/archive/refs/heads/main.zip) and unpack it. Open the unpacked folder
(`radioport-open-main`) in File Explorer, click the address bar, type `powershell` and press Enter:
PowerShell opens in that folder. Without Git, updating later means downloading the ZIP again.

**Check:** `dir` shows `build.py`, `site` and `pipeline`.

## 3. Get WolvenKit CLI and vgmstream

These two tools read the game's archives and decode its audio. Run this in the `radioport` folder:

```powershell
$ProgressPreference = 'SilentlyContinue'   # makes downloads much faster in Windows PowerShell
Invoke-WebRequest https://github.com/WolvenKit/WolvenKit/releases/download/9.1.0/WolvenKit.Console-9.1.0.zip -OutFile wolvenkit.zip
Expand-Archive wolvenkit.zip tools\wolvenkit -Force
Invoke-WebRequest https://github.com/vgmstream/vgmstream/releases/latest/download/vgmstream-win64.zip -OutFile vgmstream.zip
Expand-Archive vgmstream.zip tools\vgmstream -Force
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

The launcher can open the folder for you:

- **Steam:** right-click the game → **Manage → Browse local files**.
- **GOG Galaxy:** open the game → **⚙ (settings) → Manage installation → Show folder**.
- **Epic Games:** Library → **⋯** on the game → **Manage** → folder icon next to the install path.

Then click the address bar in File Explorer and copy the path.

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
2. Find the computer's address: run `ipconfig` and look for **IPv4 Address** (on a Russian Windows: **IPv4-адрес**),
   for example `192.168.1.20`.
3. On the phone, open `http://192.168.1.20:8077`.

On the phone you can add the page to the home screen; it then opens like an app.

## Free up space

After the build you can delete the `work` folder (about 1.5 GB of temporary files). The player only needs `site\`.

## Updating

- **New code:** download the ZIP again and extract it over the old folder (your built music stays, it is not in the ZIP),
  or run `git pull` if you used Git. Then refresh the page in the browser.
- **After a game patch:** run `py build.py` again. It adds whatever is missing.
  To rebuild everything from scratch, delete `site\audio`, `site\dj` and the `work` folder first.

## Troubleshooting

| Message or symptom | Cause and fix |
|---|---|
| "Windows protected your PC" when starting `Install.bat` | Normal for unsigned scripts from the internet. Click **More info → Run anyway**, or follow the [manual setup](#manual-setup). |
| The installer cannot find the game and opens a folder window | Choose the folder that contains `archive` (see [step 4](#4-find-your-game-folder) for where launchers put it). |
| The installer says a program is "still not found" | Windows needs a fresh window to see new programs. Close the window and double-click `Install.bat` again. |
| `py` or `ffmpeg` is not recognized | The program is not on `PATH`. Open a new PowerShell window after installing. If that does not help, reinstall Python with "Add python.exe to PATH" ticked. |
| `WolvenKit.CLI.exe does not start` | The .NET 10 Runtime is missing: `winget install -e --id Microsoft.DotNet.Runtime.10`. |
| `game folder: set "game" in config.json` | The path is wrong. It must be the folder that contains `archive\pc\content` (step 4). Use quotes around a path with spaces. |
| `WolvenKit failed on ... .archive` | The game files are incomplete or the game is updating. Verify the files (Steam: **Properties → Installed Files → Verify integrity of game files**; GOG Galaxy: **Manage installation → Verify / Repair**), then run the build again. |
| `winget` is not recognized | Install **App Installer** from the Microsoft Store, or install the programs by hand (links in step 1). |
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
- **Listen away from home** (Tailscale, home server, your own domain with Cloudflare): see [HOSTING.md](HOSTING.md).
- **How the extraction works:** [PIPELINE.md](PIPELINE.md).
