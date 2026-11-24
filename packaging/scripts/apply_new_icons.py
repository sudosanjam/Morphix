"""
Generates and replaces all application icons across:
- packaging/icons (morphix.ico, setup.ico, update.ico)
- app/web/assets (morphix.ico, favicon.ico, setup.ico, update.ico, morphix_retro_logo.png, favicons)
- app/web (favicon.ico)
from the user-provided retro icons.
"""

from pathlib import Path
from PIL import Image

SRC_DIR = Path("packaging/source_icons")
ICONS_DIR = Path("packaging/icons")
ASSETS_DIR = Path("app/web/assets")
WEB_DIR = Path("app/web")

ICONS_DIR.mkdir(parents=True, exist_ok=True)
ASSETS_DIR.mkdir(parents=True, exist_ok=True)

SIZES = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (24, 24), (16, 16)]

def make_ico(src_img: Image.Image, out_path: Path):
    imgs = []
    for sz, _ in SIZES:
        if sz >= src_img.width:
            imgs.append(src_img.resize((sz, sz), Image.Resampling.NEAREST))
        else:
            imgs.append(src_img.resize((sz, sz), Image.Resampling.LANCZOS))
    imgs[0].save(out_path, format="ICO", sizes=SIZES, append_images=imgs[1:])
    print(f"  [✓] Generated ICO: {out_path} ({out_path.stat().st_size} bytes)")

def apply_icons():
    print("Applying new icons...")

    # Load sources
    img_morphix = Image.open(SRC_DIR / "morphix_source.png").convert("RGBA")
    img_setup = Image.open(SRC_DIR / "setup_source.png").convert("RGBA")
    img_update = Image.open(SRC_DIR / "update_source.png").convert("RGBA")

    # 1. Packaging ICOs
    make_ico(img_morphix, ICONS_DIR / "morphix.ico")
    make_ico(img_setup, ICONS_DIR / "setup.ico")
    make_ico(img_update, ICONS_DIR / "update.ico")

    # 2. Web Assets ICOs
    make_ico(img_morphix, ASSETS_DIR / "morphix.ico")
    make_ico(img_morphix, ASSETS_DIR / "favicon.ico")
    make_ico(img_morphix, WEB_DIR / "favicon.ico")
    make_ico(img_setup, ASSETS_DIR / "setup.ico")
    make_ico(img_update, ASSETS_DIR / "update.ico")

    # 3. Web Logo (crisp pixel upscale of the retro tools folder)
    logo_high = img_morphix.resize((384, 384), Image.Resampling.NEAREST)
    logo_high.save(ASSETS_DIR / "morphix_retro_logo.png", format="PNG")
    print(f"  [✓] Updated logo: {ASSETS_DIR / 'morphix_retro_logo.png'}")

    # 4. Web Favicons (PNG variants)
    img_morphix.resize((16, 16), Image.Resampling.LANCZOS).save(ASSETS_DIR / "favicon-16.png", format="PNG")
    img_morphix.resize((32, 32), Image.Resampling.NEAREST).save(ASSETS_DIR / "favicon-32.png", format="PNG")
    img_morphix.resize((48, 48), Image.Resampling.NEAREST).save(ASSETS_DIR / "favicon.png", format="PNG")
    img_morphix.resize((180, 180), Image.Resampling.NEAREST).save(ASSETS_DIR / "apple-touch-icon.png", format="PNG")
    img_morphix.resize((192, 192), Image.Resampling.NEAREST).save(ASSETS_DIR / "android-chrome-192.png", format="PNG")
    print("  [✓] Updated all favicon PNG variants")

if __name__ == "__main__":
    apply_icons()
