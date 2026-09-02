#!/usr/bin/env python3
"""
Add photos to the Covenant Treasures gallery.

    1. Put new photos in  raw-photos/   (HEIC straight off a phone is fine)
    2. Run:  python3 add-photos.py
    3. Commit and push.

It converts them, drops them into assets/img/gallery/, and inserts them at the
top of the gallery in index.html for you. Existing photos are left alone.

One-time setup in a fresh Codespace:
    pip install pillow pillow-heif

Naming: the filename becomes the caption, so name files descriptively.
    inter-house-sports-day.heic   ->  "Inter house sports day"
    primary-4-science-class.jpg   ->  "Primary 4 science class"
Captions are read aloud by screen readers and indexed by Google, so they matter.

Options:
    --dry-run    convert and report, but don't touch index.html
"""

import os
import re
import shutil
import sys

try:
    from PIL import Image, ImageOps
except ImportError:
    sys.exit("Pillow is missing.  Run:  pip install pillow pillow-heif")

try:
    import pillow_heif
    pillow_heif.register_heif_opener()
    HEIC = True
except ImportError:
    HEIC = False

SRC = "raw-photos"
OUT = os.path.join("assets", "img", "gallery")
PAGE = "index.html"

MAX_WIDTH = 1400
QUALITY = 78
EXTS = (".heic", ".heif", ".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff")

DRY = "--dry-run" in sys.argv


def caption_from(stem):
    words = re.sub(r"[-_]+", " ", stem).split()
    if not words:
        return "School photo"
    text = " ".join(words)
    return text[0].upper() + text[1:]


def slugify(stem):
    slug = re.sub(r"[^a-z0-9]+", "-", stem.lower()).strip("-")
    return slug or "photo"


def main():
    if not os.path.isdir(SRC):
        os.makedirs(SRC, exist_ok=True)
        sys.exit(f"Created {SRC}/ — put your photos in there and run this again.")

    if not os.path.isfile(PAGE):
        sys.exit(f"Can't find {PAGE}. Run this from the folder that contains it.")

    os.makedirs(OUT, exist_ok=True)
    page = open(PAGE, encoding="utf-8").read()

    files = sorted(f for f in os.listdir(SRC) if f.lower().endswith(EXTS))
    if not files:
        sys.exit(f"No images found in {SRC}/")

    if not HEIC and any(f.lower().endswith((".heic", ".heif")) for f in files):
        print("! pillow-heif is not installed, so HEIC files will be skipped.")
        print("  Run:  pip install pillow-heif\n")

    figures = []
    skipped = []
    total_in = total_out = 0

    for filename in files:
        stem = os.path.splitext(filename)[0]
        slug = slugify(stem)
        out_name = slug + ".webp"
        out_path = os.path.join(OUT, out_name)

        if out_name in page:
            skipped.append(f"{filename} (already in the gallery)")
            continue

        try:
            im = Image.open(os.path.join(SRC, filename))
        except Exception as exc:
            skipped.append(f"{filename} ({exc})")
            continue

        # apply the phone's rotation flag, then drop all metadata including GPS
        im = ImageOps.exif_transpose(im).convert("RGB")

        if im.width > MAX_WIDTH:
            im = im.resize((MAX_WIDTH, round(im.height * MAX_WIDTH / im.width)),
                           Image.LANCZOS)

        im.save(out_path, "WEBP", quality=QUALITY, method=6)

        a = os.path.getsize(os.path.join(SRC, filename))
        b = os.path.getsize(out_path)
        total_in += a
        total_out += b
        print(f"  {filename}  {a//1024}KB -> {out_name}  {b//1024}KB")

        figures.append(
            f'      <figure><img src="assets/img/gallery/{out_name}" '
            f'alt="{caption_from(stem)}" width="{im.width}" height="{im.height}" '
            f'loading="lazy" decoding="async"></figure>'
        )

    for note in skipped:
        print(f"  skipped {note}")

    if not figures:
        sys.exit("\nNothing new to add.")

    print(f"\n{len(figures)} new photo(s): {total_in//1024}KB -> {total_out//1024}KB")

    if DRY:
        print("\n--dry-run, so index.html was not changed. Markup:\n")
        print("\n".join(figures))
        return

    anchor = '<div class="gallery">'
    if anchor not in page:
        sys.exit("Couldn't find the gallery in index.html. Paste these in by hand:\n\n"
                 + "\n".join(figures))

    shutil.copy(PAGE, PAGE + ".bak")
    page = page.replace(anchor, anchor + "\n" + "\n".join(figures), 1)
    open(PAGE, "w", encoding="utf-8").write(page)

    print(f"Added to {PAGE} (previous version saved as {PAGE}.bak).")
    print("Open it in the Codespace preview to check, then commit.")


if __name__ == "__main__":
    main()
