# Installing Bulk Photo Editor

Pick the route that matches you. Nothing here changes your photos: the app only reads originals and writes new files.

| I am… | Do this |
|-------|---------|
| **a Windows user with a ready-made installer** | [Windows: run Setup.exe](#windows-setup-installer) |
| **on Windows, no installer, have Python** | [Windows: one-click from source](#windows-from-source-no-build-needed) |
| **on a Mac** | [macOS](#macos) |
| **the person building the installer** | [Building the Windows installer](#building-the-windows-installer) |

---

## Windows - Setup installer
1. Run **`BulkPhotoEditor-Setup-<version>.exe`**.
2. If Windows SmartScreen says *"Windows protected your PC"*: click **More info → Run anyway** (the installer is not code-signed; see *Signing* below).
3. Choose *Install just for me* (no admin needed) or *for all users*.
4. Keep **"Add Open in Bulk Photo Editor to the right-click menu"** ticked if you want it, and optionally a Desktop shortcut.
5. Finish. Start it from the Start menu.

**Using it:** drag a folder or photos onto the window, or right-click a folder → **Open in Bulk Photo Editor**.
**Uninstall:** Settings → Apps → Bulk Photo Editor → Uninstall (removes the right-click menu too).

*No installer?* Unzip `BulkPhotoEditor-<version>-portable.zip` anywhere and run `BulkPhotoEditor.exe` - no installation, no admin rights.

## Windows - from source (no build needed)
Requires **Python 3.9+** from <https://www.python.org/downloads/windows/> - during setup tick **"Add python.exe to PATH"** and keep **tcl/tk and IDLE** selected.

1. Unzip the project somewhere permanent (e.g. `C:\Apps\BulkPhotoEditor`).
2. Double-click **`packaging\windows\install_from_source.bat`**.
   It creates a private environment, installs Pillow / NumPy / tkinterdnd2, and adds *Bulk Photo Editor* shortcuts to the Desktop and Start menu.
3. Start it from the shortcut. To remove: `packaging\windows\uninstall_from_source.bat`.

Prefer the command line? `pip install -r requirements.txt` then `python run.py` (or drag a folder onto `scripts\run_windows.bat`).

## macOS
Requires macOS 11+ and Python with Tk (python.org installer, or `brew install python-tk`).

```bash
pip3 install -r requirements-macos.txt
./packaging/build_mac_app.sh --install      # builds "Bulk Photo Editor.app", copies it to /Applications and installs the Finder Quick Action
```
Or just run from source: `python3 run.py`. Details, signing and troubleshooting: [docs/PACKAGING.md](docs/PACKAGING.md).

## Building the Windows installer
On a Windows PC (the build cannot be done from macOS/Linux):

1. Install **Python 3.9+** (python.org; *Add to PATH*, *tcl/tk* ticked).
2. Optional but recommended: install **Inno Setup 6** (free) from <https://jrsoftware.org/isdl.php> so a proper `Setup.exe` is produced.
3. In the project folder run **`packaging\windows\build_windows.bat`**.

Outputs in `dist\`:

| File | What it is |
|------|-----------|
| `BulkPhotoEditor\BulkPhotoEditor.exe` | the app folder (run directly) |
| `BulkPhotoEditor-<version>-portable.zip` | zip of that folder - unzip and run |
| `BulkPhotoEditor-Setup-<version>.exe` | the installer (needs Inno Setup 6) |

### Signing (optional)
Unsigned installers trigger a SmartScreen warning on other PCs. To avoid it, sign `BulkPhotoEditor.exe` and the Setup with a code-signing certificate
(`signtool sign /fd SHA256 /a /tr http://timestamp.digicert.com /td SHA256 <file>`).

## Troubleshooting
| Problem | Fix |
|---------|-----|
| "Python was not found" | Reinstall Python and tick **Add python.exe to PATH**; reopen the window |
| "This Python has no Tk" / `No module named tkinter` | Run the Python installer → *Modify* → tick **tcl/tk and IDLE** |
| Drag-and-drop does nothing | `pip install tkinterdnd2` (the Windows installer / portable build already include it). Add files / Add folder always work |
| Window looks blurry on a 4K / scaled display | Fixed in v6.1 (DPI-aware). Update, or right-click the exe → Properties → Compatibility → *Change high DPI settings* |
| Antivirus flags the `.exe` | PyInstaller apps are sometimes flagged by mistake; build it yourself or sign it, and allow-list the folder |
| Right-click menu entry missing | Re-run Setup and tick the *right-click menu* task; Windows 11 shows it under **Show more options** |
