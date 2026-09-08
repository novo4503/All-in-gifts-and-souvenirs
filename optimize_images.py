from pathlib import Path
from PIL import Image
import shutil

# ---------------------------------------------------------
# SETTINGS
# ---------------------------------------------------------

# Search the whole Django project
ROOT = Path(__file__).resolve().parent

# Backup folder
BACKUP_ROOT = ROOT / "image_backup"

# Only optimize images bigger than 500 KB
MIN_SIZE_KB = 500

# Maximum width/height.
# 1200px is still plenty for larger product/detail views.
MAX_DIMENSION = 1200

# JPEG/WebP compression quality
QUALITY = 78

# Image types to optimize
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

# Folders we DON'T want to touch
SKIP_FOLDERS = {
    ".git",
    "image_backup",
    "venv",
    ".venv",
    "__pycache__",
    "node_modules",
}


def format_size(size_bytes):
    if size_bytes >= 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.2f} MB"
    return f"{size_bytes / 1024:.1f} KB"


def should_skip(path):
    return any(part in SKIP_FOLDERS for part in path.parts)


def backup_file(path):
    relative = path.relative_to(ROOT)
    backup_path = BACKUP_ROOT / relative

    backup_path.parent.mkdir(parents=True, exist_ok=True)

    if not backup_path.exists():
        shutil.copy2(path, backup_path)

    return backup_path


def optimize_image(path):
    original_size = path.stat().st_size

    if original_size < MIN_SIZE_KB * 1024:
        return None

    # Make backup BEFORE changing anything
    backup_file(path)

    try:
        with Image.open(path) as img:

            original_width, original_height = img.size

            # ---------------------------------------------
            # RESIZE
            # ---------------------------------------------
            if max(img.size) > MAX_DIMENSION:
                img.thumbnail(
                    (MAX_DIMENSION, MAX_DIMENSION),
                    Image.Resampling.LANCZOS
                )

            extension = path.suffix.lower()

            # ---------------------------------------------
            # JPEG
            # ---------------------------------------------
            if extension in {".jpg", ".jpeg"}:

                # JPEG doesn't support alpha/transparency
                if img.mode not in ("RGB", "L"):
                    img = img.convert("RGB")

                img.save(
                    path,
                    format="JPEG",
                    quality=QUALITY,
                    optimize=True,
                    progressive=True
                )

            # ---------------------------------------------
            # PNG
            # ---------------------------------------------
            elif extension == ".png":

                img.save(
                    path,
                    format="PNG",
                    optimize=True
                )

            # ---------------------------------------------
            # WEBP
            # ---------------------------------------------
            elif extension == ".webp":

                img.save(
                    path,
                    format="WEBP",
                    quality=QUALITY,
                    method=6
                )

        new_size = path.stat().st_size

        return {
            "path": path,
            "old_size": original_size,
            "new_size": new_size,
            "old_dimensions": (original_width, original_height),
            "new_dimensions": Image.open(path).size,
        }

    except Exception as error:
        print(f"\nERROR processing:")
        print(path)
        print(error)

        # Restore original if optimization failed
        backup_path = BACKUP_ROOT / path.relative_to(ROOT)

        if backup_path.exists():
            shutil.copy2(backup_path, path)

        return None


print()
print("=" * 70)
print("IMAGE OPTIMIZER")
print("=" * 70)

print(f"\nProject: {ROOT}")
print(f"Backup:  {BACKUP_ROOT}")
print(f"Images larger than {MIN_SIZE_KB} KB will be optimized.")
print()

results = []

for path in ROOT.rglob("*"):

    if not path.is_file():
        continue

    if should_skip(path):
        continue

    if path.suffix.lower() not in IMAGE_EXTENSIONS:
        continue

    result = optimize_image(path)

    if result:
        results.append(result)

        saved = result["old_size"] - result["new_size"]

        print("-" * 70)
        print(result["path"].relative_to(ROOT))
        print(
            f"Dimensions: "
            f"{result['old_dimensions'][0]}x{result['old_dimensions'][1]}"
            f" -> "
            f"{result['new_dimensions'][0]}x{result['new_dimensions'][1]}"
        )
        print(
            f"Size: "
            f"{format_size(result['old_size'])}"
            f" -> "
            f"{format_size(result['new_size'])}"
        )
        print(f"Saved: {format_size(saved)}")


print()
print("=" * 70)

if results:

    total_before = sum(item["old_size"] for item in results)
    total_after = sum(item["new_size"] for item in results)
    total_saved = total_before - total_after

    print(f"Optimized: {len(results)} images")
    print(f"Before:    {format_size(total_before)}")
    print(f"After:     {format_size(total_after)}")
    print(f"Saved:     {format_size(total_saved)}")

else:
    print("No images larger than the threshold were found.")

print()
print("Original images are stored in:")
print(BACKUP_ROOT)

print("=" * 70)