import os
import sys
import json
import io
import time
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory, render_template
from flask_cors import CORS
from PIL import Image

# Setup base directory
BASE_DIR = Path(__file__).resolve().parent

# Locate artifacts directory
ARTIFACT_DIR = None
for cand in [
    BASE_DIR / 'outputs' / 'outputs' / 'artifacts',
    BASE_DIR / 'outputs' / 'artifacts',
    BASE_DIR.parent / 'outputs' / 'outputs' / 'artifacts',
    BASE_DIR.parent / 'outputs' / 'artifacts',
]:
    if cand.exists() and (cand / 'inference.py').exists():
        ARTIFACT_DIR = cand
        break

if not ARTIFACT_DIR:
    raise FileNotFoundError("Could not locate IVF model artifacts directory!")

# Locate figures and metrics
FIGURES_DIR = None
METRICS_PATH = None
for cand_fig in [
    BASE_DIR / 'outputs' / 'outputs' / 'figures',
    BASE_DIR / 'outputs' / 'figures',
]:
    if cand_fig.exists():
        FIGURES_DIR = cand_fig
        break

for cand_met in [
    BASE_DIR / 'outputs' / 'outputs' / 'metrics.json',
    BASE_DIR / 'outputs' / 'metrics.json',
]:
    if cand_met.exists():
        METRICS_PATH = cand_met
        break

# Add artifacts to path and load IVFPredictor
sys.path.insert(0, str(ARTIFACT_DIR))
import inference

print(f"Loading IVF Predictor from {ARTIFACT_DIR} ...")
t0 = time.time()
predictor = inference.IVFPredictor(str(ARTIFACT_DIR), device='cpu')
print(f"IVF Predictor loaded successfully in {time.time() - t0:.2f}s!")

# Load metadata and presets
with open(BASE_DIR / 'features_metadata.json', 'r', encoding='utf-8') as f:
    FEATURES_META = json.load(f)

PRESETS_PATH = BASE_DIR / 'presets.json'
PRESETS_DATA = {}
if PRESETS_PATH.exists():
    with open(PRESETS_PATH, 'r', encoding='utf-8') as f:
        PRESETS_DATA = json.load(f)

METRICS_DATA = {}
if METRICS_PATH and METRICS_PATH.exists():
    with open(METRICS_PATH, 'r', encoding='utf-8') as f:
        METRICS_DATA = json.load(f)

# Initialize Flask App
app = Flask(__name__, template_folder='templates', static_folder='static')
CORS(app)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/features', methods=['GET'])
def get_features():
    return jsonify(FEATURES_META)


@app.route('/api/presets', methods=['GET'])
def get_presets():
    return jsonify(PRESETS_DATA)


@app.route('/api/metrics', methods=['GET'])
def get_metrics():
    return jsonify(METRICS_DATA)


@app.route('/api/figures/<path:filename>', methods=['GET'])
def get_figure(filename):
    if not FIGURES_DIR or not FIGURES_DIR.exists():
        return jsonify({'error': 'Figures directory not found'}), 404
    return send_from_directory(str(FIGURES_DIR), filename)


@app.route('/api/sample_image/<sample_name>', methods=['GET'])
def get_sample_image(sample_name):
    # Strip extension if passed
    stem = Path(sample_name).stem
    fn = f"{stem}.jpg"
    sample_dir = BASE_DIR / 'sample_images'
    target = sample_dir / fn
    if target.exists():
        return send_from_directory(str(sample_dir), fn, mimetype='image/jpeg')
    return jsonify({'error': f'Sample image {sample_name} not found'}), 404


@app.route('/api/predict', methods=['POST'])
def predict():
    try:
        t_start = time.time()
        clinical_data = {}
        image = None

        # Check content type
        if request.content_type and 'multipart/form-data' in request.content_type:
            # Check for clinical_json field
            if 'clinical_json' in request.form:
                clinical_data = json.loads(request.form['clinical_json'])
            else:
                # Individual form fields
                for feat in predictor.cfg['features']:
                    val = request.form.get(feat)
                    if val is not None and val.strip() != '':
                        clinical_data[feat] = val

            # Check for image file
            if 'image' in request.files:
                file_storage = request.files['image']
                if file_storage.filename and file_storage.filename.strip() != '':
                    image_bytes = file_storage.read()
                    image = Image.open(io.BytesIO(image_bytes))

        elif request.is_json:
            json_body = request.get_json() or {}
            clinical_data = json_body.get('clinical', {})
            # Optional base64 image could be handled if present

        # Run prediction through IVFPredictor
        res = predictor.predict(clinical_data, image)
        res['elapsed_seconds'] = round(time.time() - t_start, 3)

        return jsonify(res)

    except ValueError as ve:
        return jsonify({'error': str(ve)}), 400
    except Exception as e:
        return jsonify({'error': f"Prediction error: {str(e)}"}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 7860))
    print(f"Starting IVF Prediction Web Application on http://0.0.0.0:{port}")
    app.run(host='0.0.0.0', port=port, debug=False)

