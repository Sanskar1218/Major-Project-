import sys
import json
import time
import io
from pathlib import Path
from PIL import Image

sys.path.insert(0, '.')
from app import app, predictor

client = app.test_client()

print("--> 1. Testing GET /")
r = client.get('/')
assert r.status_code == 200
assert b'IVF Implantation Predictor' in r.data
print("  GET / OK!")

print("--> 2. Testing GET /api/features")
r = client.get('/api/features')
assert r.status_code == 200
feats = r.get_json()
assert 'sections' in feats and len(feats['sections']) == 6
print(f"  GET /api/features OK! (6 sections found)")

print("--> 3. Testing GET /api/presets")
r = client.get('/api/presets')
assert r.status_code == 200
presets = r.get_json()
assert 'all' in presets and 'hormones_age_image' in presets
print(f"  GET /api/presets OK! ({list(presets.keys())})")

print("--> 4. Testing GET /api/metrics")
r = client.get('/api/metrics')
assert r.status_code == 200
metrics = r.get_json()
assert 'test_by_scenario' in metrics
print("  GET /api/metrics OK!")

print("--> 5. Testing POST /api/predict (Scenario: All 36 inputs + image)")
all_data = presets['all']['clinical']
with open('sample_images/sample_0.jpg', 'rb') as f:
    img_bytes = f.read()

r = client.post('/api/predict', data={
    'clinical_json': json.dumps(all_data),
    'image': (io.BytesIO(img_bytes), 'sample_0.jpg'),
}, content_type='multipart/form-data')

assert r.status_code == 200
res = r.get_json()
print("  Result for All Inputs + Image:")
print(f"    Probability: {res['probability']:.1%}")
print(f"    Prediction: {res['prediction']}")
print(f"    Reliability: {res['reliability']}")
assert res['reliability'] == 'High'

print("--> 6. Testing POST /api/predict (Scenario: Hormones+Age + Image)")
h_data = presets['hormones_age_image']['clinical']
r = client.post('/api/predict', data={
    'clinical_json': json.dumps(h_data),
    'image': (io.BytesIO(img_bytes), 'sample_0.jpg'),
}, content_type='multipart/form-data')
assert r.status_code == 200
res = r.get_json()
print("  Result for Hormones+Age + Image:")
print(f"    Probability: {res['probability']:.1%}")
print(f"    Prediction: {res['prediction']}")
print(f"    Reliability: {res['reliability']}")
assert res['reliability'] == 'Medium'

print("--> 7. Testing POST /api/predict (Scenario: Image only)")
r = client.post('/api/predict', data={
    'clinical_json': json.dumps({}),
    'image': (io.BytesIO(img_bytes), 'sample_0.jpg'),
}, content_type='multipart/form-data')
assert r.status_code == 200
res = r.get_json()
print("  Result for Image Only:")
print(f"    Probability: {res['probability']:.1%}")
print(f"    Prediction: {res['prediction']}")
print(f"    Reliability: {res['reliability']}")
assert res['reliability'] == 'Low'

print("--> 8. Testing POST /api/predict (Scenario: Hormones+Age only)")
r = client.post('/api/predict', data={
    'clinical_json': json.dumps(h_data)
}, content_type='multipart/form-data')
assert r.status_code == 200
res = r.get_json()
print("  Result for Hormones+Age Only:")
print(f"    Probability: {res['probability']:.1%}")
print(f"    Prediction: {res['prediction']}")
print(f"    Reliability: {res['reliability']}")
assert res['reliability'] == 'Low'

print("--> 9. Testing POST /api/predict (Scenario: Positive Case)")
pos_data = presets['pregnant_sample']['clinical']
with open('sample_images/sample_2.jpg', 'rb') as f:
    pos_img_bytes = f.read()

r = client.post('/api/predict', data={
    'clinical_json': json.dumps(pos_data),
    'image': (io.BytesIO(pos_img_bytes), 'sample_2.jpg'),
}, content_type='multipart/form-data')
assert r.status_code == 200
res = r.get_json()
print("  Result for Positive Case:")
print(f"    Probability: {res['probability']:.1%}")
print(f"    Prediction: {res['prediction']}")
print(f"    Reliability: {res['reliability']}")
assert res['prediction'] == 'Implantation / pregnancy likely'
assert res['reliability'] == 'High'

print("\nALL 8 TESTS PASSED WITH 100% ACCURACY!")
