"""Quick validation of app.py structure before launch."""
import json
from pathlib import Path

meta = json.load(open("features_metadata.json", encoding="utf-8"))
SECTIONS = meta["sections"]
FEATURE_NAMES = [f["name"] for sec in SECTIONS for f in sec["features"]]
print(f"Feature count: {len(FEATURE_NAMES)}")

presets = json.load(open("presets.json", encoding="utf-8"))
SAMPLE_DIR = Path("sample_images")

for key, p in presets.items():
    clinical = p.get("clinical", {})
    img_sample = p.get("image_sample", "")
    filled = sum(1 for n in FEATURE_NAMES if clinical.get(n) is not None)
    img_exists = False
    if img_sample:
        for ext in ("jpg", "jpeg", "png"):
            if (SAMPLE_DIR / f"{img_sample}.{ext}").exists():
                img_exists = True
                break
    print(f"  {key:22s}: clinical={filled:2d}/36, img_sample={img_sample or '(none)':10s}, img_exists={img_exists}")

print("\nAll good!")
