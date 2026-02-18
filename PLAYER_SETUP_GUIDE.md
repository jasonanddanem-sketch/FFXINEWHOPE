# NewHope FFXI - Player Setup Guide

How to connect to the NewHope private FFXI server.

---

## What You Need

1. **Final Fantasy XI installed** on your Windows PC
   - Standard PlayOnline/SquareEnix installation, or a copied FFXI folder
   - If you copied FFXI from another PC (not installed via PlayOnline), you need to register it — see "Copied FFXI Installation" below
2. **The NewHope Launcher** (two files):
   - `NewHope Launcher.exe`
   - `xiloader.exe`
3. **Tailscale VPN** (for connecting to the server)

---

## Step 1: Install Tailscale

The server uses Tailscale VPN for secure connections. You need to join the Tailscale network.

1. Download Tailscale from https://tailscale.com/download
2. Install and sign in (the server admin will need to approve your device)
3. Once connected, your PC gets a Tailscale IP (like `100.x.x.x`)
4. The server address you'll use is: **100.85.173.6**

---

## Step 2: Download the Launcher

Download both files from the GitHub releases page:
- https://github.com/jasonanddanem-sketch/FFXINEWHOPE

Place both files in the same folder:
```
Any Folder/
    NewHope Launcher.exe
    xiloader.exe
```

**Important:** Your antivirus may flag xiloader.exe — this is a false positive. You'll need to whitelist the folder or add an exception.

---

## Step 3: First-Time Setup

1. **Run `NewHope Launcher.exe` as Administrator** (right-click > Run as administrator)
   - Admin is required because xiloader needs to interact with the FFXI process
2. The first-time setup wizard will appear asking for:

### FFXI Installation Folder
- Point this to your FFXI installation, for example:
  - `C:\Program Files (x86)\PlayOnline\SquareEnix\FINAL FANTASY XI`
  - Or wherever your FFXI is installed (e.g., `D:\FFXI\SquareEnix\FINAL FANTASY XI`)

### Windower Path (Optional)
- If you use Windower, browse to your `Windower.exe`
- The launcher will start Windower automatically after the game launches
- Leave blank if you don't use Windower

### Server Address
- Enter the Tailscale server IP: **100.85.173.6**
- If playing on the same PC as the server: use `127.0.0.1`
- If on the same LAN without Tailscale: use `192.168.1.72`

3. Click **Save & Continue**

---

## Step 4: Create an Account

1. On the login screen, enter a **username** and **password**
2. Click **Create Account**
3. Your account is created on the server — remember these credentials

---

## Step 5: Log In and Play

1. Enter your username and password
2. Click **Login**
3. The launcher will:
   - Start xiloader which connects to the server
   - Launch FFXI through PlayOnline
   - Optionally start Windower after the game loads
4. At the FFXI title screen, press any key to enter the lobby
5. Create a character and enter the game

---

## Troubleshooting

### "Failed to initialize instance of polcore!"
Your FFXI registry entries are missing. See "Copied FFXI Installation" below.

### Launcher won't start / crashes immediately
- Make sure you're running as Administrator
- Make sure `xiloader.exe` is in the same folder as the launcher
- Whitelist the folder in your antivirus

### Can log in but stuck on "Downloading data..."
- Make sure Tailscale is connected (check the Tailscale icon in your system tray)
- Make sure you're using the correct server address (100.85.173.6)
- Try restarting Tailscale

### "WinError 740 requires elevation"
You need to run the launcher as Administrator. Right-click > Run as administrator.

### Game launches but shows a black screen or crashes
- Make sure your FFXI installation is working (try launching through PlayOnline normally first)
- Check that your FFXI path in the launcher settings points to the correct folder

### How to change settings after first setup
- Click the gear/settings button on the login screen to go back to the setup wizard
- Or delete `config.json` in the launcher folder to reset everything

---

## Copied FFXI Installation (No PlayOnline Install)

If you copied FFXI from another PC instead of installing through PlayOnline, Windows won't have the registry entries that FFXI needs. You need to create them manually.

### Option 1: Run the Registry Script
If provided with `setup-registry.ps1`, run it in PowerShell as Administrator:
```powershell
Set-ExecutionPolicy Bypass -Scope Process
.\setup-registry.ps1
```

### Option 2: Manual Registry Setup
1. Open Registry Editor (`regedit`)
2. Create these keys (replace `D:\FFXI` with your actual FFXI path):

```
HKEY_LOCAL_MACHINE\SOFTWARE\WOW6432Node\PlayOnlineUS\SquareEnix\PlayOnlineViewer\1000
    (Default) = D:\FFXI\SquareEnix\PlayOnlineViewer

HKEY_LOCAL_MACHINE\SOFTWARE\WOW6432Node\PlayOnlineUS\SquareEnix\FinalFantasyXI\0001
    (Default) = D:\FFXI\SquareEnix\FINAL FANTASY XI

HKEY_LOCAL_MACHINE\SOFTWARE\WOW6432Node\PlayOnlineUS\SquareEnix\FinalFantasyXI\0002
    (Default) = D:\FFXI\SquareEnix\FINAL FANTASY XI
```

3. Register the COM component (run in an Admin Command Prompt):
```cmd
regsvr32 "D:\FFXI\SquareEnix\PlayOnlineViewer\viewer\com\polcore.dll"
```
Without this, xiloader will fail with "Failed to initialize instance of polcore!"

---

## Server Info

| Setting | Value |
|---------|-------|
| Server Name | NewHope |
| Server Address (Tailscale) | 100.85.173.6 |
| Server Address (LAN) | 192.168.1.72 |
| Server Software | LandSandBoat (open-source FFXI emulator) |
| Level Cap | 99 |
| EXP Rate | 1.5x |
| Drop Rate | 5x |
| Gil Rate | 10x mob gil, 1.5x overall |
| Starting Gil | 50,000 |
| Starting Inventory | 80 slots |
| Skillup Rate | 3x |
| Movement Speed | 75 base, 100 cap, 150 mount |

---

## Ports (for reference / firewall rules)

If you need to configure your firewall, the server uses these ports:

| Port | Protocol | Purpose |
|------|----------|---------|
| 54231 | TCP | Authentication |
| 54001 | TCP | Lobby |
| 54230 | TCP | Character data |
| 54230 | UDP | Map server (gameplay) |
| 54002 | TCP | Search/Auction House |

Players generally don't need to open ports — only the server does. Tailscale handles the routing.
