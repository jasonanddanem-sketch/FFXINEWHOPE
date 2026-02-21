"""
New Hope - FFXI Launcher
Connects to a LandSandBoat private server via Ashita.
"""

import tkinter as tk
from tkinter import filedialog, messagebox
import json
import os
import subprocess
import threading
import sys
import urllib.request

# ---------------------------------------------------------------------------
# Version & Repo
# ---------------------------------------------------------------------------
VERSION = "2.0"
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
# Ashita addon download (custom GitHub repos)
# ---------------------------------------------------------------------------
GITHUB_GSUI_API = "https://api.github.com/repos/jasonanddanem-sketch/GSUI/contents"
HD_MAPS_ZIP = "https://github.com/criticalxi/xicombinedmaps/archive/refs/heads/main.zip"
HD_MAPS_SUBDIR = "xicombinedmaps-main/2048x2048"  # path inside the zip

# Plugins that are always loaded (essential for Ashita operation)
ESSENTIAL_PLUGINS = {"Addons", "Thirdparty"}

# Default selections for first-time users
DEFAULT_PLUGINS = {"Addons", "Thirdparty", "Screenshot", "Minimap"}
DEFAULT_ADDONS = {
    "hideconsole", "distance", "fps", "move", "timestamp", "tparty",
}

# Addons available for download from GitHub (not bundled)
DOWNLOADABLE_ADDONS = {
    "GSUI": GITHUB_GSUI_API,
}


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

        # Auto-detect bundled Ashita next to the launcher (or parent dir)
        if not self.config.get("ashita_path"):
            for base in (APP_DIR, os.path.dirname(APP_DIR)):
                bundled = os.path.join(base, "Ashita", "Ashita-cli.exe")
                if os.path.exists(bundled):
                    self.config["ashita_path"] = bundled
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
                    r"e.g.  D:\FFXI\SquareEnix  (folder containing "
                    "PlayOnline & FINAL FANTASY XI)",
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
                     colour=ORANGE, width=30).pack(pady=(0, 6))
        self._button(frame, "Download HD Maps", self._download_hd_maps,
                     colour=BG_LIGHT, width=30).pack(pady=(0, 10))

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

        # Check for Ashita
        ashita_path = self.config.get("ashita_path", "")
        if not ashita_path or not os.path.exists(ashita_path):
            messagebox.showerror(
                "Ashita Not Found",
                "Could not find Ashita-cli.exe.\n\n"
                "Make sure the Ashita folder is next to the launcher.")
            return

        server_ip = self.config.get("server_ip", "127.0.0.1")

        if create_account:
            # For account creation, use xiloader if present
            xiloader = os.path.join(APP_DIR, "xiloader.exe")
            if not os.path.exists(xiloader):
                messagebox.showerror(
                    "xiloader.exe Not Found",
                    "Account creation requires xiloader.exe.\n"
                    f"Place it in:\n{APP_DIR}")
                return
            self._status_var.set("Creating account...")
            t = threading.Thread(
                target=self._do_create_account,
                args=(xiloader, server_ip, username, password),
                daemon=True)
            t.start()
        else:
            self._status_var.set("Launching game...")
            t = threading.Thread(
                target=self._do_launch_ashita,
                args=(ashita_path, server_ip, username, password),
                daemon=True)
            t.start()

    def _do_create_account(self, xiloader: str, server_ip: str,
                           username: str, password: str):
        """Create an account via xiloader, then launch Ashita."""
        try:
            ffxi_path = self.config.get("ffxi_path", "")
            cmd = [
                xiloader,
                "--server", server_ip,
                "--user", username,
                "--pass", password,
            ]
            self._set_status("Creating account...")
            subprocess.Popen(
                cmd,
                cwd=ffxi_path if ffxi_path else APP_DIR,
                creationflags=subprocess.CREATE_NEW_CONSOLE,
            )
            self._set_status("Account creation started! Close xiloader when done.")
        except Exception as exc:
            self._set_status("Error")
            self.root.after(0, lambda: messagebox.showerror("Error", str(exc)))

    def _do_launch_ashita(self, ashita_path: str, server_ip: str,
                          username: str, password: str):
        """Generate Ashita boot config and launch the game."""
        try:
            ashita_dir = os.path.dirname(ashita_path)
            ffxi_path = self.config.get("ffxi_path", "")

            # Generate the boot .ini
            self._set_status("Writing Ashita config...")
            ini_path = os.path.join(ashita_dir, "config", "boot", "newhope.ini")
            os.makedirs(os.path.dirname(ini_path), exist_ok=True)
            self._write_boot_ini(ini_path, server_ip, username, password,
                                 ffxi_path)

            # Launch Ashita-cli.exe with the config
            self._set_status("Starting Ashita...")
            subprocess.Popen(
                [ashita_path, "newhope.ini"],
                cwd=ashita_dir,
            )
            self._set_status("Game launched with Ashita!")

        except Exception as exc:
            self._set_status("Error")
            self.root.after(0, lambda: messagebox.showerror(
                "Error", str(exc)))

    # ------------------------------------------------------------------
    # Ashita boot .ini generation
    # ------------------------------------------------------------------
    def _write_boot_ini(self, ini_path: str, server_ip: str,
                        username: str, password: str, ffxi_path: str):
        """Write the Ashita boot configuration file."""

        # Detect FFXI subdirectory paths for sandbox
        pol_path, ffxi_game_path = self._detect_ffxi_paths(ffxi_path)

        # Read the current startup script to see if user has customized it
        ashita_dir = os.path.dirname(os.path.dirname(os.path.dirname(ini_path)))
        script_path = os.path.join(ashita_dir, "scripts", "newhope_addons.txt")
        script_name = "newhope_addons.txt"

        # If the startup script doesn't exist yet, create default one
        if not os.path.exists(script_path):
            self._write_default_script(ashita_dir)

        # Escape password for the command line (wrap in quotes if needed)
        safe_pass = password.replace('"', '\\"')

        ini_content = f"""; New Hope - Ashita v4 Boot Configuration
; Auto-generated by New Hope Launcher v{VERSION}

[ashita.launcher]
autoclose = 1
name = NewHope

[ashita.boot]
file = .\\bootloader\\pol.exe
command = --server {server_ip} --user {username} --password "{safe_pass}"
gamemodule = ffximain.dll
script = {script_name}
args =

[ashita.language]
playonline = 0
ashita = 0

[ashita.logging]
level = 0
crashdumps = 1

[ashita.taskpool]
threadcount = -1

[ashita.resources]
offsets.use_overrides = 1
pointers.use_overrides = 1
resources.use_overrides = 1

[ashita.window.startpos]
x = -1
y = -1

[ashita.input]
gamepad.allowbackground = 0
gamepad.disableenumeration = 0
keyboard.blockinput = 0
keyboard.blockbindsduringinput = 0
keyboard.silentbinds = 0
keyboard.windowskeyenabled = 1
mouse.blockinput = 0
mouse.unhook = 1

[ashita.misc]
addons.silent = 0
aliases.silent = 0
plugins.silent = 0

[ashita.polplugins]
sandbox = 1
pivot = 1

[ashita.polplugins.args]

[ffxi.direct3d8]
presentparams.backbufferformat = -1
presentparams.backbuffercount = -1
presentparams.multisampletype = -1
presentparams.swapeffect = -1
presentparams.enableautodepthstencil = -1
presentparams.autodepthstencilformat = -1
presentparams.flags = -1
presentparams.fullscreen_refreshrateinhz = -1
presentparams.fullscreen_presentationinterval = -1
behaviorflags.fpu_preserve = 0

[ffxi.registry]
0000 = 6
0001 = 1920
0002 = 1080
0003 = 2048
0004 = 2048
0007 = 1
0011 = 2
0017 = 0
0018 = 2
0019 = 2
0021 = 1
0022 = 0
0028 = 0
0029 = 12
0034 = 3
0035 = 1
0036 = 0
0037 = 1920
0038 = 1080
0039 = 1
0040 = 0
0041 = 1
0043 = 1
0044 = 1

[sandbox.paths]
common = C:\\Program Files (x86)\\Common Files
pol = {pol_path}
ffxi = {ffxi_game_path}
"""
        with open(ini_path, "w", encoding="utf-8") as f:
            f.write(ini_content)

    @staticmethod
    def _detect_ffxi_paths(ffxi_base: str) -> tuple[str, str]:
        """Auto-detect PlayOnline and FFXI game directories."""
        pol_path = ""
        ffxi_path = ""

        if not ffxi_base or not os.path.isdir(ffxi_base):
            return pol_path, ffxi_path

        for name in os.listdir(ffxi_base):
            full = os.path.join(ffxi_base, name)
            if not os.path.isdir(full):
                continue
            low = name.lower()
            if "playonline" in low:
                pol_path = full
            elif "final fantasy" in low or "ffxi" in low:
                ffxi_path = full

        return pol_path, ffxi_path

    # ------------------------------------------------------------------
    # Ashita startup script generation
    # ------------------------------------------------------------------
    def _write_default_script(self, ashita_dir: str):
        """Write the default newhope_addons.txt startup script."""
        script_path = os.path.join(ashita_dir, "scripts", "newhope_addons.txt")
        os.makedirs(os.path.dirname(script_path), exist_ok=True)

        lines = [
            "##########################################################################",
            "# New Hope - Ashita Startup Script",
            f"# Auto-generated by New Hope Launcher v{VERSION}",
            "#",
            "# This file is managed by the launcher's Addons picker.",
            "# Manual edits will be overwritten when you save in the Addons dialog.",
            "##########################################################################",
            "",
            "# Load Plugins",
        ]

        for plugin in sorted(DEFAULT_PLUGINS, key=str.lower):
            lines.append(f"/load {plugin.lower()}")

        lines.append("")
        lines.append("# Load Addons")

        for addon in sorted(DEFAULT_ADDONS, key=str.lower):
            lines.append(f"/addon load {addon}")

        lines.append("")
        lines.append("##########################################################################")
        lines.append("# Keybinds")
        lines.append("##########################################################################")
        lines.append("")
        lines.append("/bind insert /ashita")
        lines.append("/bind SYSRQ /screenshot hide")
        lines.append("/bind ^v /paste")
        lines.append("/bind F11 /ambient")
        lines.append("/bind F12 /fps")

        with open(script_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")

    # ------------------------------------------------------------------
    # Parse / write startup script for addon picker
    # ------------------------------------------------------------------
    @staticmethod
    def _read_script(script_path: str) -> tuple[set, set]:
        """Parse the startup script and return (enabled_addons, enabled_plugins)."""
        addons: set[str] = set()
        plugins: set[str] = set()

        if not os.path.exists(script_path):
            return addons, plugins

        try:
            with open(script_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("/addon load "):
                        name = line[len("/addon load "):].strip()
                        if name:
                            addons.add(name)
                    elif line.startswith("/load "):
                        name = line[len("/load "):].strip()
                        if name:
                            plugins.add(name)
        except Exception:
            pass

        return addons, plugins

    @staticmethod
    def _write_script(script_path: str, addon_vars: dict, plugin_vars: dict):
        """Write the startup script from the addon/plugin picker state."""
        os.makedirs(os.path.dirname(script_path), exist_ok=True)

        lines = [
            "##########################################################################",
            "# New Hope - Ashita Startup Script",
            "# Managed by the launcher's Addons picker.",
            "##########################################################################",
            "",
            "# Load Plugins",
        ]

        for name in sorted(plugin_vars.keys(), key=str.lower):
            if plugin_vars[name].get():
                lines.append(f"/load {name.lower()}")

        lines.append("")
        lines.append("# Load Addons")

        for name in sorted(addon_vars.keys(), key=str.lower):
            if addon_vars[name].get():
                lines.append(f"/addon load {name}")

        lines.append("")
        lines.append("##########################################################################")
        lines.append("# Keybinds")
        lines.append("##########################################################################")
        lines.append("")
        lines.append("/bind insert /ashita")
        lines.append("/bind SYSRQ /screenshot hide")
        lines.append("/bind ^v /paste")
        lines.append("/bind F11 /ambient")
        lines.append("/bind F12 /fps")

        # Post-load config (wait for addons to initialize)
        lines.append("")
        lines.append("/wait 3")
        lines.append("/ambient 255 255 255 255")

        with open(script_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")

    # ------------------------------------------------------------------
    # Scan Ashita addons & plugins
    # ------------------------------------------------------------------
    @staticmethod
    def _scan_addons(ashita_dir: str) -> list[str]:
        """Return sorted list of addon names found in Ashita's addons/ dir."""
        addons_dir = os.path.join(ashita_dir, "addons")
        if not os.path.isdir(addons_dir):
            return []
        skip = {"libs"}
        addons = []
        for name in os.listdir(addons_dir):
            if os.path.isdir(os.path.join(addons_dir, name)):
                if name.lower() not in skip:
                    addons.append(name)
        return sorted(addons, key=str.lower)

    @staticmethod
    def _scan_plugins(ashita_dir: str) -> list[str]:
        """Return sorted list of plugin names (no .dll) from plugins/ dir."""
        plugins_dir = os.path.join(ashita_dir, "plugins")
        if not os.path.isdir(plugins_dir):
            return []
        skip = {"sdk"}
        plugins = []
        for name in os.listdir(plugins_dir):
            full = os.path.join(plugins_dir, name)
            if name.lower().endswith(".dll") and os.path.isfile(full):
                plugins.append(name[:-4])  # strip .dll
        return sorted(plugins, key=str.lower)

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

    def _download_addon(self, addon_name: str, ashita_dir: str,
                        status_cb, done_cb) -> None:
        """Download an addon from GitHub (runs on a background thread)."""
        import shutil

        addons_dir = os.path.join(ashita_dir, "addons")
        temp_dir = os.path.join(addons_dir, f"{addon_name}_downloading")
        final_dir = os.path.join(addons_dir, addon_name)

        try:
            api_url = DOWNLOADABLE_ADDONS.get(addon_name)
            if not api_url:
                raise RuntimeError(f"No download source for {addon_name}")

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
        ashita_path = self.config.get("ashita_path", "")
        if not ashita_path:
            messagebox.showinfo("Ashita Not Found",
                                "Ashita was not detected.")
            return
        ashita_dir = os.path.dirname(ashita_path)
        script_path = os.path.join(ashita_dir, "scripts", "newhope_addons.txt")

        addons = self._scan_addons(ashita_dir)
        plugins = self._scan_plugins(ashita_dir)
        enabled_addons, enabled_plugins = self._read_script(script_path)

        # If no script exists yet, use defaults
        first_time = not os.path.exists(script_path)
        if first_time:
            enabled_addons = DEFAULT_ADDONS.copy()
            enabled_plugins = {p.lower() for p in DEFAULT_PLUGINS}

        # --- Build popup ---
        popup = tk.Toplevel(self.root)
        popup.title("Addons & Plugins")
        popup.configure(bg=BG)
        popup.geometry("400x600")
        popup.resizable(False, True)
        popup.transient(self.root)
        popup.grab_set()

        # Header
        self._label(popup, "Ashita Addons & Plugins", size=13, bold=True,
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

        # --- Plugins section (shown first since they're fewer) ---
        self._label(inner, "Plugins", size=11, bold=True,
                    colour=GOLD).pack(pady=(6, 0))
        tk.Frame(inner, bg=GOLD, height=1).pack(fill="x", pady=(0, 4))

        if plugins:
            for name in plugins:
                checked = (name.lower() in {p.lower() for p in enabled_plugins}
                           or name in ESSENTIAL_PLUGINS)
                var = tk.BooleanVar(value=checked)
                plugin_vars[name] = var

                cb = tk.Checkbutton(
                    inner, text=name, variable=var,
                    bg=BG, fg=FG, selectcolor=BG_ENTRY,
                    activebackground=BG, activeforeground=FG,
                    font=("Segoe UI", 9), anchor="w")

                # Essential plugins are always checked and disabled
                if name in ESSENTIAL_PLUGINS:
                    cb.configure(state="disabled",
                                 disabledforeground=FG_DIM)
                    var.set(True)

                cb.pack(fill="x", padx=20)
        else:
            self._label(inner, "No plugins found.", size=9,
                        colour=FG_DIM).pack(padx=20)

        # --- Installed Addons section ---
        self._label(inner, "Addons", size=11, bold=True,
                    colour=GOLD).pack(pady=(12, 0))
        tk.Frame(inner, bg=GOLD, height=1).pack(fill="x", pady=(0, 4))

        if addons:
            for name in addons:
                checked = (name in enabled_addons
                           or name.lower() in {a.lower() for a in enabled_addons}
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

        # --- Available Addons (Download) section ---
        installed_lower = {a.lower() for a in addons}
        available = [name for name in DOWNLOADABLE_ADDONS
                     if name.lower() not in installed_lower]

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
                        args=(name, ashita_dir, _status, _done),
                        daemon=True)
                    t.start()

                dl_btn.configure(command=_start_download)

        # --- Buttons ---
        btn_frame = tk.Frame(popup, bg=BG)
        btn_frame.pack(fill="x", padx=10, pady=(8, 12))

        def _save():
            try:
                self._write_script(script_path, addon_vars, plugin_vars)
                self._newly_downloaded.clear()
                popup.destroy()
            except Exception as exc:
                messagebox.showerror("Error",
                                     f"Could not save startup script:\n{exc}")

        self._button(btn_frame, "Save", _save,
                     colour=GREEN_BTN, width=12).pack(side="left", expand=True)
        self._button(btn_frame, "Cancel", popup.destroy,
                     colour=BG_LIGHT, width=12).pack(side="left", expand=True)

        popup.protocol("WM_DELETE_WINDOW", popup.destroy)

    # ------------------------------------------------------------------
    # HD Maps download
    # ------------------------------------------------------------------
    def _download_hd_maps(self):
        """Download HD combined maps from GitHub and install into Ashita."""
        ashita_path = self.config.get("ashita_path", "")
        if not ashita_path:
            messagebox.showinfo("Ashita Not Found",
                                "Ashita was not detected.")
            return

        ashita_dir = os.path.dirname(ashita_path)
        maps_dir = os.path.join(ashita_dir, "polplugins", "DATs",
                                "xicombinedmaps")

        # Check if already installed
        if os.path.isdir(maps_dir) and os.listdir(maps_dir):
            result = messagebox.askyesno(
                "HD Maps Already Installed",
                "HD Combined Maps are already installed.\n\n"
                "Do you want to re-download and replace them?")
            if not result:
                return

        result = messagebox.askyesno(
            "Download HD Maps",
            "This will download the HD Combined Maps pack\n"
            "from github.com/criticalxi/xicombinedmaps\n\n"
            "Download size: ~600 MB\n\n"
            "The maps will be installed into Ashita's\n"
            "Pivot overlay directory.\n\n"
            "Continue?")
        if not result:
            return

        self._status_var.set("Downloading HD Maps...")
        t = threading.Thread(target=self._do_download_hd_maps,
                             args=(ashita_dir,), daemon=True)
        t.start()

    def _do_download_hd_maps(self, ashita_dir: str):
        """Download and extract HD maps (runs on background thread)."""
        import zipfile
        import shutil

        maps_dir = os.path.join(ashita_dir, "polplugins", "DATs",
                                "xicombinedmaps")
        zip_path = os.path.join(ashita_dir, "polplugins", "DATs",
                                "_hdmaps_download.zip")

        try:
            os.makedirs(os.path.dirname(zip_path), exist_ok=True)

            # Download the zip
            self._set_status("Downloading HD Maps (this may take a while)...")
            req = urllib.request.Request(
                HD_MAPS_ZIP,
                headers={"User-Agent": "NewHopeLauncher"})
            with urllib.request.urlopen(req, timeout=600) as resp:
                total = int(resp.headers.get("Content-Length", 0))
                downloaded = 0
                with open(zip_path, "wb") as f:
                    while True:
                        chunk = resp.read(131072)  # 128KB chunks
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total > 0:
                            pct = int(downloaded * 100 / total)
                            mb = downloaded // (1024 * 1024)
                            self._set_status(
                                f"Downloading HD Maps... {mb} MB ({pct}%)")

            self._set_status("Extracting HD Maps...")

            # Extract only the 2048x2048 subdirectory
            if os.path.isdir(maps_dir):
                shutil.rmtree(maps_dir)
            os.makedirs(maps_dir, exist_ok=True)

            with zipfile.ZipFile(zip_path, "r") as zf:
                prefix = HD_MAPS_SUBDIR + "/"
                members = [m for m in zf.namelist()
                           if m.startswith(prefix) and not m.endswith("/")]
                total_files = len(members)
                for i, member in enumerate(members):
                    # Strip the prefix to get relative path (ROM/xxx/yyy.DAT)
                    rel_path = member[len(prefix):]
                    if not rel_path:
                        continue
                    dest = os.path.join(maps_dir, rel_path.replace("/", os.sep))
                    os.makedirs(os.path.dirname(dest), exist_ok=True)
                    with zf.open(member) as src, open(dest, "wb") as dst:
                        shutil.copyfileobj(src, dst)
                    if (i + 1) % 50 == 0 or i + 1 == total_files:
                        self._set_status(
                            f"Extracting HD Maps... {i + 1}/{total_files}")

            # Clean up zip
            os.remove(zip_path)

            self._set_status("HD Maps installed!")
            self.root.after(0, lambda: messagebox.showinfo(
                "HD Maps Installed",
                "HD Combined Maps have been installed.\n\n"
                "They will be loaded by Pivot on next game launch."))

        except Exception as exc:
            self._set_status("HD Maps download failed.")
            # Clean up on failure
            if os.path.exists(zip_path):
                os.remove(zip_path)
            self.root.after(0, lambda: messagebox.showerror(
                "Download Error",
                f"Could not download HD Maps:\n\n{exc}"))

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

            # Download the exe from GitHub Releases
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


# ===================================================================
# Entry
# ===================================================================
if __name__ == "__main__":
    LauncherApp()
