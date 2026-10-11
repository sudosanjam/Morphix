"""Build script for creating standalone offline Linux distribution bundles."""

import os
import sys
import shutil
import tarfile
import subprocess
from pathlib import Path

def create_linux_offline_bundle():
    print("=" * 60)
    print("Morphix - Creating Linux Offline Distribution Bundle")
    print("=" * 60)

    dist_dir = Path("dist")
    dist_dir.mkdir(parents=True, exist_ok=True)
    bundle_dir = dist_dir / "morphix-linux-bundle"

    if bundle_dir.exists():
        shutil.rmtree(bundle_dir)
    bundle_dir.mkdir(parents=True, exist_ok=True)

    print("[1/4] Copying application code and static assets...")
    shutil.copytree("app", bundle_dir / "app")
    shutil.copy("pyproject.toml", bundle_dir / "pyproject.toml")
    shutil.copy("requirements.txt", bundle_dir / "requirements.txt")
    shutil.copy("README.md", bundle_dir / "README.md")

    print("[2/4] Copying installer scripts...")
    pkg_linux = bundle_dir / "packaging" / "linux"
    pkg_linux.mkdir(parents=True, exist_ok=True)
    shutil.copy("packaging/linux/install.sh", bundle_dir / "install.sh")
    shutil.copy("packaging/linux/uninstall.sh", bundle_dir / "uninstall.sh")
    shutil.copy("packaging/linux/morphix.desktop", bundle_dir / "morphix.desktop")

    print("[3/4] Preparing offline wheel packages directory...")
    wheels_dir = bundle_dir / "packaging" / "linux" / "wheels"
    wheels_dir.mkdir(parents=True, exist_ok=True)

    # If running on Linux with pip, download wheels
    if sys.platform.startswith("linux"):
        print("Downloading Linux wheels for 100% offline installation...")
        cmd = [sys.executable, "-m", "pip", "download", "-r", "requirements.txt", "-d", str(wheels_dir)]
        subprocess.run(cmd)
    else:
        print("[INFO] On non-Linux host, creating offline bundle structure with setup hooks.")
        wheels_readme = wheels_dir / "README.txt"
        wheels_readme.write_text("Offline wheels can be placed here with 'pip download -r requirements.txt -d wheels/' on Linux.\n")

    print("[4/4] Creating tar.gz archive...")
    tar_path = dist_dir / "morphix-v1.0.0-linux-offline.tar.gz"
    with tarfile.open(tar_path, "w:gz") as tar:
        tar.add(bundle_dir, arcname="morphix")

    print(f"\n[SUCCESS] Offline bundle created: {tar_path.resolve()}")
    print("Usage on target Linux machine:")
    print("  tar -xzf morphix-v1.0.0-linux-offline.tar.gz")
    print("  cd morphix")
    print("  chmod +x install.sh")
    print("  ./install.sh")
    print("=" * 60)

if __name__ == "__main__":
    create_linux_offline_bundle()
