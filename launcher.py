"""
New Hope - FFXI Launcher
Connects to a LandSandBoat private server via xiloader.
"""

import tkinter as tk
from tkinter import filedialog, messagebox
import json
import os
import subprocess
import threading
import sys
import urllib.request
import tempfile

# ---------------------------------------------------------------------------
# Version & Repo
# ---------------------------------------------------------------------------
VERSION = "1.6"
REPO_RAW = "https://raw.githubusercontent.com/jasonanddanem-sketch/FFXINEWHOPE/main"

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
if getattr(sys, "frozen", False):
    APP_DIR = os.path.dirname(sys.executable)
    # PyInstaller --onefile extracts bundled data to a temp dir
    DATA_DIR = getattr(sys, "_MEIPASS", APP_DIR)
else:
    APP_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_DIR = APP_DIR

CONFIG_FILE = os.path.join(APP_DIR, "config.json")

# ---------------------------------------------------------------------------
# Colours (dark theme)
# ---------------------------------------------------------------------------
BG        = "#1a1a2e"
BG_LIGHT  = "#16213e"
BG_ENTRY  = "#0f3460"
FG        = "#e0e0e0"
FG_DIM    = "#888888"
GOLD      = "#e2b714"
BLUE_BTN  = "#1a73e8"
GREEN_BTN = "#2e7d32"
RED_BTN   = "#c62828"
ORANGE    = "#e67e22"

# ---------------------------------------------------------------------------
# Official Windower addons (from github.com/Windower/Lua)
# ---------------------------------------------------------------------------
GITHUB_ADDON_API = "https://api.github.com/repos/Windower/Lua/contents/addons"
GITHUB_GSUI_API  = "https://api.github.com/repos/jasonanddanem-sketch/GSUI/contents"

WINDOWER_ADDONS = [
    "AnnounceTarget", "AutoControl", "AutoJoin", "AutoRA", "AutoReply",
    "AutoRoll", "AzureSets", "BattleMod", "BattleStations", "Blist",
    "BlockList", "BluGuide", "BoxDestroyer", "Cancel", "Capes",
    "CapeTracker", "Chars", "ChatLink", "ChatPorter", "Clock",
    "Clue", "ConsoleBG", "CraftMon", "DamageMeter", "DanceMon",
    "DebuffNotify", "Distance", "DistancePlus", "DressUp", "DynamisHelper",
    "EasyFarm", "EnemyBar", "EquipViewer", "Eval", "FastCS",
    "FindAll", "FishBuddy", "Folio", "GameTime", "GearInfo",
    "GearSwap", "GilTracker", "GSUI", "HealBot", "HideConsole", "InfoBar",
    "InstaLS", "IPC", "ItemCollector", "JobChange", "Jump",
    "KeyItems", "Linker", "Logger", "MacroChanger", "Mappy",
    "MeritPointCalc", "MobTracker", "NamePlates", "OBI", "Organizer",
    "PetSchool", "PetTP", "PointWatch", "Porter", "Pouches",
    "Respond", "Reive", "RollTracker", "Runic", "Scoreboard",
    "Sell", "SetBGM", "Shortcuts", "SilverLibs", "Songs",
    "Sparks", "SpellCheck", "StatusTimer", "TFour", "Texts",
    "Timers", "Timestamp", "TParty", "Treasury", "TreasurePool",
    "Trusts", "Update", "VanaTunes", "VisibleFavor", "WAR",
    "WatchDog", "Weather", "WS", "XIPivot", "Yush",
]

# ===================================================================
# Main Application
# ===================================================================
class LauncherApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("New Hope - FFXI")
        self.root.configure(bg=BG)
        self.root.resizable(False, False)

        # Set window icon
        self._set_window_icon()

        self.config = self._load_config()

        # Auto-detect bundled Windower next to the launcher (or parent dir)
        if not self.config.get("windower_path"):
            for base in (APP_DIR, os.path.dirname(APP_DIR)):
                bundled = os.path.join(base, "Windower", "Windower.exe")
                if os.path.exists(bundled):
                    self.config["windower_path"] = bundled
                    self._save_config()
                    break

        # Track freshly downloaded addons (auto-checked when dialog reopens)
        self._newly_downloaded: set[str] = set()
        self._download_active = False

        # Load logo images (keep references to prevent garbage collection)
        self._logo_img = self._load_image("logo.png")
        self._logo_small_img = self._load_image("logo_small.png")

        # Show the right screen
        if not self.config.get("ffxi_path"):
            self._show_setup()
        else:
            self._show_login()

        # Centre the window on screen
        self.root.update_idletasks()
        self._centre_window()
        self.root.mainloop()

    # ------------------------------------------------------------------
    # Config helpers
    # ------------------------------------------------------------------
    def _load_config(self) -> dict:
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                pass
        return {}

    def _save_config(self):
        with open(CONFIG_FILE, "w") as f:
            json.dump(self.config, f, indent=2)

    # ------------------------------------------------------------------
    # UI helpers
    # ------------------------------------------------------------------
    def _set_window_icon(self):
        """Set the window/taskbar icon from icon.ico or icon.png."""
        ico_path = os.path.join(DATA_DIR, "icon.ico")
        png_path = os.path.join(DATA_DIR, "icon.png")
        try:
            if os.path.exists(ico_path):
                self.root.iconbitmap(ico_path)
            elif os.path.exists(png_path):
                icon = tk.PhotoImage(file=png_path)
                self.root.iconphoto(True, icon)
        except Exception:
            pass  # Fall back to default icon

    def _load_image(self, filename: str):
        """Load a PNG image. Checks bundled data dir first, then app dir."""
        for base in (DATA_DIR, APP_DIR):
            path = os.path.join(base, filename)
            if os.path.exists(path):
                try:
                    return tk.PhotoImage(file=path)
                except Exception:
                    continue
        return None

    def _centre_window(self):
        w = self.root.winfo_width()
        h = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (w // 2)
        y = (self.root.winfo_screenheight() // 2) - (h // 2)
        self.root.geometry(f"+{x}+{y}")

    def _clear(self):
        for w in self.root.winfo_children():
            w.destroy()

    def _label(self, parent, text, size=10, bold=False, colour=FG, **kw):
        weight = "bold" if bold else "normal"
        lbl = tk.Label(parent, text=text, font=("Segoe UI", size, weight),
                       fg=colour, bg=parent["bg"], **kw)
        return lbl

    def _entry(self, parent, textvar, show=None, width=30):
        e = tk.Entry(parent, textvariable=textvar, width=width,
                     font=("Segoe UI", 11), bg=BG_ENTRY, fg=FG,
                     insertbackground=FG, relief="flat", bd=6)
        if show:
            e.configure(show=show)
        return e

    def _button(self, parent, text, command, colour=BLUE_BTN, width=20):
        btn = tk.Button(parent, text=text, command=command,
                        font=("Segoe UI", 11, "bold"), fg="white", bg=colour,
                        activebackground=colour, activeforeground="white",
                        relief="flat", bd=0, cursor="hand2", width=width)
        return btn

    # ==================================================================
    # SETUP SCREEN (first launch + settings)
    # ==================================================================
    def _show_setup(self):
        self._clear()
        self.root.geometry("520x560")

        frame = tk.Frame(self.root, bg=BG)
        frame.pack(fill="both", expand=True, padx=30, pady=20)

        # Logo or fallback text
        if self._logo_small_img:
            tk.Label(frame, image=self._logo_small_img, bg=BG).pack(
                pady=(0, 5))
        else:
            self._label(frame, "New Hope", size=20, bold=True,
                        colour=GOLD).pack(pady=(0, 2))
        self._label(frame, "First-Time Setup", size=11,
                    colour=FG_DIM).pack(pady=(0, 15))

        # --- FFXI Path ---
        self._label(frame, "FFXI Installation Folder", size=10,
                    bold=True).pack(anchor="w")
        row1 = tk.Frame(frame, bg=BG)
        row1.pack(fill="x", pady=(2, 10))

        self._ffxi_var = tk.StringVar(value=self.config.get("ffxi_path", ""))
        self._entry(row1, self._ffxi_var, width=42).pack(side="left")
        self._button(row1, "Browse", self._browse_ffxi,
                     colour=BG_LIGHT, width=8).pack(side="right", padx=(6, 0))

        self._label(frame,
                    "e.g.  C:\\Program Files (x86)\\PlayOnline\\SquareEnix\\FINAL FANTASY XI",
                    size=8, colour=FG_DIM).pack(anchor="w", pady=(0, 6))

        # --- Server IP ---
        self._label(frame, "Server Address", size=10,
                    bold=True).pack(anchor="w")
        self._server_var = tk.StringVar(
            value=self.config.get("server_ip", "127.0.0.1"))
        self._entry(frame, self._server_var, width=52).pack(
            anchor="w", pady=(2, 2))
        self._label(frame,
                    "127.0.0.1 = same PC  |  LAN IP = home network  |  "
                    "Public IP = internet",
                    size=8, colour=FG_DIM).pack(anchor="w", pady=(0, 15))

        # --- Save ---
        self._button(frame, "Save & Continue",
                     self._save_setup, colour=GREEN_BTN,
                     width=22).pack(pady=(5, 0))

    def _browse_ffxi(self):
        path = filedialog.askdirectory(title="Select FFXI Installation Folder")
        if path:
            self._ffxi_var.set(path)

    def _save_setup(self):
        ffxi = self._ffxi_var.get().strip()
        if not ffxi:
            messagebox.showerror("Error", "FFXI path is required.")
            return
        if not os.path.isdir(ffxi):
            messagebox.showerror("Error",
                                 "FFXI path does not exist.\n\n" + ffxi)
            return

        self.config["ffxi_path"]     = ffxi
        self.config["server_ip"]     = (self._server_var.get().strip()
                                        or "127.0.0.1")
        self._save_config()
        self._show_login()

    # ==================================================================
    # LOGIN SCREEN
    # ==================================================================
    def _show_login(self):
        self._clear()
        self.root.geometry("420x680")

        frame = tk.Frame(self.root, bg=BG)
        frame.pack(fill="both", expand=True, padx=30, pady=20)

        # Logo or fallback text
        if self._logo_img:
            tk.Label(frame, image=self._logo_img, bg=BG).pack(pady=(5, 15))
        else:
            self._label(frame, "NEW HOPE", size=28, bold=True,
                        colour=GOLD).pack(pady=(10, 0))
            self._label(frame, "Final Fantasy XI", size=12,
                        colour=FG_DIM).pack(pady=(0, 30))

        # Username
        self._label(frame, "Username", size=10, bold=True).pack(anchor="w")
        self._user_var = tk.StringVar()
        self._entry(frame, self._user_var, width=34).pack(
            anchor="w", pady=(2, 10))

        # Load remembered username
        if self.config.get("remember_user") and self.config.get("username"):
            self._user_var.set(self.config["username"])

        # Password
        self._label(frame, "Password", size=10, bold=True).pack(anchor="w")
        self._pass_var = tk.StringVar()
        pw_entry = self._entry(frame, self._pass_var, show="*", width=34)
        pw_entry.pack(anchor="w", pady=(2, 8))

        # Load remembered password
        if self.config.get("remember_pass") and self.config.get("saved_pass"):
            import base64
            try:
                self._pass_var.set(
                    base64.b64decode(self.config["saved_pass"]).decode("utf-8"))
            except Exception:
                pass

        # Checkboxes row
        chk_frame = tk.Frame(frame, bg=BG)
        chk_frame.pack(anchor="w", pady=(0, 5))

        self._remember_var = tk.BooleanVar(
            value=self.config.get("remember_user", False))
        tk.Checkbutton(chk_frame, text="Remember username",
                       variable=self._remember_var, bg=BG, fg=FG,
                       selectcolor=BG_ENTRY, activebackground=BG,
                       activeforeground=FG,
                       font=("Segoe UI", 9)).pack(side="left")

        self._remember_pass_var = tk.BooleanVar(
            value=self.config.get("remember_pass", False))
        tk.Checkbutton(chk_frame, text="Remember password",
                       variable=self._remember_pass_var, bg=BG, fg=FG,
                       selectcolor=BG_ENTRY, activebackground=BG,
                       activeforeground=FG,
                       font=("Segoe UI", 9)).pack(side="left", padx=(15, 0))

        # Buttons
        self._button(frame, "Login", self._login,
                     colour=GREEN_BTN, width=30).pack(pady=(15, 6))
        self._button(frame, "Create Account", self._create_account,
                     colour=BLUE_BTN, width=30).pack(pady=(0, 6))
        self._button(frame, "Check for Updates", self._check_updates,
                     colour=ORANGE, width=30).pack(pady=(0, 10))

        # Status
        self._status_var = tk.StringVar(value="Ready")
        self._label(frame, "", size=9, colour=FG_DIM,
                    textvariable=self._status_var).pack()

        # Bottom bar
        bot = tk.Frame(frame, bg=BG)
        bot.pack(side="bottom", fill="x")

        self._label(bot,
                    f"v{VERSION}  |  Server: {self.config.get('server_ip', '127.0.0.1')}",
                    size=8, colour=FG_DIM).pack(side="left")
        self._button(bot, "Settings", self._show_setup,
                     colour=BG_LIGHT, width=8).pack(side="right")
        self._button(bot, "Addons", self._show_addons,
                     colour=BG_LIGHT, width=8).pack(side="right", padx=(0, 6))

        # Enter key to login
        self.root.bind("<Return>", lambda e: self._login())

    # ------------------------------------------------------------------
    # Launch logic
    # ------------------------------------------------------------------
    def _login(self):
        self._launch(create_account=False)

    def _create_account(self):
        self._launch(create_account=True)

    def _launch(self, create_account: bool):
        username = self._user_var.get().strip()
        password = self._pass_var.get().strip()

        if not username or not password:
            messagebox.showerror("Error",
                                 "Username and password are required.")
            return

        if len(username) < 3 or len(username) > 15:
            messagebox.showerror("Error",
                                 "Username must be 3-15 characters.")
            return

        if len(password) < 6 or len(password) > 15:
            messagebox.showerror("Error",
                                 "Password must be 6-15 characters.")
            return

        # Save preferences
        self.config["remember_user"] = self._remember_var.get()
        if self._remember_var.get():
            self.config["username"] = username
        else:
            self.config.pop("username", None)

        self.config["remember_pass"] = self._remember_pass_var.get()
        if self._remember_pass_var.get():
            import base64
            self.config["saved_pass"] = base64.b64encode(
                password.encode("utf-8")).decode("utf-8")
        else:
            self.config.pop("saved_pass", None)

        self._save_config()

        # Find xiloader
        xiloader = os.path.join(APP_DIR, "xiloader.exe")
        if not os.path.exists(xiloader):
            messagebox.showerror(
                "xiloader.exe Not Found",
                f"Place xiloader.exe in the launcher folder:\n\n{APP_DIR}")
            return

        server_ip = self.config.get("server_ip", "127.0.0.1")
        windower_path = self.config.get("windower_path", "")
        use_windower = bool(windower_path)

        action = "Creating account..." if create_account else "Logging in..."
        self._status_var.set(action)

        t = threading.Thread(target=self._do_launch,
                             args=(xiloader, server_ip,
                                   username, password,
                                   use_windower, windower_path),
                             daemon=True)
        t.start()

    def _do_launch(self, xiloader: str, server_ip: str,
                   username: str, password: str,
                   use_windower: bool, windower_path: str):
        try:
            ffxi_path = self.config.get("ffxi_path", "")

            if use_windower and windower_path and os.path.exists(windower_path):
                windower_dir = os.path.dirname(windower_path)

                # Copy xiloader.exe into the Windower folder so it can
                # be found reliably regardless of launcher install path
                import shutil
                dest_xiloader = os.path.join(windower_dir, "xiloader.exe")
                try:
                    shutil.copy2(xiloader, dest_xiloader)
                except Exception as exc:
                    self._set_status("Could not copy xiloader.")
                    self.root.after(0, lambda e=exc: messagebox.showerror(
                        "Error",
                        f"Could not copy xiloader.exe to Windower folder:\n"
                        f"{exc}"))
                    return

                # Write a "NewHope" profile into Windower's settings.xml
                # so Windower launches the game through xiloader with the
                # correct server / credentials.
                self._set_status("Configuring Windower...")
                ok = self._update_windower_profile(
                    windower_dir, server_ip, username, password)
                if not ok:
                    self._set_status("Failed to update Windower settings.")
                    self.root.after(0, lambda: messagebox.showerror(
                        "Windower Error",
                        "Could not write to Windower's settings.xml.\n\n"
                        "Make sure the Windower folder is not read-only."))
                    return

                # Launch Windower with -p to auto-start the profile
                # (skips the interactive UI and launches the game directly)
                self._set_status("Starting Windower...")
                subprocess.Popen(
                    [windower_path, "-p", "NewHope"],
                    cwd=windower_dir,
                )
                self._set_status("Game launched with Windower!")
            else:
                # No Windower — launch xiloader directly
                cmd = [
                    xiloader,
                    "--server", server_ip,
                    "--username", username,
                    "--password", password,
                    "--hide",
                ]
                self._set_status("Authenticating...")
                subprocess.Popen(
                    cmd,
                    cwd=ffxi_path,
                    creationflags=subprocess.CREATE_NEW_CONSOLE,
                )
                self._set_status("Game launched!")

        except Exception as exc:
            self._set_status("Error")
            self.root.after(0, lambda: messagebox.showerror(
                "Error", str(exc)))

    # ------------------------------------------------------------------
    # Windower profile helper
    # ------------------------------------------------------------------
    def _update_windower_profile(self, windower_dir: str,
                                 server_ip: str,
                                 username: str, password: str) -> bool:
        """Add / update a 'NewHope' profile in Windower's settings.xml
        that uses xiloader.exe as the executable with server args."""
        import xml.etree.ElementTree as ET

        settings_path = os.path.join(windower_dir, "settings.xml")
        if not os.path.exists(settings_path):
            return False

        try:
            tree = ET.parse(settings_path)
            root = tree.getroot()

            # Find or create the NewHope profile
            profile = None
            for p in root.findall("profile"):
                if p.get("name") == "NewHope":
                    profile = p
                    break

            if profile is None:
                profile = ET.SubElement(root, "profile")
                profile.set("name", "NewHope")
                # Copy useful display settings from the default profile
                default = root.find("profile[@name='']")
                if default is not None:
                    for child in default:
                        if child.tag not in ("executable", "args"):
                            copy = ET.SubElement(profile, child.tag)
                            copy.text = child.text

            # Helper to set a child element's text
            def _set(tag, text):
                el = profile.find(tag)
                if el is None:
                    el = ET.SubElement(profile, tag)
                el.text = text

            # xiloader.exe was already copied into the Windower folder
            _set("executable", "xiloader.exe")
            _set("args", (f"--server {server_ip} "
                          f"--user {username} "
                          f"--pass {password}"))

            tree.write(settings_path, encoding="utf-8",
                       xml_declaration=True)
            return True
        except Exception:
            return False

    # ------------------------------------------------------------------
    # FFXI registry helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _set_ffxi_windowed(windowed: bool):
        """Set FFXI windowed/fullscreen mode in the Windows registry."""
        try:
            import winreg
            key_path = r"SOFTWARE\PlayOnlineUS\SquareEnix\FinalFantasyXI"
            # Try both 32-bit and 64-bit registry views
            for access in [winreg.KEY_WOW64_32KEY, winreg.KEY_WOW64_64KEY]:
                try:
                    key = winreg.OpenKey(
                        winreg.HKEY_LOCAL_MACHINE, key_path,
                        0, winreg.KEY_SET_VALUE | access)
                    # 0003=0 for windowed, 0003=nonzero for fullscreen
                    winreg.SetValueEx(key, "0003", 0, winreg.REG_DWORD,
                                      0 if windowed else 1)
                    # 0037 = windowed mode flag (some FFXI versions)
                    winreg.SetValueEx(key, "0037", 0, winreg.REG_DWORD,
                                      1 if windowed else 0)
                    winreg.CloseKey(key)
                except FileNotFoundError:
                    continue
                except PermissionError:
                    continue
        except Exception:
            pass  # Non-critical, game may still work

    # ------------------------------------------------------------------
    # Update logic
    # ------------------------------------------------------------------
    def _check_updates(self):
        self._status_var.set("Checking for updates...")
        t = threading.Thread(target=self._do_check_updates, daemon=True)
        t.start()

    def _do_check_updates(self):
        import json as _json

        REPO_API = "https://api.github.com/repos/jasonanddanem-sketch/FFXINEWHOPE"

        try:
            # Fetch latest release from GitHub Releases API
            self._set_status("Checking for updates...")
            req = urllib.request.Request(
                f"{REPO_API}/releases/latest",
                headers={"Accept": "application/vnd.github.v3+json",
                         "User-Agent": "NewHopeLauncher"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                release = _json.loads(resp.read().decode("utf-8"))

            remote_version = release.get("tag_name", "").lstrip("v")
            if not remote_version:
                self._set_status("No releases found.")
                return

            if remote_version == VERSION:
                self._set_status(f"You're up to date! (v{VERSION})")
                return

            # Find the exe asset in the release
            exe_url = None
            for asset in release.get("assets", []):
                if asset["name"].lower().endswith(".exe"):
                    exe_url = asset["browser_download_url"]
                    break

            if not exe_url:
                self._set_status("Update has no download file.")
                return

            # Ask user on the main thread
            notes = release.get("body", "").strip()
            msg = (f"Update available!\n\n"
                   f"Current: v{VERSION}\n"
                   f"New: v{remote_version}\n")
            if notes:
                # Truncate long release notes
                if len(notes) > 300:
                    notes = notes[:300] + "..."
                msg += f"\n{notes}\n"
            msg += "\nDownload and install the update?"

            result = [None]
            answered = threading.Event()

            def ask():
                result[0] = messagebox.askyesno("Update Available", msg)
                answered.set()

            self.root.after(0, ask)
            answered.wait(timeout=120)

            if not result[0]:
                self._set_status("Update cancelled.")
                return

            self._set_status("Downloading update...")

            # Download the exe from GitHub Releases (handles redirects properly)
            update_path = os.path.join(APP_DIR, "NewHope Launcher_update.exe")
            dl_req = urllib.request.Request(
                exe_url, headers={"User-Agent": "NewHopeLauncher"})
            with urllib.request.urlopen(dl_req, timeout=120) as resp:
                with open(update_path, "wb") as f:
                    while True:
                        chunk = resp.read(65536)
                        if not chunk:
                            break
                        f.write(chunk)

            # Verify download is a real exe (PE header starts with MZ)
            valid = False
            if os.path.exists(update_path) and os.path.getsize(update_path) > 100000:
                with open(update_path, "rb") as f:
                    valid = f.read(2) == b"MZ"

            if not valid:
                if os.path.exists(update_path):
                    os.remove(update_path)
                self._set_status("Download failed.")
                self.root.after(0, lambda: messagebox.showerror(
                    "Error",
                    "Download failed — file is corrupted or not a valid exe."))
                return

            # Write the updater batch script
            if getattr(sys, "frozen", False):
                exe_name = os.path.basename(sys.executable)
            else:
                exe_name = "NewHope Launcher.exe"

            bat_path = os.path.join(APP_DIR, "_update.bat")
            with open(bat_path, "w") as f:
                f.write(f'@echo off\n')
                f.write(f'echo Updating New Hope Launcher...\n')
                f.write(f'timeout /t 3 /nobreak >nul\n')
                f.write(f'del "{exe_name}"\n')
                f.write(f'ren "NewHope Launcher_update.exe" "{exe_name}"\n')
                f.write(f'start "" "{exe_name}"\n')
                f.write(f'del "%~f0"\n')

            self._set_status("Restarting to apply update...")

            # Launch the batch script via cmd.exe and exit
            subprocess.Popen(
                ["cmd.exe", "/c", bat_path],
                cwd=APP_DIR,
                creationflags=subprocess.CREATE_NO_WINDOW)

            self.root.after(500, self.root.destroy)

        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                self._set_status(f"You're up to date! (v{VERSION})")
            else:
                self._set_status("Update check failed.")
                self.root.after(0, lambda: messagebox.showerror(
                    "Update Error", f"HTTP {exc.code}: {exc.reason}"))
        except urllib.error.URLError as exc:
            self._set_status("Could not reach update server.")
            self.root.after(0, lambda: messagebox.showerror(
                "Update Error",
                f"Could not reach GitHub.\n\n{exc}"))
        except Exception as exc:
            self._set_status("Update check failed.")
            self.root.after(0, lambda: messagebox.showerror(
                "Update Error", str(exc)))

    def _set_status(self, text: str):
        self.root.after(0, lambda: self._status_var.set(text))

    # ------------------------------------------------------------------
    # Addon / Plugin picker
    # ------------------------------------------------------------------
    @staticmethod
    def _scan_addons(windower_dir: str) -> list[str]:
        """Return sorted list of addon names found in Windower's addons/ dir."""
        addons_dir = os.path.join(windower_dir, "addons")
        if not os.path.isdir(addons_dir):
            return []
        skip = {"libs", "new folder", "equip viewer"}
        addons = []
        for name in os.listdir(addons_dir):
            if os.path.isdir(os.path.join(addons_dir, name)):
                if name.lower() not in skip:
                    addons.append(name)
        return sorted(addons, key=str.lower)

    @staticmethod
    def _scan_plugins(windower_dir: str) -> list[str]:
        """Return sorted list of plugin names (no .dll) from plugins/ dir."""
        plugins_dir = os.path.join(windower_dir, "plugins")
        if not os.path.isdir(plugins_dir):
            return []
        skip = {"luacore.dll"}
        plugins = []
        for name in os.listdir(plugins_dir):
            if name.lower().endswith(".dll") and name.lower() not in skip:
                plugins.append(name[:-4])  # strip .dll
        return sorted(plugins, key=str.lower)

    @staticmethod
    def _read_autoload(settings_path: str) -> tuple[set, set]:
        """Parse settings.xml and return (enabled_addons, enabled_plugins)."""
        import xml.etree.ElementTree as ET

        addons: set[str] = set()
        plugins: set[str] = set()
        if not os.path.exists(settings_path):
            return addons, plugins
        try:
            tree = ET.parse(settings_path)
            autoload = tree.getroot().find("autoload")
            if autoload is None:
                return addons, plugins
            for el in autoload.findall("addon"):
                if el.text and el.text.strip():
                    addons.add(el.text.strip())
            for el in autoload.findall("plugin"):
                if el.text and el.text.strip():
                    plugins.add(el.text.strip())
        except Exception:
            pass
        return addons, plugins

    @staticmethod
    def _save_autoload(settings_path: str, addon_vars: dict, plugin_vars: dict):
        """Write checked addons/plugins into the <autoload> section."""
        import xml.etree.ElementTree as ET

        tree = ET.parse(settings_path)
        root = tree.getroot()
        autoload = root.find("autoload")
        if autoload is None:
            autoload = ET.SubElement(root, "autoload")

        # Remove existing addon/plugin entries
        for el in list(autoload):
            if el.tag in ("addon", "plugin"):
                autoload.remove(el)

        # Write checked addons
        for name, var in sorted(addon_vars.items(), key=lambda x: x[0].lower()):
            if var.get():
                child = ET.SubElement(autoload, "addon")
                child.text = name

        # Write checked plugins
        for name, var in sorted(plugin_vars.items(), key=lambda x: x[0].lower()):
            if var.get():
                child = ET.SubElement(autoload, "plugin")
                child.text = name

        tree.write(settings_path, encoding="utf-8", xml_declaration=True)

    # ------------------------------------------------------------------
    # Addon download helpers
    # ------------------------------------------------------------------
    def _fetch_github_dir(self, api_url: str, local_dir: str,
                          status_cb) -> None:
        """Recursively download a GitHub directory via the Contents API."""
        import json as _json

        req = urllib.request.Request(
            api_url,
            headers={"Accept": "application/vnd.github.v3+json",
                     "User-Agent": "NewHopeLauncher"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            entries = _json.loads(resp.read().decode("utf-8"))

        os.makedirs(local_dir, exist_ok=True)
        for entry in entries:
            name = entry["name"]
            if entry["type"] == "dir":
                self._fetch_github_dir(entry["url"],
                                       os.path.join(local_dir, name),
                                       status_cb)
            elif entry["type"] == "file" and entry.get("download_url"):
                status_cb(f"Downloading {name}...")
                dl_req = urllib.request.Request(
                    entry["download_url"],
                    headers={"User-Agent": "NewHopeLauncher"})
                with urllib.request.urlopen(dl_req, timeout=30) as dl_resp:
                    data = dl_resp.read()
                with open(os.path.join(local_dir, name), "wb") as f:
                    f.write(data)

    def _download_addon(self, addon_name: str, windower_dir: str,
                        status_cb, done_cb) -> None:
        """Download an addon from GitHub (runs on a background thread)."""
        import shutil

        addons_dir = os.path.join(windower_dir, "addons")
        temp_dir = os.path.join(addons_dir, f"{addon_name}_downloading")
        final_dir = os.path.join(addons_dir, addon_name)

        try:
            if addon_name == "GSUI":
                api_url = GITHUB_GSUI_API
            else:
                api_url = f"{GITHUB_ADDON_API}/{addon_name}"
            self._fetch_github_dir(api_url, temp_dir, status_cb)

            # Verify we got lua files
            has_lua = any(f.endswith(".lua")
                         for f in os.listdir(temp_dir))
            if not has_lua:
                raise RuntimeError("No .lua files found — invalid addon.")

            # Move to final location
            if os.path.exists(final_dir):
                shutil.rmtree(final_dir)
            os.rename(temp_dir, final_dir)

            self._newly_downloaded.add(addon_name)
            done_cb(True, "")
        except Exception as exc:
            # Clean up temp dir on failure
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)
            done_cb(False, str(exc))
        finally:
            self._download_active = False

    # ------------------------------------------------------------------
    # Addon / Plugin dialog
    # ------------------------------------------------------------------
    def _show_addons(self):
        """Open the Addons & Plugins picker dialog."""
        windower_path = self.config.get("windower_path", "")
        if not windower_path:
            messagebox.showinfo("Windower Not Found",
                                "Windower was not detected.")
            return
        windower_dir = os.path.dirname(windower_path)
        settings_path = os.path.join(windower_dir, "settings.xml")

        if not os.path.exists(settings_path):
            messagebox.showerror(
                "Settings Not Found",
                f"Could not find settings.xml in:\n{windower_dir}\n\n"
                "Launch Windower once first to generate it.")
            return

        addons = self._scan_addons(windower_dir)
        plugins = self._scan_plugins(windower_dir)
        enabled_addons, enabled_plugins = self._read_autoload(settings_path)

        # --- Build popup ---
        popup = tk.Toplevel(self.root)
        popup.title("Addons & Plugins")
        popup.configure(bg=BG)
        popup.geometry("380x560")
        popup.resizable(False, True)
        popup.transient(self.root)
        popup.grab_set()

        # Header
        self._label(popup, "Windower Addons & Plugins", size=13, bold=True,
                    colour=GOLD).pack(pady=(12, 8))

        # Scrollable area
        container = tk.Frame(popup, bg=BG)
        container.pack(fill="both", expand=True, padx=10)

        canvas = tk.Canvas(container, bg=BG, highlightthickness=0)
        scrollbar = tk.Scrollbar(container, orient="vertical",
                                 command=canvas.yview)
        inner = tk.Frame(canvas, bg=BG)

        inner.bind("<Configure>",
                   lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas_id = canvas.create_window((0, 0), window=inner, anchor="n")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Keep inner frame centered when canvas resizes
        def _center_inner(event):
            canvas.itemconfigure(canvas_id, width=event.width)
        canvas.bind("<Configure>", _center_inner)

        # Mousewheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        def _bind_wheel(event=None):
            canvas.bind_all("<MouseWheel>", _on_mousewheel)

        def _unbind_wheel(event=None):
            canvas.unbind_all("<MouseWheel>")

        canvas.bind("<Enter>", _bind_wheel)
        canvas.bind("<Leave>", _unbind_wheel)

        addon_vars: dict[str, tk.BooleanVar] = {}
        plugin_vars: dict[str, tk.BooleanVar] = {}

        # --- Installed Addons section ---
        self._label(inner, "Installed Addons", size=11, bold=True,
                    colour=GOLD).pack(pady=(6, 0))
        tk.Frame(inner, bg=GOLD, height=1).pack(fill="x", pady=(0, 4))

        if addons:
            for name in addons:
                checked = (name in enabled_addons
                           or name in self._newly_downloaded)
                var = tk.BooleanVar(value=checked)
                addon_vars[name] = var
                tk.Checkbutton(inner, text=name, variable=var,
                               bg=BG, fg=FG, selectcolor=BG_ENTRY,
                               activebackground=BG, activeforeground=FG,
                               font=("Segoe UI", 9),
                               anchor="w").pack(fill="x", padx=20)
        else:
            self._label(inner, "No addons found.", size=9,
                        colour=FG_DIM).pack(padx=20)

        # --- Plugins section ---
        self._label(inner, "Plugins", size=11, bold=True,
                    colour=GOLD).pack(pady=(12, 0))
        tk.Frame(inner, bg=GOLD, height=1).pack(fill="x", pady=(0, 4))

        if plugins:
            for name in plugins:
                var = tk.BooleanVar(value=(name in enabled_plugins))
                plugin_vars[name] = var
                tk.Checkbutton(inner, text=name, variable=var,
                               bg=BG, fg=FG, selectcolor=BG_ENTRY,
                               activebackground=BG, activeforeground=FG,
                               font=("Segoe UI", 9),
                               anchor="w").pack(fill="x", padx=20)
        else:
            self._label(inner, "No plugins found.", size=9,
                        colour=FG_DIM).pack(padx=20)

        # --- Available Addons (Download) section ---
        installed_lower = {a.lower() for a in addons}
        available = [a for a in WINDOWER_ADDONS
                     if a.lower() not in installed_lower]

        if available:
            self._label(inner, "Available Addons (Download)", size=11,
                        bold=True, colour=ORANGE).pack(pady=(12, 0))
            tk.Frame(inner, bg=ORANGE, height=1).pack(fill="x", pady=(0, 4))

            for addon_name in available:
                row = tk.Frame(inner, bg=BG)
                row.pack(fill="x", padx=20, pady=1)

                self._label(row, addon_name, size=9).pack(
                    side="left", anchor="w")

                status_lbl = tk.Label(row, text="", font=("Segoe UI", 8),
                                      fg=FG_DIM, bg=BG)
                status_lbl.pack(side="right", padx=(4, 0))

                dl_btn = tk.Button(
                    row, text="Download", font=("Segoe UI", 8, "bold"),
                    fg="white", bg=ORANGE, activebackground=ORANGE,
                    activeforeground="white", relief="flat", bd=0,
                    cursor="hand2", width=9)
                dl_btn.pack(side="right")

                def _start_download(name=addon_name, btn=dl_btn,
                                    lbl=status_lbl):
                    if self._download_active:
                        return
                    self._download_active = True
                    btn.configure(state="disabled", text="...")

                    def _status(msg, _lbl=lbl):
                        self.root.after(0, lambda: _lbl.configure(text=msg))

                    def _done(ok, err, _popup=popup):
                        def _finish():
                            if ok:
                                # Reopen dialog so the addon appears
                                # in the installed section
                                _popup.destroy()
                                self._show_addons()
                            else:
                                btn.configure(state="normal",
                                              text="Download")
                                lbl.configure(text=f"Error: {err[:30]}")
                        self.root.after(0, _finish)

                    t = threading.Thread(
                        target=self._download_addon,
                        args=(name, windower_dir, _status, _done),
                        daemon=True)
                    t.start()

                dl_btn.configure(command=_start_download)

        # --- Buttons ---
        btn_frame = tk.Frame(popup, bg=BG)
        btn_frame.pack(fill="x", padx=10, pady=(8, 12))

        def _save():
            try:
                self._save_autoload(settings_path, addon_vars, plugin_vars)
                self._newly_downloaded.clear()
                popup.destroy()
            except Exception as exc:
                messagebox.showerror("Error",
                                     f"Could not save settings.xml:\n{exc}")

        self._button(btn_frame, "Save", _save,
                     colour=GREEN_BTN, width=12).pack(side="left", expand=True)
        self._button(btn_frame, "Cancel", popup.destroy,
                     colour=BG_LIGHT, width=12).pack(side="left", expand=True)

        popup.protocol("WM_DELETE_WINDOW", popup.destroy)


# ===================================================================
# Entry
# ===================================================================
if __name__ == "__main__":
    LauncherApp()
