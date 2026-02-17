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
        self.root.geometry("400x520")

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

        self._windower_chk = tk.BooleanVar(
            value=bool(self.config.get("windower_path")))
        if self.config.get("windower_path"):
            tk.Checkbutton(chk_frame, text="Use Windower",
                           variable=self._windower_chk, bg=BG, fg=FG,
                           selectcolor=BG_ENTRY, activebackground=BG,
                           activeforeground=FG,
                           font=("Segoe UI", 9)).pack(side="left", padx=(15, 0))

        # Buttons
        self._button(frame, "Login", self._login,
                     colour=GREEN_BTN, width=30).pack(pady=(15, 6))
        self._button(frame, "Create Account", self._create_account,
                     colour=BLUE_BTN, width=30).pack(pady=(0, 10))

        # Status
        self._status_var = tk.StringVar(value="Ready")
        self._label(frame, "", size=9, colour=FG_DIM,
                    textvariable=self._status_var).pack()

        # Bottom bar
        bot = tk.Frame(frame, bg=BG)
        bot.pack(side="bottom", fill="x")

        self._label(bot,
                    f"Server: {self.config.get('server_ip', '127.0.0.1')}",
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

        action = "Creating account..." if create_account else "Logging in..."
        self._status_var.set(action)

        t = threading.Thread(target=self._do_launch,
                             args=(xiloader, server_ip,
                                   username, password, create_account),
                             daemon=True)
        t.start()

    def _do_launch(self, xiloader: str, server_ip: str,
                   username: str, password: str, create_account: bool):
        try:
            ffxi_path = self.config.get("ffxi_path", "")

            # xiloader v2.x supports --username and --password flags
            cmd = [
                xiloader,
                "--server", server_ip,
                "--username", username,
                "--password", password,
                "--hide",
            ]

            # Launch xiloader in a visible console window so its TUI works
            proc = subprocess.Popen(
                cmd,
                cwd=ffxi_path,
                creationflags=subprocess.CREATE_NEW_CONSOLE,
            )

            self._set_status("xiloader launched — follow prompts in its window")

            # Launch Windower if enabled (wait for game to start)
            if (self._windower_chk.get()
                    and self.config.get("windower_path")):
                windower = self.config["windower_path"]
                if os.path.exists(windower):
                    import time
                    time.sleep(5)
                    subprocess.Popen(
                        [windower],
                        cwd=os.path.dirname(windower))
                    self._set_status("Game + Windower launched!")

        except Exception as exc:
            self._set_status("Error")
            self.root.after(0, lambda: messagebox.showerror(
                "Error", str(exc)))

    def _set_status(self, text: str):
        self.root.after(0, lambda: self._status_var.set(text))


# ===================================================================
# Entry
# ===================================================================
if __name__ == "__main__":
    LauncherApp()
