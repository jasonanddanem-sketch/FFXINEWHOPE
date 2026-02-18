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
VERSION = "1.4"
REPO_RAW = "https://raw.githubusercontent.com/jasonanddanem-sketch/FFXINEWHOPE/main"

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
if getattr(sys, "frozen", False):
    APP_DIR = os.path.dirname(sys.executable)
else:
    APP_DIR = os.path.dirname(os.path.abspath(__file__))

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


# ===================================================================
# Main Application
# ===================================================================
class LauncherApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("New Hope - FFXI")
        self.root.configure(bg=BG)
        self.root.resizable(False, False)

        self.config = self._load_config()

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
        self.root.geometry("520x480")

        frame = tk.Frame(self.root, bg=BG)
        frame.pack(fill="both", expand=True, padx=30, pady=20)

        # Title
        self._label(frame, "New Hope", size=20, bold=True,
                    colour=GOLD).pack(pady=(0, 2))
        self._label(frame, "First-Time Setup", size=11,
                    colour=FG_DIM).pack(pady=(0, 20))

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

        # --- Windower Path ---
        self._label(frame, "Windower Path  (optional)", size=10,
                    bold=True).pack(anchor="w")
        row2 = tk.Frame(frame, bg=BG)
        row2.pack(fill="x", pady=(2, 10))

        self._windower_var = tk.StringVar(
            value=self.config.get("windower_path", ""))
        self._entry(row2, self._windower_var, width=42).pack(side="left")
        self._button(row2, "Browse", self._browse_windower,
                     colour=BG_LIGHT, width=8).pack(side="right", padx=(6, 0))

        self._label(frame, "Path to Windower.exe — leave blank to skip",
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

    def _browse_windower(self):
        path = filedialog.askopenfilename(
            title="Select Windower.exe",
            filetypes=[("Executable", "*.exe"), ("All files", "*.*")])
        if path:
            self._windower_var.set(path)

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
        self.config["windower_path"] = self._windower_var.get().strip()
        self.config["server_ip"]     = (self._server_var.get().strip()
                                        or "127.0.0.1")
        self._save_config()
        self._show_login()

    # ==================================================================
    # LOGIN SCREEN
    # ==================================================================
    def _show_login(self):
        self._clear()
        self.root.geometry("400x560")

        frame = tk.Frame(self.root, bg=BG)
        frame.pack(fill="both", expand=True, padx=30, pady=20)

        # Branding
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

        action = "Creating account..." if create_account else "Logging in..."
        self._status_var.set(action)

        t = threading.Thread(target=self._do_launch,
                             args=(xiloader, server_ip,
                                   username, password,
                                   windower_path),
                             daemon=True)
        t.start()

    def _do_launch(self, xiloader: str, server_ip: str,
                   username: str, password: str,
                   windower_path: str):
        try:
            import time
            ffxi_path = self.config.get("ffxi_path", "")

            # Step 1: Launch xiloader (handles auth + starts pol.exe)
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

            # Step 2: If Windower is configured, wait for FFXI to start
            # then launch Windower so it hooks into the running process
            if windower_path and os.path.exists(windower_path):
                self._set_status("Waiting for FFXI to start...")

                # Wait up to 30 seconds for pol.exe to appear
                found = False
                for i in range(30):
                    time.sleep(1)
                    try:
                        result = subprocess.run(
                            ["tasklist", "/FI", "IMAGENAME eq pol.exe", "/NH"],
                            capture_output=True, text=True, timeout=5,
                            creationflags=subprocess.CREATE_NO_WINDOW,
                        )
                        if "pol.exe" in result.stdout.lower():
                            found = True
                            break
                    except Exception:
                        pass

                if found:
                    # Give pol.exe a few more seconds to fully initialize
                    time.sleep(5)
                    self._set_status("Launching Windower...")
                    subprocess.Popen(
                        [windower_path],
                        cwd=os.path.dirname(windower_path),
                    )
                    self._set_status("Game launched with Windower!")
                else:
                    self._set_status("Game launched! (Start Windower manually if needed)")
            else:
                self._set_status("Game launched!")

        except Exception as exc:
            self._set_status("Error")
            self.root.after(0, lambda: messagebox.showerror(
                "Error", str(exc)))

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
        try:
            # Fetch remote version
            url = f"{REPO_RAW}/version.txt"
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=10) as resp:
                remote_version = resp.read().decode("utf-8").strip()

            if remote_version == VERSION:
                self._set_status(f"You're up to date! (v{VERSION})")
                return

            # New version available — ask user
            msg = (f"Update available!\n\n"
                   f"Current: v{VERSION}\n"
                   f"New: v{remote_version}\n\n"
                   f"Download and install the update?")

            do_update = [False]

            def ask():
                do_update[0] = messagebox.askyesno("Update Available", msg)

            self.root.after(0, ask)

            # Wait for user response
            import time
            while not do_update[0] and do_update == [False]:
                time.sleep(0.2)
                # Check if dialog was answered
                try:
                    self.root.after(0, lambda: None)
                except:
                    return

            # Give the dialog time to close and set the value
            time.sleep(0.5)

            if not do_update[0]:
                self._set_status("Update cancelled.")
                return

            self._set_status("Downloading update...")

            # Download new launcher exe
            exe_url = f"{REPO_RAW}/dist/NewHope%20Launcher.exe"
            update_path = os.path.join(APP_DIR, "NewHope Launcher_update.exe")

            urllib.request.urlretrieve(exe_url, update_path)

            if not os.path.exists(update_path) or os.path.getsize(update_path) < 100000:
                os.remove(update_path)
                self._set_status("Download failed.")
                self.root.after(0, lambda: messagebox.showerror(
                    "Error", "Download failed — file too small or corrupted."))
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

            # Launch the batch script and exit
            subprocess.Popen(
                [bat_path],
                cwd=APP_DIR,
                creationflags=subprocess.CREATE_NO_WINDOW)

            self.root.after(500, self.root.destroy)

        except urllib.error.URLError:
            self._set_status("Could not reach update server.")
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
