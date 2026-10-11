"""Build script for Windows Packaging & Installer Generation."""

import os
import sys
import shutil
import zipfile
import subprocess
from pathlib import Path

def build_windows():
    print("=" * 60)
    print("Morphix - Building Windows Distribution")
    print("=" * 60)

    # 1. Run PyInstaller
    spec_file = Path("packaging/windows/morphix.spec")
    print(f"\n[1/3] Running PyInstaller with {spec_file}...")
    cmd = [sys.executable, "-m", "PyInstaller", str(spec_file), "--noconfirm", "--clean"]
    res = subprocess.run(cmd)
    if res.returncode != 0:
        print("[ERROR] PyInstaller build failed.")
        return False

    dist_dir = Path("dist/Morphix")
    if not dist_dir.exists():
        print("[ERROR] Expected build directory dist/Morphix was not found.")
        return False

    print("[SUCCESS] PyInstaller bundle created at dist/Morphix")

    # 2. Add quick launcher batch file to dist
    launcher_bat = dist_dir / "run_morphix.bat"
    launcher_bat.write_text("@echo off\r\nstart \"\" \"%~dp0morphix.exe\"\r\n", encoding="ascii")

    cli_bat = dist_dir / "morphix.bat"
    cli_bat.write_text("@echo off\r\n\"%~dp0morphix.exe\" %*\r\n", encoding="ascii")

    # 3. Create Portable Zip Bundle
    dist_zip = Path("dist/Morphix-v1.0.0-windows-x64.zip")
    print(f"\n[2/3] Creating portable offline zip bundle: {dist_zip}...")
    with zipfile.ZipFile(dist_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(dist_dir):
            for file in files:
                file_p = Path(root) / file
                arc_name = file_p.relative_to(Path("dist"))
                zf.write(file_p, arc_name)
    print(f"[SUCCESS] Portable distribution bundle ready: {dist_zip}")

    # 4. Check for Inno Setup compiler (ISCC.exe)
    print("\n[3/3] Checking for Inno Setup Compiler (ISCC)...")
    iscc_candidates = [
        shutil.which("iscc"),
        r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        r"C:\Program Files\Inno Setup 6\ISCC.exe",
    ]
    iscc_exe = next((c for c in iscc_candidates if c and os.path.exists(c)), None)

    if iscc_exe:
        print(f"Found Inno Setup at {iscc_exe}. Compiling Morphix-Setup.exe...")
        iss_file = Path("packaging/windows/morphix_inno_setup.iss")
        res_iss = subprocess.run([iscc_exe, str(iss_file)])
        if res_iss.returncode == 0:
            print("[SUCCESS] Created one-click Windows installer: dist/Morphix-Setup.exe")
        else:
            print("[WARNING] Inno Setup compilation returned non-zero code.")
    else:
        print("[NOTE] Inno Setup (ISCC.exe) is not installed on this build machine.")
        print("The complete standalone distribution and installer script are prepared:")
        print(f"  - Standalone Application: {dist_dir.resolve()}")
        print(f"  - Portable Zip Bundle:   {dist_zip.resolve()}")
        print(f"  - Inno Setup Script:     {Path('packaging/windows/morphix_inno_setup.iss').resolve()}")
        print("To generate Morphix-Setup.exe, install Inno Setup 6 and run 'iscc packaging/windows/morphix_inno_setup.iss'.")

    print("\n" + "=" * 60)
    print("Windows Build Finished Successfully!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    success = build_windows()
    sys.exit(0 if success else 1)
