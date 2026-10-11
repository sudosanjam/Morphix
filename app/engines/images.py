"""Pillow-powered raster image conversion and processing engine."""

import io
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from PIL import Image, ImageOps, ImageFilter, ImageEnhance

from app.engines.base import EngineCapability
from app.core.errors import ConversionFailedError, ValidationError


class ImageEngine(EngineCapability):
    name = "pillow"
    display_name = "Pillow Image Processor"

    SUPPORTED_INPUTS = ["png", "jpg", "jpeg", "webp", "gif", "bmp", "tiff", "tif", "ico"]
    SUPPORTED_OUTPUTS = ["png", "jpg", "jpeg", "webp", "gif", "bmp", "tiff", "ico"]

    @classmethod
    def is_available(cls) -> bool:
        try:
            import PIL
            return True
        except ImportError:
            return False

    @classmethod
    def get_version(cls) -> Optional[str]:
        try:
            import PIL
            return PIL.__version__
        except Exception:
            return None

    @classmethod
    def get_binary_path(cls) -> Optional[str]:
        return "bundled-python (Pillow)"

    @classmethod
    def convert(
        cls,
        source_path: Path,
        target_path: Path,
        target_format: str,
        settings: Dict[str, Any],
        progress_cb=None
    ) -> Path:
        """Convert and process image according to format and settings."""
        fmt = target_format.lower()
        if fmt == "jpeg":
            fmt = "jpg"

        if progress_cb:
            progress_cb(10, "Opening source image...")

        try:
            with Image.open(source_path) as img:
                # Handle orientation tag automatically
                try:
                    img = ImageOps.exif_transpose(img)
                except Exception:
                    pass

                # Pre-processing: Resize / Dimensions
                width = settings.get("width")
                height = settings.get("height")
                preserve_aspect = settings.get("preserve_aspect", True)
                fit_mode = settings.get("fit_mode", "contain")
                resample_name = settings.get("resample", "lanczos").lower()

                resample_filters = {
                    "lanczos": Image.Resampling.LANCZOS,
                    "bicubic": Image.Resampling.BICUBIC,
                    "bilinear": Image.Resampling.BILINEAR,
                    "nearest": Image.Resampling.NEAREST,
                }
                resample = resample_filters.get(resample_name, Image.Resampling.LANCZOS)

                orig_w, orig_h = img.size

                if width or height:
                    target_w = int(width) if width else orig_w
                    target_h = int(height) if height else orig_h

                    if preserve_aspect:
                        if width and not height:
                            target_h = int(orig_h * (target_w / orig_w))
                        elif height and not width:
                            target_w = int(orig_w * (target_h / orig_h))
                        elif fit_mode == "contain":
                            ratio = min(target_w / orig_w, target_h / orig_h)
                            target_w = int(orig_w * ratio)
                            target_h = int(orig_h * ratio)
                        elif fit_mode == "cover":
                            ratio = max(target_w / orig_w, target_h / orig_h)
                            new_w, new_h = int(orig_w * ratio), int(orig_h * ratio)
                            img = img.resize((new_w, new_h), resample=resample)
                            # Crop center
                            left = (new_w - target_w) // 2
                            top = (new_h - target_h) // 2
                            img = img.crop((left, top, left + target_w, top + target_h))
                            target_w, target_h = img.size

                    if (target_w, target_h) != img.size:
                        img = img.resize((max(1, target_w), max(1, target_h)), resample=resample)

                if progress_cb:
                    progress_cb(40, "Applying visual enhancements...")

                # Transformations: Rotation and flipping
                rotate = int(settings.get("rotate", 0))
                if rotate in (90, 180, 270):
                    # In Pillow, rotate(90) is counterclockwise, so expand and angle
                    img = img.rotate(360 - rotate, expand=True)

                if settings.get("flip_horizontal", False):
                    img = img.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
                if settings.get("flip_vertical", False):
                    img = img.transpose(Image.Transpose.FLIP_TOP_BOTTOM)

                # Color adjustments
                if settings.get("grayscale", False):
                    img = ImageOps.grayscale(img)

                brightness = float(settings.get("brightness", 1.0))
                if brightness != 1.0 and img.mode in ("RGB", "RGBA", "L"):
                    enhancer = ImageEnhance.Brightness(img)
                    img = enhancer.enhance(brightness)

                contrast = float(settings.get("contrast", 1.0))
                if contrast != 1.0 and img.mode in ("RGB", "RGBA", "L"):
                    enhancer = ImageEnhance.Contrast(img)
                    img = enhancer.enhance(contrast)

                blur = float(settings.get("blur", 0.0))
                if blur > 0:
                    img = img.filter(ImageFilter.GaussianBlur(radius=blur))

                sharpen = float(settings.get("sharpen", 0.0))
                if sharpen > 0:
                    img = img.filter(ImageFilter.UnsharpMask(radius=2, percent=int(sharpen * 50)))

                if progress_cb:
                    progress_cb(70, f"Encoding output format ({fmt.upper()})...")

                # Transparency handling
                flatten_transparency = settings.get("flatten_transparency", False)
                bg_hex = settings.get("background_color", "#FFFFFF").lstrip("#")
                try:
                    bg_rgb = tuple(int(bg_hex[i:i+2], 16) for i in (0, 2, 4))
                except Exception:
                    bg_rgb = (255, 255, 255)

                if fmt in ("jpg", "bmp") or flatten_transparency:
                    if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
                        alpha_img = img.convert("RGBA")
                        bg_img = Image.new("RGB", alpha_img.size, bg_rgb)
                        bg_img.paste(alpha_img, mask=alpha_img.split()[3])
                        img = bg_img
                    elif img.mode != "RGB":
                        img = img.convert("RGB")

                # Output preparation
                target_path.parent.mkdir(parents=True, exist_ok=True)
                save_kwargs = {}

                quality = int(settings.get("quality", 85))
                optimize = bool(settings.get("optimize", True))

                if fmt == "jpg":
                    save_kwargs["quality"] = max(1, min(100, quality))
                    save_kwargs["optimize"] = optimize
                    progressive = settings.get("progressive", False)
                    if progressive:
                        save_kwargs["progressive"] = True
                    pil_fmt = "JPEG"
                elif fmt == "png":
                    compress_level = int(settings.get("png_compression", 6))
                    save_kwargs["compress_level"] = max(0, min(9, compress_level))
                    save_kwargs["optimize"] = optimize
                    pil_fmt = "PNG"
                elif fmt == "webp":
                    lossless = bool(settings.get("lossless", False))
                    save_kwargs["lossless"] = lossless
                    if not lossless:
                        save_kwargs["quality"] = max(1, min(100, quality))
                    save_kwargs["method"] = int(settings.get("effort", 4))
                    pil_fmt = "WEBP"
                elif fmt == "gif":
                    pil_fmt = "GIF"
                elif fmt == "bmp":
                    pil_fmt = "BMP"
                elif fmt == "tiff":
                    pil_fmt = "TIFF"
                elif fmt == "ico":
                    pil_fmt = "ICO"
                    # ICO requires specific size constraints
                    if img.size[0] > 256 or img.size[1] > 256:
                        img = img.resize((256, 256), resample=Image.Resampling.LANCZOS)
                else:
                    pil_fmt = fmt.upper()

                # Handle metadata stripping
                if not settings.get("strip_metadata", False):
                    # Preserve exif if present
                    if "exif" in img.info:
                        save_kwargs["exif"] = img.info["exif"]

                img.save(target_path, format=pil_fmt, **save_kwargs)

            if progress_cb:
                progress_cb(100, "Image conversion completed.")

            return target_path

        except Exception as e:
            raise ConversionFailedError(f"Pillow conversion failed: {str(e)}")
