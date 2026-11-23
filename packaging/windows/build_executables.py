"""
Compiles the C# launcher sources into Windows .exe binaries using csc.exe.
Attaches the custom aesthetic icons to each executable:
- Morphix.exe (morphix.ico)
- Setup.exe (setup.ico)
- Update.exe (update.ico)
"""

import sys
import subprocess
from pathlib import Path

CSC_PATH = Path(r"C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe")
if not CSC_PATH.exists():
    # Fallback to Framework 32-bit if 64-bit not found
    CSC_PATH = Path(r"C:\Windows\Microsoft.NET\Framework\v4.0.30319\csc.exe")

SRC_DIR = Path("packaging/windows/src")
ICONS_DIR = Path("packaging/icons")
ROOT_DIR = Path(".")

TARGETS = [
    {
        "src": SRC_DIR / "Setup.cs",
        "icon": ICONS_DIR / "setup.ico",
        "out_primary": ROOT_DIR / "Setup.exe",
        "out_alias": ROOT_DIR / "Setup-Morphix.exe",
        "name": "Morphix Setup & Installer"
    },
    {
        "src": SRC_DIR / "Update.cs",
        "icon": ICONS_DIR / "update.ico",
        "out_primary": ROOT_DIR / "Update.exe",
        "out_alias": ROOT_DIR / "Update-Morphix.exe",
        "name": "Morphix One-Click Updater"
    },
    {
        "src": SRC_DIR / "Run.cs",
        "icon": ICONS_DIR / "morphix.ico",
        "out_primary": ROOT_DIR / "Morphix.exe",
        "out_alias": ROOT_DIR / "Run-Morphix.exe",
        "name": "Morphix Runner"
    }
]

def compile_all():
    if not CSC_PATH.exists():
        print(f"Error: C# compiler not found at {CSC_PATH}")
        sys.exit(1)

    print(f"Using C# compiler: {CSC_PATH}")

    for target in TARGETS:
        src = target["src"]
        icon = target["icon"]
        out_primary = target["out_primary"]
        out_alias = target["out_alias"]

        print(f"\nBuilding {target['name']} -> {out_primary.name} ...")
        cmd = [
            str(CSC_PATH),
            "/nologo",
            "/optimize+",
            f"/win32icon:{icon}",
            f"/out:{out_primary}",
            "/target:exe",
            str(src)
        ]

        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            print(f"Compilation failed for {src}:\n{res.stderr}\n{res.stdout}")
            sys.exit(1)

        size_kb = out_primary.stat().st_size / 1024
        print(f"  [✓] Created {out_primary} ({size_kb:.1f} KB)")

        # Create alias copy
        import shutil
        shutil.copyfile(out_primary, out_alias)
        print(f"  [✓] Created alias {out_alias}")

    print("\nAll executables built successfully with aesthetic custom icons!")

if __name__ == "__main__":
    compile_all()
