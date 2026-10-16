"""Image optimization for uploaded photos.

Phone cameras produce images far larger than this app ever displays
(e.g. 3000x4000 at 5-10 MB rendered in a ~900 px column), so uploads and
the one-off `optimize_photos` command funnel through `optimize_image_file`:
downscale, apply EXIF orientation, strip metadata, re-encode.
"""
import io

from django.core.files.base import ContentFile
from PIL import Image, ImageOps

# Longest side of stored photos, in pixels. Covers the largest display
# (detail page ~896 px) plus Retina.
MAX_LONGEST_EDGE = 1600
JPEG_QUALITY = 82
# Files at or under this size that also fit MAX_LONGEST_EDGE are left
# untouched, which keeps optimization idempotent.
SMALL_FILE_BYTES = 512 * 1024


def optimize_image_file(file):
    """Return an optimized file-like copy of *file*.

    *file* must be a readable file-like with a ``name`` attribute (e.g. an
    ``UploadedFile`` or ``ContentFile``). If the file already fits the
    constraints it is returned unchanged.
    """
    data = file.read()
    img = Image.open(io.BytesIO(data))
    if max(img.size) <= MAX_LONGEST_EDGE and len(data) <= SMALL_FILE_BYTES:
        file.seek(0)
        return file

    fmt = img.format
    img = ImageOps.exif_transpose(img)
    if max(img.size) > MAX_LONGEST_EDGE:
        img.thumbnail((MAX_LONGEST_EDGE, MAX_LONGEST_EDGE), Image.Resampling.LANCZOS)

    out = io.BytesIO()
    save_kwargs = {'optimize': True}
    if fmt in ('JPEG', 'WEBP'):
        save_kwargs['quality'] = JPEG_QUALITY
    img.save(out, fmt, **save_kwargs)

    return ContentFile(out.getvalue(), name=getattr(file, 'name', 'image.jpg'))
