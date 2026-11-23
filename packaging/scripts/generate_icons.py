"""
Generate high-fidelity, aesthetic multi-resolution Windows icons (.ico) for:
1. Morphix.ico (App / Runner)
2. Setup.ico (Installer / Setup)
3. Update.ico (Sync / Updater)

Generates full icon mipmaps: 256x256, 128x128, 64x64, 48x48, 32x32, 24x24, 16x16 with alpha channel.
"""

import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

ASSETS_DIR = Path("app/web/assets")
ICONS_DIR = Path("packaging/icons")
ICONS_DIR.mkdir(parents=True, exist_ok=True)

SIZES = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (24, 24), (16, 16)]

def load_base_logo(size=512):
    logo_path = ASSETS_DIR / "morphix_retro_logo.png"
    if logo_path.exists():
        img = Image.open(logo_path).convert("RGBA")
        return img.resize((size, size), Image.Resampling.LANCZOS)
    
    # Fallback generation if logo not present
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle([20, 20, size-20, size-20], radius=80, fill=(24, 24, 32, 255), outline=(70, 130, 240, 255), width=12)
    return canvas

def create_morphix_icon():
    base = load_base_logo(512)
    
    # Generate multi-size list
    images = [base.resize(sz, Image.Resampling.LANCZOS) for sz in SIZES]
    out_path = ICONS_DIR / "morphix.ico"
    images[0].save(out_path, format="ICO", sizes=SIZES, append_images=images[1:])
    print(f"Generated {out_path} ({out_path.stat().st_size} bytes)")
    return out_path

def create_setup_icon():
    base = load_base_logo(512)
    
    # Draw an aesthetic emerald/cyan installer badge in bottom right
    badge_size = 200
    badge = Image.new("RGBA", (badge_size, badge_size), (0, 0, 0, 0))
    bdraw = ImageDraw.Draw(badge)
    
    # Badge background circle with dark shadow
    bdraw.ellipse([6, 6, badge_size-6, badge_size-6], fill=(16, 185, 129, 255), outline=(255, 255, 255, 230), width=10)
    
    # Draw install box/arrow in the center
    # Arrow pointing down into tray
    cx, cy = badge_size // 2, badge_size // 2
    
    # Down arrow
    arrow_color = (255, 255, 255, 255)
    # Shaft
    bdraw.rectangle([cx - 14, cy - 50, cx + 14, cy + 10], fill=arrow_color)
    # Arrow head
    bdraw.polygon([(cx - 40, cy + 5), (cx + 40, cy + 5), (cx, cy + 45)], fill=arrow_color)
    # Tray bracket
    bdraw.line([(cx - 48, cy + 30), (cx - 48, cy + 62), (cx + 48, cy + 62), (cx + 48, cy + 30)], fill=arrow_color, width=12)
    
    # Composite badge onto bottom-right of base
    # offset: (512 - 200 + 10, 512 - 200 + 10)
    offset_x = 512 - badge_size + 8
    offset_y = 512 - badge_size + 8
    
    # Soft badge shadow
    shadow = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
    sdraw = ImageDraw.Draw(shadow)
    sdraw.ellipse([offset_x - 6, offset_y - 6, offset_x + badge_size + 6, offset_y + badge_size + 6], fill=(0, 0, 0, 160))
    shadow = shadow.filter(ImageFilter.GaussianBlur(8))
    
    composite = Image.alpha_composite(base, shadow)
    composite.alpha_composite(badge, (offset_x, offset_y))
    
    images = [composite.resize(sz, Image.Resampling.LANCZOS) for sz in SIZES]
    out_path = ICONS_DIR / "setup.ico"
    images[0].save(out_path, format="ICO", sizes=SIZES, append_images=images[1:])
    print(f"Generated {out_path} ({out_path.stat().st_size} bytes)")
    return out_path

def create_update_icon():
    base = load_base_logo(512)
    
    # Draw an aesthetic sapphire/indigo sync badge in bottom right
    badge_size = 200
    badge = Image.new("RGBA", (badge_size, badge_size), (0, 0, 0, 0))
    bdraw = ImageDraw.Draw(badge)
    
    # Badge background circle
    bdraw.ellipse([6, 6, badge_size-6, badge_size-6], fill=(99, 102, 241, 255), outline=(255, 255, 255, 230), width=10)
    
    # Draw 2 circular sync arrows
    cx, cy = badge_size // 2, badge_size // 2
    r = 50
    arrow_color = (255, 255, 255, 255)
    
    # Arc 1: top arc
    bdraw.arc([cx - r, cy - r, cx + r, cy + r], start=210, end=390, fill=arrow_color, width=14)
    # Head 1 at 390 (which is 30 deg)
    h1_x = cx + int(r * math.cos(math.radians(30)))
    h1_y = cy + int(r * math.sin(math.radians(30)))
    bdraw.polygon([(h1_x - 10, h1_y - 18), (h1_x + 22, h1_y + 4), (h1_x - 14, h1_y + 20)], fill=arrow_color)
    
    # Arc 2: bottom arc
    bdraw.arc([cx - r, cy - r, cx + r, cy + r], start=30, end=210, fill=arrow_color, width=14)
    # Head 2 at 210 deg
    h2_x = cx + int(r * math.cos(math.radians(210)))
    h2_y = cy + int(r * math.sin(math.radians(210)))
    bdraw.polygon([(h2_x + 10, h2_y + 18), (h2_x - 22, h2_y - 4), (h2_x + 14, h2_y - 20)], fill=arrow_color)
    
    offset_x = 512 - badge_size + 8
    offset_y = 512 - badge_size + 8
    
    shadow = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
    sdraw = ImageDraw.Draw(shadow)
    sdraw.ellipse([offset_x - 6, offset_y - 6, offset_x + badge_size + 6, offset_y + badge_size + 6], fill=(0, 0, 0, 160))
    shadow = shadow.filter(ImageFilter.GaussianBlur(8))
    
    composite = Image.alpha_composite(base, shadow)
    composite.alpha_composite(badge, (offset_x, offset_y))
    
    images = [composite.resize(sz, Image.Resampling.LANCZOS) for sz in SIZES]
    out_path = ICONS_DIR / "update.ico"
    images[0].save(out_path, format="ICO", sizes=SIZES, append_images=images[1:])
    print(f"Generated {out_path} ({out_path.stat().st_size} bytes)")
    return out_path

if __name__ == "__main__":
    create_morphix_icon()
    create_setup_icon()
    create_update_icon()
    print("All icons generated successfully.")
