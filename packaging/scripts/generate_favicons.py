"""
Generate all required favicon formats and sizes from morphix_retro_logo.png:
- favicon.ico (multi-size: 16, 24, 32, 48, 64, 128, 256)
- favicon-16.png
- favicon-32.png
- favicon.png (64x64)
- apple-touch-icon.png (180x180)
- android-chrome-192.png (192x192)
"""

from pathlib import Path
from PIL import Image

ASSETS_DIR = Path("app/web/assets")
ASSETS_DIR.mkdir(parents=True, exist_ok=True)
WEB_DIR = Path("app/web")

logo_path = ASSETS_DIR / "morphix_retro_logo.png"
if not logo_path.exists():
    raise FileNotFoundError("Master logo not found at " + str(logo_path))

logo = Image.open(logo_path).convert("RGBA")

# 1. Multi-resolution ICO
sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (24, 24), (16, 16)]
ico_images = [logo.resize(sz, Image.Resampling.LANCZOS) for sz in sizes]

ico_images[0].save(ASSETS_DIR / "morphix.ico", format="ICO", sizes=sizes, append_images=ico_images[1:])
ico_images[0].save(ASSETS_DIR / "favicon.ico", format="ICO", sizes=sizes, append_images=ico_images[1:])
ico_images[0].save(WEB_DIR / "favicon.ico", format="ICO", sizes=sizes, append_images=ico_images[1:])
print("Saved favicon.ico and morphix.ico")

# 2. PNG variants
logo.resize((16, 16), Image.Resampling.LANCZOS).save(ASSETS_DIR / "favicon-16.png", format="PNG")
logo.resize((32, 32), Image.Resampling.LANCZOS).save(ASSETS_DIR / "favicon-32.png", format="PNG")
logo.resize((64, 64), Image.Resampling.LANCZOS).save(ASSETS_DIR / "favicon.png", format="PNG")
logo.resize((180, 180), Image.Resampling.LANCZOS).save(ASSETS_DIR / "apple-touch-icon.png", format="PNG")
logo.resize((192, 192), Image.Resampling.LANCZOS).save(ASSETS_DIR / "android-chrome-192.png", format="PNG")
print("Saved PNG favicon variants")
