from __future__ import annotations
import json, os, re, subprocess, sys, threading, time
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog

APP_NAME = "Game-Resp"
APP_DIR = Path(os.getenv("APPDATA", str(Path.home()))) / APP_NAME
DATA_FILE = APP_DIR / "library.json"

BG = "#10131a"
PANEL = "#191e29"
PANEL2 = "#202737"
TEXT = "#eef2ff"
MUTED = "#9ba7bd"
ACCENT = "#7c5cff"
GREEN = "#43d9a3"
RED = "#ff6b7a"

def load_data():
    APP_DIR.mkdir(parents=True, exist_ok=True)
    try:
        data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {"games": []}
    except (OSError, json.JSONDecodeError):
        return {"games": []}

def save_data(data):
    APP_DIR.mkdir(parents=True, exist_ok=True)
    temp = DATA_FILE.with_suffix(".tmp")
    temp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    temp.replace(DATA_FILE)

def steam_roots():
    roots = []
    candidates = [
        Path(os.getenv("PROGRAMFILES(X86)", r"C:\Program Files (x86)")) / "Steam",
        Path(os.getenv("PROGRAMFILES", r"C:\Program Files")) / "Steam",
        Path.home() / "scoop" / "apps" / "steam" / "current",
    ]
    try:
        import winreg
        for hive in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
            for keyname in (r"Software\Valve\Steam", r"Software\WOW6432Node\Valve\Steam"):
                try:
                    with winreg.OpenKey(hive, keyname) as key:
                        value, _ = winreg.QueryValueEx(key, "SteamPath")
                        candidates.append(Path(value))
                except OSError:
                    pass
    except ImportError:
        pass
    for path in candidates:
        if path.exists() and path not in roots:
            roots.append(path)
    return roots

def parse_vdf_string(text, key):
    match = re.search(r'"' + re.escape(key) + r'"\s*"([^"]+)"', text, re.I)
    return match.group(1) if match else None

def steam_library_paths():
    paths = []
    for root in steam_roots():
        paths.append(root)
        vdf = root / "steamapps" / "libraryfolders.vdf"
        if vdf.exists():
            try:
                content = vdf.read_text(encoding="utf-8", errors="ignore")
                # Current Steam format stores paths on lines like "path" "D:\\SteamLibrary".
                for raw in re.findall(r'"path"\s*"([^"]+)"', content, re.I):
                    p = Path(raw.replace("\\\\", "\\"))
                    if p.exists() and p not in paths:
                        paths.append(p)
                # Older format uses numbered keys containing escaped paths.
                for raw in re.findall(r'"\d+"\s*"([^"]+)"', content):
                    if ":" in raw or raw.startswith("\\\\"):
                        p = Path(raw.replace("\\\\", "\\"))
                        if p.exists() and p not in paths:
                            paths.append(p)
            except OSError:
                pass
    return paths

def scan_steam_games():
    found = []
    seen = set()
    for library in steam_library_paths():
        steamapps = library / "steamapps"
        if not steamapps.exists():
            continue
        for manifest in steamapps.glob("appmanifest_*.acf"):
            try:
                raw = manifest.read_text(encoding="utf-8", errors="ignore")
                appid = parse_vdf_string(raw, "appid")
                name = parse_vdf_string(raw, "name")
                installdir = parse_vdf_string(raw, "installdir")
                if not name or not installdir:
                    continue
                install = steamapps / "common" / installdir
                key = "steam:" + (appid or name.lower())
                if key in seen:
                    continue
                seen.add(key)
                found.append({
                    "id": key, "name": name, "path": str(install),
                    "source": "Steam", "appid": appid or "", "favorite": False,
                    "status": "Installed" if install.exists() else "Missing",
                    "tags": [], "notes": "", "added": int(time.time())
                })
            except OSError:
                continue
    return found

class GameResp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Game-Resp | Your game universe")
        self.geometry("1180x760")
        self.minsize(900, 600)
        self.configure(bg=BG)
        self.data = load_data()
        self.games = self.data.setdefault("games", [])
        self.filter_var = tk.StringVar()
        self.source_var = tk.StringVar(value="All games")
        self.sort_var = tk.StringVar(value="Recently added")
        self.status_var = tk.StringVar(value="Ready")
        self._setup_style()
        self._build_ui()
        self.render_games()

    def _setup_style(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Treeview", background=PANEL, fieldbackground=PANEL, foreground=TEXT,
                        rowheight=34, borderwidth=0, font=("Segoe UI", 10))
        style.configure("Treeview.Heading", background=PANEL2, foreground=MUTED,
                        relief="flat", font=("Segoe UI", 9, "bold"))
        style.map("Treeview", background=[("selected", ACCENT)], foreground=[("selected", "white")])
        style.configure("TCombobox", fieldbackground=PANEL2, background=PANEL2, foreground=TEXT)
        style.configure("Horizontal.TProgressbar", troughcolor=PANEL2, background=ACCENT)

    def _label(self, parent, text, size=10, color=TEXT, bold=False):
        return tk.Label(parent, text=text, bg=parent.cget("bg"), fg=color,
                        font=("Segoe UI", size, "bold" if bold else "normal"))

    def _button(self, parent, text, command, primary=False):
        return tk.Button(parent, text=text, command=command, cursor="hand2",
                         bg=ACCENT if primary else PANEL2, fg="white" if primary else TEXT,
                         activebackground="#6547dc" if primary else "#30394c",
                         activeforeground="white", relief="flat", bd=0,
                         padx=13, pady=9, font=("Segoe UI", 9, "bold"))

    def _build_ui(self):
        header = tk.Frame(self, bg=BG, padx=22, pady=18)
        header.pack(fill="x")
        brand = tk.Frame(header, bg=BG)
        brand.pack(side="left")
        self._label(brand, "GAME-RESP", 22, TEXT, True).pack(anchor="w")
        self._label(brand, "YOUR LIBRARY. YOUR RULES.", 8, MUTED, True).pack(anchor="w", pady=(2,0))
        actions = tk.Frame(header, bg=BG)
        actions.pack(side="right")
        self._button(actions, "↻ Scan Steam", self.scan_steam).pack(side="left", padx=4)
        self._button(actions, "+ Add game", self.add_game, True).pack(side="left", padx=4)
        self._button(actions, "Import", self.import_library).pack(side="left", padx=4)

        stats = tk.Frame(self, bg=BG, padx=22)
        stats.pack(fill="x", pady=(0, 14))
        self.stat_total = self._stat_card(stats, "GAMES IN LIBRARY", "0")
        self.stat_steam = self._stat_card(stats, "STEAM TITLES", "0")
        self.stat_custom = self._stat_card(stats, "NON-STEAM GAMES", "0")
        self.stat_fav = self._stat_card(stats, "FAVORITES", "0")

        toolbar = tk.Frame(self, bg=BG, padx=22, pady=6)
        toolbar.pack(fill="x")
        search = tk.Entry(toolbar, textvariable=self.filter_var, bg=PANEL, fg=TEXT, insertbackground=TEXT,
                          relief="flat", font=("Segoe UI", 11), width=34)
        search.pack(side="left", ipady=10, padx=(0,10))
        search.insert(0, "")
        self.filter_var.trace_add("write", lambda *_: self.render_games())
        source = ttk.Combobox(toolbar, textvariable=self.source_var, values=["All games", "Steam", "Non-Steam", "Favorites", "Missing"], state="readonly", width=14)
        source.pack(side="left", ipady=5, padx=4)
        source.bind("<<ComboboxSelected>>", lambda _: self.render_games())
        sort = ttk.Combobox(toolbar, textvariable=self.sort_var, values=["Recently added", "Name A–Z", "Name Z–A"], state="readonly", width=17)
        sort.pack(side="left", ipady=5, padx=4)
        sort.bind("<<ComboboxSelected>>", lambda _: self.render_games())
        self._button(toolbar, "Export library", self.export_library).pack(side="right")

        body = tk.Frame(self, bg=BG, padx=22, pady=10)
        body.pack(fill="both", expand=True)
        self.tree = ttk.Treeview(body, columns=("name", "source", "status", "path"), show="headings", selectmode="browse")
        self.tree.heading("source", text="PLATFORM")
        self.tree.heading("name", text="GAME")
        self.tree.heading("status", text="STATUS")
        self.tree.heading("path", text="LOCATION")
        self.tree["columns"] = ("name", "source", "status", "path")
        self.tree.column("name", width=250, minwidth=180)
        self.tree.column("source", width=110, minwidth=90)
        self.tree.column("status", width=100, minwidth=80)
        self.tree.column("path", width=500, minwidth=200)
        scroll = ttk.Scrollbar(body, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self.tree.bind("<Double-1>", lambda _: self.launch_selected())
        self.tree.bind("<<TreeviewSelect>>", lambda _: self.update_details())

        lower = tk.Frame(self, bg=PANEL, padx=22, pady=13)
        lower.pack(fill="x", side="bottom")
        self.details = tk.Label(lower, text="Select a game to view details.", bg=PANEL, fg=MUTED, anchor="w", font=("Segoe UI", 9))
        self.details.pack(side="left", fill="x", expand=True)
        buttons = tk.Frame(lower, bg=PANEL)
        buttons.pack(side="right")
        self._button(buttons, "▶ Play", self.launch_selected, True).pack(side="left", padx=3)
        self._button(buttons, "★ Favorite", self.toggle_favorite).pack(side="left", padx=3)
        self._button(buttons, "Edit", self.edit_selected).pack(side="left", padx=3)
        self._button(buttons, "Remove", self.remove_selected).pack(side="left", padx=3)
        footer = tk.Frame(self, bg=BG, padx=22, pady=6)
        footer.pack(fill="x")
        self._label(footer, "FREE FOREVER  •  LOCAL-FIRST  •  OPEN SOURCE", 8, MUTED, True).pack(side="left")
        tk.Label(footer, textvariable=self.status_var, bg=BG, fg=GREEN, font=("Segoe UI", 8)).pack(side="right")

    def _stat_card(self, parent, title, value):
        card = tk.Frame(parent, bg=PANEL, padx=16, pady=12)
        card.pack(side="left", fill="x", expand=True, padx=(0,9))
        self._label(card, title, 8, MUTED, True).pack(anchor="w")
        val = self._label(card, value, 20, TEXT, True)
        val.pack(anchor="w", pady=(4,0))
        return val

    def selected_game(self):
        selected = self.tree.selection()
        if not selected:
            return None
        gid = selected[0]
        return next((g for g in self.games if g.get("id") == gid), None)

    def render_games(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        query = self.filter_var.get().strip().lower()
        mode = self.source_var.get()
        games = list(self.games)
        if query:
            games = [g for g in games if query in g.get("name","").lower() or query in g.get("path","").lower() or query in " ".join(g.get("tags",[])).lower()]
        if mode == "Steam": games = [g for g in games if g.get("source") == "Steam"]
        elif mode == "Non-Steam": games = [g for g in games if g.get("source") != "Steam"]
        elif mode == "Favorites": games = [g for g in games if g.get("favorite")]
        elif mode == "Missing": games = [g for g in games if g.get("source") != "Steam" and not Path(g.get("path","")).exists()]
        if self.sort_var.get() == "Name A–Z": games.sort(key=lambda g:g.get("name","").lower())
        elif self.sort_var.get() == "Name Z–A": games.sort(key=lambda g:g.get("name","").lower(), reverse=True)
        else: games.sort(key=lambda g:g.get("added",0), reverse=True)
        for g in games:
            status = g.get("status","Installed")
            if g.get("source") != "Steam":
                status = "Ready" if Path(g.get("path","")).exists() else "Missing"
            name = ("★ " if g.get("favorite") else "") + g.get("name","Untitled")
            self.tree.insert("", "end", iid=g.get("id"), values=(name, g.get("source","Non-Steam"), status, g.get("path","")))
        self.stat_total.config(text=str(len(self.games)))
        self.stat_steam.config(text=str(sum(g.get("source")=="Steam" for g in self.games)))
        self.stat_custom.config(text=str(sum(g.get("source")!="Steam" for g in self.games)))
        self.stat_fav.config(text=str(sum(bool(g.get("favorite")) for g in self.games)))

    def persist(self):
        self.data["games"] = self.games
        save_data(self.data)
        self.render_games()

    def scan_steam(self):
        self.status_var.set("Scanning Steam libraries…")
        self.update_idletasks()
        try:
            found = scan_steam_games()
            existing = {g.get("id") for g in self.games}
            added = 0
            for game in found:
                if game["id"] not in existing:
                    self.games.append(game); added += 1
            self.persist()
            self.status_var.set(f"Steam scan complete — {added} new game(s)")
            messagebox.showinfo("Steam scan complete", f"Found {len(found)} installed Steam manifest(s).\nAdded {added} new entr{'y' if added == 1 else 'ies'} to Game-Resp.")
        except Exception as exc:
            self.status_var.set("Steam scan failed")
            messagebox.showerror("Steam scan", str(exc))

    def add_game(self):
        path = filedialog.askopenfilename(title="Select game executable", filetypes=[("Windows executables", "*.exe"), ("All files", "*.*")])
        if not path: return
        p = Path(path)
        if any(Path(g.get("path","")).resolve() == p.resolve() for g in self.games if g.get("path")):
            messagebox.showinfo("Already added", "This executable is already in your library."); return
        name = simpledialog.askstring("Add game", "Game name:", initialvalue=p.stem, parent=self)
        if not name: return
        game = {"id":"custom:"+str(time.time_ns()), "name":name.strip(), "path":str(p),
                "source":"Non-Steam", "favorite":False, "status":"Installed", "tags":[], "notes":"", "added":int(time.time())}
        self.games.append(game); self.persist()
        self.status_var.set(f"Added {name.strip()}")

    def launch_selected(self):
        game = self.selected_game()
        if not game:
            messagebox.showinfo("Select a game", "Choose a game from your library first."); return
        try:
            if game.get("source") == "Steam" and game.get("appid"):
                subprocess.Popen(["cmd", "/c", "start", "", f"steam://run/{game['appid']}"], shell=False)
            else:
                path = Path(game.get("path",""))
                if not path.exists():
                    messagebox.showerror("Executable not found", f"Can't find:\n{path}\n\nEdit this game to update its executable path."); return
                os.startfile(str(path))
            self.status_var.set(f"Launching {game.get('name','game')}…")
        except Exception as exc:
            messagebox.showerror("Couldn't launch game", str(exc))

    def toggle_favorite(self):
        game = self.selected_game()
        if not game: return
        game["favorite"] = not bool(game.get("favorite"))
        self.persist()
        self.status_var.set(("Added to" if game["favorite"] else "Removed from") + " favorites")

    def edit_selected(self):
        game = self.selected_game()
        if not game: return
        name = simpledialog.askstring("Edit game", "Game name:", initialvalue=game.get("name",""), parent=self)
        if name is None: return
        if name.strip(): game["name"] = name.strip()
        notes = simpledialog.askstring("Game notes", "Notes (optional):", initialvalue=game.get("notes",""), parent=self)
        if notes is not None: game["notes"] = notes
        if game.get("source") != "Steam":
            if messagebox.askyesno("Executable path", "Would you like to choose a new executable?"):
                path = filedialog.askopenfilename(title="Select game executable", filetypes=[("Windows executables","*.exe"),("All files","*.*")])
                if path: game["path"] = path
        tags = simpledialog.askstring("Game tags", "Comma-separated tags:", initialvalue=", ".join(game.get("tags",[])), parent=self)
        if tags is not None: game["tags"] = [x.strip() for x in tags.split(",") if x.strip()]
        self.persist()

    def remove_selected(self):
        game = self.selected_game()
        if not game: return
        if messagebox.askyesno("Remove game", f"Remove {game.get('name')} from your Game-Resp library?\nThe game files will not be deleted."):
            self.games.remove(game); self.persist(); self.details.config(text="Select a game to view details.")

    def update_details(self):
        game = self.selected_game()
        if not game:
            self.details.config(text="Select a game to view details."); return
        tags = ", ".join(game.get("tags",[])) or "No tags"
        notes = game.get("notes","") or "No notes"
        self.details.config(text=f"{game.get('name')}  •  {game.get('source')}  •  Tags: {tags}  •  Notes: {notes[:100]}")

    def import_library(self):
        path = filedialog.askopenfilename(title="Import Game-Resp library", filetypes=[("JSON library","*.json")])
        if not path: return
        try:
            imported = json.loads(Path(path).read_text(encoding="utf-8"))
            games = imported.get("games", [])
            if not isinstance(games, list): raise ValueError("The JSON file doesn't contain a games list.")
            existing = {g.get("id") for g in self.games}
            added = 0
            for g in games:
                if isinstance(g, dict) and g.get("name") and g.get("path") and g.get("id") not in existing:
                    self.games.append(g); existing.add(g.get("id")); added += 1
            self.persist()
            messagebox.showinfo("Import complete", f"Imported {added} game(s).")
        except Exception as exc:
            messagebox.showerror("Import failed", str(exc))

    def export_library(self):
        path = filedialog.asksaveasfilename(title="Export library", defaultextension=".json", initialfile="game-resp-library.json", filetypes=[("JSON library","*.json")])
        if not path: return
        try:
            Path(path).write_text(json.dumps({"games":self.games}, indent=2, ensure_ascii=False), encoding="utf-8")
            self.status_var.set("Library exported")
        except OSError as exc:
            messagebox.showerror("Export failed", str(exc))

if __name__ == "__main__":
    app = GameResp()
    app.mainloop()
