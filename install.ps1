# Radioport installer: sets up everything and builds the player from your copy of Cyberpunk 2077.
# Run it with Install.bat (double-click). Safe to run again: finished parts are skipped.
#
#   -Game <folder>   use this game folder instead of searching for it
#   -NoStart         do not start the player at the end
#   -NoShortcut      do not create the desktop shortcut
param([string]$Game, [switch]$NoStart, [switch]$NoShortcut)

$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'      # Invoke-WebRequest is many times faster without the progress bar
$Root = $PSScriptRoot
Set-Location $Root

function Say($text) { Write-Host "`n== $text" -ForegroundColor Cyan }
function Ok($text) { Write-Host "   $text" -ForegroundColor Green }
function Fail($text) { Write-Host "`n$text" -ForegroundColor Red; exit 1 }

function Refresh-Path {
    $env:Path = [Environment]::GetEnvironmentVariable('Path', 'Machine') + ';' + [Environment]::GetEnvironmentVariable('Path', 'User')
}

function Find-Python {
    foreach ($c in 'py', 'python') {
        $cmd = Get-Command $c -ErrorAction SilentlyContinue
        if (-not $cmd) { continue }
        # skip the Microsoft Store placeholder python.exe, it only opens the Store
        $v = & $cmd.Source -c "import sys; print(sys.version_info >= (3, 10))" 2>$null
        if ($v -eq 'True') { return $cmd.Source }
    }
    return $null
}

function Has-DotNet10 {
    if (-not (Get-Command dotnet -ErrorAction SilentlyContinue)) { return $false }
    return [bool]((& dotnet --list-runtimes 2>$null) -match '^Microsoft\.NETCore\.App 10\.')
}

function Is-GameFolder($p) {
    # [IO.Path]::Combine, not Join-Path: Join-Path throws when the drive does not exist (old Steam library on a removed disk)
    return $p -and (Test-Path -LiteralPath ([IO.Path]::Combine($p, 'archive\pc\content\audio_2_soundbanks.archive')))
}

function Find-Game {
    $found = New-Object System.Collections.Generic.List[string]
    # Steam: main folder from the registry, extra libraries from libraryfolders.vdf
    $steam = (Get-ItemProperty HKCU:\Software\Valve\Steam -Name SteamPath -ErrorAction SilentlyContinue).SteamPath
    if ($steam) {
        $libs = @($steam)
        $vdf = [IO.Path]::Combine($steam, 'steamapps\libraryfolders.vdf')
        if (Test-Path $vdf) {
            $libs += [regex]::Matches((Get-Content $vdf -Raw), '"path"\s+"([^"]+)"') | ForEach-Object { $_.Groups[1].Value -replace '\\\\', '\' }
        }
        $libs | ForEach-Object { $found.Add([IO.Path]::Combine($_, 'steamapps\common\Cyberpunk 2077')) }
    }
    # GOG Galaxy: the game id is 1423049311
    foreach ($k in 'HKLM:\SOFTWARE\WOW6432Node\GOG.com\Games\1423049311', 'HKLM:\SOFTWARE\GOG.com\Games\1423049311') {
        $p = (Get-ItemProperty $k -Name path -ErrorAction SilentlyContinue).path
        if ($p) { $found.Add($p) }
    }
    # Epic Games: one manifest file per installed game
    $epic = 'C:\ProgramData\Epic\EpicGamesLauncher\Data\Manifests'
    if (Test-Path $epic) {
        Get-ChildItem $epic -Filter *.item | ForEach-Object {
            try { $m = Get-Content $_.FullName -Raw | ConvertFrom-Json; if ($m.DisplayName -like 'Cyberpunk 2077*') { $found.Add($m.InstallLocation) } } catch {}
        }
    }
    foreach ($p in $found) { if (Is-GameFolder $p) { return $p } }

    # anything else: look two folders deep on every drive, e.g. D:\Games\Cyberpunk 2077
    Write-Host '   searching the drives...'
    foreach ($d in [IO.DriveInfo]::GetDrives() | Where-Object { $_.DriveType -eq 'Fixed' -and $_.IsReady }) {
        $level1 = Get-ChildItem $d.RootDirectory.FullName -Directory -ErrorAction SilentlyContinue
        foreach ($a in $level1) {
            if (Is-GameFolder $a.FullName) { return $a.FullName }
            foreach ($b in Get-ChildItem $a.FullName -Directory -ErrorAction SilentlyContinue) {
                if (Is-GameFolder $b.FullName) { return $b.FullName }
            }
        }
    }
    return $null
}

function Pick-Folder {
    Add-Type -AssemblyName System.Windows.Forms
    $dlg = New-Object System.Windows.Forms.FolderBrowserDialog
    $dlg.Description = 'Select the Cyberpunk 2077 game folder (the one that contains the "archive" folder)'
    $dlg.ShowNewFolderButton = $false
    if ($dlg.ShowDialog() -eq 'OK') { return $dlg.SelectedPath }
    return $null
}

function Get-Tool($name, $url, $exe) {
    $dir = Join-Path $Root "tools\$name"
    if (Get-ChildItem $dir -Recurse -Filter $exe -ErrorAction SilentlyContinue) { Ok "${name}: already here"; return }
    Write-Host "   downloading ${name}..."
    $zip = Join-Path $env:TEMP "radioport-$name.zip"
    Invoke-WebRequest $url -OutFile $zip -UseBasicParsing
    Expand-Archive $zip $dir -Force
    Remove-Item $zip
    Ok "${name}: done"
}

Write-Host 'RADIOPORT INSTALLER' -ForegroundColor Cyan
Write-Host 'Takes about 30 minutes, most of it automatic. You can leave it running.'

# 1. programs
Say 'Step 1 of 4: programs (Python, ffmpeg, .NET 10 Runtime)'
$need = @()
if (-not (Find-Python)) { $need += 'Python.Python.3.13' }
if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue) -or -not (Get-Command ffprobe -ErrorAction SilentlyContinue)) { $need += 'Gyan.FFmpeg' }
if (-not (Has-DotNet10)) { $need += 'Microsoft.DotNet.Runtime.10' }
if ($need) {
    if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
        Fail ("Missing: $($need -join ', '). Install 'App Installer' from the Microsoft Store (it adds winget) and run Install.bat again,`n" +
              "or install the programs by hand: see docs/SETUP.md, manual setup.")
    }
    foreach ($id in $need) {
        Write-Host "   installing $id (Windows may ask for permission)..."
        winget install -e --id $id --silent --accept-package-agreements --accept-source-agreements | Out-Host
    }
    Refresh-Path
}
$py = Find-Python
if (-not $py) { Fail 'Python is still not found. Close this window, open Install.bat again (a fresh window sees new programs).' }
if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) { Fail 'ffmpeg is still not found. Close this window and run Install.bat again.' }
if (-not (Has-DotNet10)) { Fail '.NET 10 Runtime is still not found. Close this window and run Install.bat again.' }
Ok 'all programs are ready'

# 2. extraction tools
Say 'Step 2 of 4: extraction tools (WolvenKit CLI, vgmstream)'
Get-Tool 'wolvenkit' 'https://github.com/WolvenKit/WolvenKit/releases/download/9.1.0/WolvenKit.Console-9.1.0.zip' 'WolvenKit.CLI.exe'
Get-Tool 'vgmstream' 'https://github.com/vgmstream/vgmstream/releases/latest/download/vgmstream-win64.zip' 'vgmstream-cli.exe'

# 3. game folder
Say 'Step 3 of 4: your Cyberpunk 2077 folder'
if (-not $Game -and (Test-Path config.json)) {
    try { $Game = (Get-Content config.json -Raw | ConvertFrom-Json).game } catch {}
}
if (-not (Is-GameFolder $Game)) { $Game = Find-Game }
while (-not (Is-GameFolder $Game)) {
    Write-Host '   Could not find the game by itself. Please choose its folder in the window that opens.' -ForegroundColor Yellow
    $Game = Pick-Folder
    if (-not $Game) { Fail 'No folder chosen. Run Install.bat again when you know where the game is.' }
    if (-not (Is-GameFolder $Game)) { Write-Host "   '$Game' is not the game folder: it must contain archive\pc\content." -ForegroundColor Yellow }
}
Ok "found: $Game"

$free = try { (Get-PSDrive (Split-Path $Root -Qualifier).TrimEnd(':')).Free } catch { $null }
if ($free -and $free -lt 3GB) { Write-Host ("   Warning: only {0:N1} GB free on this drive, the build needs about 3 GB." -f ($free / 1GB)) -ForegroundColor Yellow }

# 4. build
Say 'Step 4 of 4: building the player from the game files (20-25 minutes)'
& $py build.py --game $Game
if ($LASTEXITCODE) { Fail 'The build stopped with an error (see above). Fix it and run Install.bat again: finished steps are skipped. Help: docs/SETUP.md, Troubleshooting.' }

if (-not $NoShortcut) {
    $lnk = Join-Path ([Environment]::GetFolderPath('Desktop')) 'Radioport.lnk'
    $sh = (New-Object -ComObject WScript.Shell).CreateShortcut($lnk)
    $sh.TargetPath = Join-Path $Root 'site\start.bat'
    $sh.WorkingDirectory = Join-Path $Root 'site'
    $sh.Save()
    Ok 'desktop shortcut "Radioport" created'
}

Write-Host "`nDONE. Radioport is ready." -ForegroundColor Green
Write-Host 'Next time, start it with the "Radioport" shortcut on your desktop (or site\start.bat).'
if (-not $NoStart) {
    Write-Host 'Starting it now. Keep the new window open while you listen.'
    Start-Process (Join-Path $Root 'site\start.bat') -WorkingDirectory (Join-Path $Root 'site')
}
