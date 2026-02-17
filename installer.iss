; ============================================
; New Hope FFXI Launcher - Inno Setup Script
; ============================================
; To build the installer:
;   1. Install Inno Setup from https://jrsoftware.org/isinfo.php
;   2. Open this file in Inno Setup
;   3. Click Build > Compile
;
; Before building, make sure these files exist in dist\:
;   - NewHope Launcher.exe  (from build.bat)
;   - xiloader.exe           (place it manually)

[Setup]
AppName=New Hope FFXI Launcher
AppVersion=1.0
AppPublisher=New Hope
DefaultDirName={autopf}\New Hope FFXI
DefaultGroupName=New Hope FFXI
UninstallDisplayIcon={app}\NewHope Launcher.exe
OutputBaseFilename=NewHope_FFXI_Setup
OutputDir=installer_output
Compression=lzma2
SolidCompression=yes
ArchitecturesAllowed=x64compatible
ArchitecturesInstallMode=x64compatible
WizardStyle=modern

[Files]
Source: "dist\NewHope Launcher.exe"; DestDir: "{app}"; Flags: ignoreversion
; Uncomment the line below once you have xiloader.exe in dist\
; Source: "dist\xiloader.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\New Hope FFXI Launcher"; Filename: "{app}\NewHope Launcher.exe"
Name: "{autodesktop}\New Hope FFXI"; Filename: "{app}\NewHope Launcher.exe"

[Run]
Filename: "{app}\NewHope Launcher.exe"; Description: "Launch New Hope"; Flags: postinstall nowait skipifsilent
