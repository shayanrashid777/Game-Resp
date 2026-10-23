# Game-Resp

**A free, open-source Windows game library.** Keep Steam and non-Steam games together in one tidy desktop launcher.

> Early release / MVP: use the Issues tab to report bugs and request features. Steam detection relies on local Steam library manifests and does not require your Steam password or account credentials.

## Features

- Dark desktop UI with library overview counters.
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

## Steam scanning notes

Game-Resp looks for Steam installation folders and reads `steamapps\libraryfolders.vdf` and `appmanifest_*.acf` files. It does not modify Steam files. A game entry can be detected from its manifest even if its installation directory is missing; the status will reflect that. Steam game launching uses `steam://run/APPID`, which requires Steam to be installed.

## Where is my library saved?

`%APPDATA%\Game-Resp\library.json`

Use **Export library** before moving to another PC or trying an early build. Import merges games without overwriting matching IDs.

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
