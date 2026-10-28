import sys, json, re
from pathlib import Path
import pandas as pd, numpy as np
from PIL import Image

sys.path.insert(0, 'outputs/outputs/artifacts')
import inference

predictor = inference.IVFPredictor('outputs/outputs/artifacts', device='cpu')
cfg = predictor.cfg
features = cfg['features']
sections = cfg['sections']

# Read Excel
sheets = pd.read_excel('dataset.xlsx', sheet_name=None)
df = pd.concat(sheets.values(), ignore_index=True)
df.columns = [str(c).strip() for c in df.columns]

# Scan images
image_dir = Path('Data set splitting')
recs = {}
for p in image_dir.rglob('*'):
    if p.suffix.lower() in {'.jpg', '.png'}:
        recs[p.name.lower()] = p
        recs[p.stem.lower()] = p

file_col = 'Embryo_ID'

print('File column:', file_col)
matched = []
for idx, r in df.iterrows():
    fn = str(r[file_col]).strip().replace('\\', '/').split('/')[-1].lower()
    img_path = recs.get(fn) or recs.get(Path(fn).stem)
    if img_path:
        matched.append((idx, img_path))

print('Total matched rows:', len(matched))
ext_matched = [m for m in matched if 'external-validation' in str(m[1]).lower()]
print('External validation matched:', len(ext_matched))

if ext_matched:
    idx, img_path = ext_matched[0]
    row = df.iloc[idx]
    img = Image.open(img_path)
    clin_full = {c: (None if pd.isna(row[c]) else float(row[c])) for c in features}
    clin_part = {c: clin_full[c] for c in sections['female_hormones_age']}
    print('Testing patient with image:', img_path.name)
    for lab, c, im in [
        ('all inputs', clin_full, img),
        ('hormones+age + image', clin_part, img),
        ('image only', None, img),
        ('hormones+age only', clin_part, None)
    ]:
        res = predictor.predict(c, im)
        print(f"  {lab:22s} -> {res['probability']:.1%}  [{res['prediction']}]  reliability: {res['reliability']}")

    # Save preset data to presets.json
    # Also find a pregnant case to save as positive preset
    preg_matched = [m for m in ext_matched if 'pregnant' in str(m[1]).lower() and 'non-pregnant' not in str(m[1]).lower()]
    print('Pregnant test cases:', len(preg_matched))
    pos_data = None
    if preg_matched:
        p_idx, p_img_path = preg_matched[0]
        p_row = df.iloc[p_idx]
        p_clin = {c: (None if pd.isna(p_row[c]) else float(p_row[c])) for c in features}
        p_img = Image.open(p_img_path)
        p_res = predictor.predict(p_clin, p_img)
        print(f"Pregnant test case ({p_img_path.name}): {p_res['probability']:.1%}  [{p_res['prediction']}]  reliability: {p_res['reliability']}")
        pos_data = {
            'clinical': p_clin,
            'image_sample': 'sample_2',
            'expected_probability': round(p_res['probability'], 4),
            'prediction': p_res['prediction'],
            'reliability': p_res['reliability']
        }

    presets = {
        'all': {
            'clinical': clin_full,
            'image_sample': 'sample_0',
            'label': 'All 36 Inputs + Image'
        },
        'hormones_age_image': {
            'clinical': clin_part,
            'image_sample': 'sample_0',
            'label': 'Hormones+Age + Image'
        },
        'image_only': {
            'clinical': {},
            'image_sample': 'sample_0',
            'label': 'Image Only'
        },
        'hormones_age_only': {
            'clinical': clin_part,
            'image_sample': None,
            'label': 'Hormones+Age Only'
        }
    }
    if pos_data:
        presets['pregnant_sample'] = pos_data

    with open('presets.json', 'w') as f:
        json.dump(presets, f, indent=2)
    print('presets.json saved successfully!')
