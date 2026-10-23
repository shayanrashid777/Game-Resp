# Game-Resp

**A free, open-source Windows game library.** Keep Steam and non-Steam games together in one tidy desktop launcher.

> Early release / MVP: use the Issues tab to report bugs and request features. Steam detection relies on local Steam library manifests and does not require your Steam password or account credentials.

## Features

- Dark desktop UI with library overview counters.
- Choose and save a custom background color from the Background button.
- Automatic Steam update notifications: checks installed Steam manifest build IDs every five minutes and notifies when a known Steam game build changes. Non-Steam games are never checked. Windows toast notifications require the bundled `winotify` dependency; an in-app notice is used if toast notifications are unavailable.
- Scan local Steam library manifests and add discovered games.
- Add non-Steam games by selecting their `.exe`.
- Launch Steam games through their Steam App ID; launch non-Steam executables directly.
- Search by game name, executable path, or tags.
- Filter by Steam, non-Steam, favorites, or missing non-Steam executable.
- Favorites, tags, notes, rename, and executable path updates.
- Import/export the library as JSON for backup or migration.
- Local-first: library data is stored on your PC. No account, subscription, telemetry, or online service required.

## Requirements

- Windows 10 or Windows 11
- Python 3.10+ for running from source (Tkinter is included in standard Windows Python installers)

## Run from source

1. Install Python from [python.org](https://www.python.org/downloads/windows/). During setup, enable **Add Python to PATH**.
2. Download or clone this repository.
3. Open PowerShell in the project directory and run:

```powershell
python app.py
```

No third-party Python packages are required.

## Build a Windows executable

Install PyInstaller and run:

```powershell
python -m pip install pyinstaller
python -m PyInstaller --noconfirm --clean --windowed --name Game-Resp app.py
```

The executable will be at `dist\Game-Resp\Game-Resp.exe`. To make a single-file executable instead, add `--onefile` to the command (first launch may take longer).

## Steam scanning notes

Game-Resp looks for Steam installation folders and reads `steamapps\libraryfolders.vdf` and `appmanifest_*.acf` files. It does not modify Steam files. A game entry can be detected from its manifest even if its installation directory is missing; the status will reflect that. Steam game launching uses `steam://run/APPID`, which requires Steam to be installed.

## Where is my library saved?

`%APPDATA%\Game-Resp\library.json`

Use **Export library** before moving to another PC or trying an early build. Import merges games without overwriting matching IDs.

## Public release checklist

1. Create a **public** GitHub repository named `Game-Resp`.
2. Upload/commit the contents of this folder.
3. Open **Actions** and let the Windows build workflow complete.
4. Create a GitHub Release tagged `v0.1.0` (or publish a version after testing). Attach a packaged Windows build from the workflow artifacts, or build locally using the command above.
5. Add screenshots and tested Windows version to the release notes.

## Roadmap ideas

- Cover art and customizable grid/card view
- Playtime tracking and session history
- Controller-friendly navigation
- Optional metadata providers and manual cover art
- Steam Grid DB integration (requires user-supplied API key / terms review)
- Per-game launch arguments and working directory
- GOG, Epic, Xbox app and other launcher integrations

## Privacy and safety

Game-Resp launches executables only when you click Play. Review executable paths before launching games. The app does not download game files or bypass DRM. Steam support is a local library scanner/launcher, not a replacement for Steam.

## License

MIT — see [LICENSE](LICENSE).
