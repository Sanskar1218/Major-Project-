"""
IVF Embryo Implantation Success Predictor
Gradio app for Hugging Face Spaces (free tier)
"""

import json
import sys
from pathlib import Path

import gradio as gr
from PIL import Image

# ── Model setup ──────────────────────────────────────────────────────────────
ARTIFACTS = Path(__file__).parent / "outputs/outputs/artifacts"
sys.path.insert(0, str(ARTIFACTS))
import inference  # noqa: E402

print("Loading IVF predictor (this takes ~15 s on CPU)…")
predictor = inference.IVFPredictor(str(ARTIFACTS), device="cpu")
print("Predictor ready.")

# ── Metadata ─────────────────────────────────────────────────────────────────
with open(Path(__file__).parent / "features_metadata.json", encoding="utf-8") as f:
    meta = json.load(f)

with open(Path(__file__).parent / "presets.json", encoding="utf-8") as f:
    presets = json.load(f)

SECTIONS = meta["sections"]   # list of section dicts

# Flat ordered list of feature names (36)
FEATURE_NAMES = []
for sec in SECTIONS:
    for feat in sec["features"]:
        FEATURE_NAMES.append(feat["name"])

# Map feature name → metadata dict
FEAT_META = {}
for sec in SECTIONS:
    for feat in sec["features"]:
        FEAT_META[feat["name"]] = feat

SAMPLE_DIR = Path(__file__).parent / "sample_images"

# ── CSS ───────────────────────────────────────────────────────────────────────
CSS = """
/* ── Global ── */
body { font-family: 'Inter', sans-serif; }
.gr-button { border-radius: 8px !important; }

/* ── Header ── */
#header { text-align: center; padding: 24px 0 8px; }
#header h1 { font-size: 2rem; font-weight: 700; margin: 0; }
#header p  { color: #6b7280; margin: 4px 0 0; font-size: 0.95rem; }

/* ── Preset bar ── */
.preset-row { gap: 6px !important; flex-wrap: wrap; justify-content: center; }
.preset-btn { font-size: 0.78rem !important; padding: 4px 10px !important; }

/* ── Result card ── */
#result-card {
    border: 2px solid #e5e7eb;
    border-radius: 12px;
    padding: 20px;
    background: #f9fafb;
    margin-top: 8px;
}
#prob-display {
    font-size: 3rem;
    font-weight: 800;
    text-align: center;
    line-height: 1.1;
}
#verdict-display {
    font-size: 1.2rem;
    font-weight: 600;
    text-align: center;
    margin: 4px 0 8px;
}
#reliability-display {
    text-align: center;
    font-size: 0.85rem;
    font-weight: 500;
    padding: 3px 12px;
    border-radius: 9999px;
    display: inline-block;
}
.reliability-high   { background:#d1fae5; color:#065f46; }
.reliability-medium { background:#fef3c7; color:#92400e; }
.reliability-low    { background:#fee2e2; color:#991b1b; }

/* ── Sub-scores ── */
#subscores { font-size: 0.82rem; color: #6b7280; }
"""

# ── Helper: build result HTML ─────────────────────────────────────────────────
def _result_html(result: dict) -> str:
    prob_pct = result["probability"] * 100
    pred     = result["prediction"]          # "Likely" / "Unlikely"
    rel      = result["reliability"]         # "High" / "Medium" / "Low"
    cs       = result.get("clinical_score")
    img_s    = result.get("image_score")
    comp     = result.get("completeness", 0)

    color = "#16a34a" if pred == "Likely" else "#dc2626"
    rel_class = f"reliability-{rel.lower()}"

    cs_str   = f"{cs*100:.1f}%" if cs is not None else "—"
    imgs_str = f"{img_s*100:.1f}%" if img_s is not None else "—"

    return f"""
<div id="result-card">
  <div id="prob-display" style="color:{color}">{prob_pct:.1f}%</div>
  <div id="verdict-display" style="color:{color}">
    {'✅ Implantation / pregnancy likely' if pred=='Likely' else '❌ Implantation / pregnancy unlikely'}
  </div>
  <div style="text-align:center">
    <span id="reliability-display" class="{rel_class}">
      Reliability: {rel}
    </span>
  </div>
  <hr style="margin:14px 0; border:none; border-top:1px solid #e5e7eb"/>
  <div id="subscores">
    <b>Threshold:</b> {predictor.threshold*100:.1f}% &nbsp;|&nbsp;
    <b>Clinical score:</b> {cs_str} &nbsp;|&nbsp;
    <b>Image score:</b> {imgs_str} &nbsp;|&nbsp;
    <b>Data completeness:</b> {comp*100:.0f}%
  </div>
  <div style="font-size:0.78rem;color:#9ca3af;margin-top:8px">
    ⚠️ For research use only. Not a substitute for medical advice.
  </div>
</div>
"""

_PLACEHOLDER_HTML = """
<div id="result-card" style="text-align:center;color:#9ca3af;padding:40px 20px">
  <div style="font-size:2rem">🔬</div>
  <div style="margin-top:8px">Fill in at least one field and click <b>Predict</b></div>
  <div style="font-size:0.8rem;margin-top:4px">
    You can leave any section blank — reliability adjusts automatically.
  </div>
</div>
"""

# ── Core predict function ─────────────────────────────────────────────────────
def predict_fn(*args):
    """args = 36 feature values (float|None) + 1 PIL Image (or None)"""
    clinical = {}
    for i, name in enumerate(FEATURE_NAMES):
        val = args[i]
        if val is not None and str(val).strip() != "":
            try:
                clinical[name] = float(val)
            except (ValueError, TypeError):
                pass

    image: Image.Image | None = args[36]  # gr.Image returns PIL

    if not clinical and image is None:
        return _PLACEHOLDER_HTML

    result = predictor.predict(clinical, image)
    return _result_html(result)

# ── Build Gradio UI ───────────────────────────────────────────────────────────
with gr.Blocks(title="IVF Success Predictor") as demo:

    # ── Header ──
    gr.HTML("""
    <div id="header">
      <h1>🔬 IVF Embryo Success Predictor</h1>
      <p>Predict clinical pregnancy likelihood from embryo image and/or clinical data</p>
    </div>
    """)

    # ── Preset buttons ──
    gr.Markdown("**Quick presets** — click to auto-fill with example patient data:")
    with gr.Row(elem_classes="preset-row"):
        btn_all   = gr.Button("All inputs",         elem_classes="preset-btn", variant="secondary")
        btn_ha_im = gr.Button("Hormones+Age+Image", elem_classes="preset-btn", variant="secondary")
        btn_im    = gr.Button("Image only",         elem_classes="preset-btn", variant="secondary")
        btn_ha    = gr.Button("Hormones+Age only",  elem_classes="preset-btn", variant="secondary")
        btn_pos   = gr.Button("✅ Positive sample",  elem_classes="preset-btn", variant="secondary")
        btn_clear = gr.Button("🗑 Clear all",        elem_classes="preset-btn", variant="stop")

    # ── Main layout ──
    with gr.Row():
        # ── Left: clinical sections ──
        with gr.Column(scale=3):
            all_inputs = []   # 36 gr.Number components in FEATURE_NAMES order

            for sec in SECTIONS:
                with gr.Accordion(label=f"📋 {sec['title']}  ({len(sec['features'])} fields)",
                                  open=False):
                    gr.Markdown(f"*{sec['description']}*")
                    with gr.Row():
                        for feat in sec["features"]:
                            fm = feat
                            inp = gr.Number(
                                label=f"{fm['label']} ({fm['unit']})",
                                value=None,
                                minimum=fm.get("min"),
                                maximum=fm.get("max"),
                                info=fm.get("tooltip", ""),
                                scale=1,
                            )
                            all_inputs.append(inp)

        # ── Right: image + predict + result ──
        with gr.Column(scale=2):
            img_input = gr.Image(
                label="Blastocyst Image (optional)",
                type="pil",
                height=220,
            )
            predict_btn = gr.Button("🔍 Predict", variant="primary", size="lg")
            result_html = gr.HTML(value=_PLACEHOLDER_HTML)

    # ── Predict wiring ──
    predict_btn.click(
        fn=predict_fn,
        inputs=all_inputs + [img_input],
        outputs=result_html,
    )

    # ── Preset helpers ──
    def _make_preset_vals(key: str):
        """Return list of 36 values + 1 PIL Image (or None) for a preset."""
        p = presets.get(key, {})
        clinical_vals = p.get("clinical", {})
        img_sample    = p.get("image_sample")  # e.g. "sample_0"

        feature_vals = [clinical_vals.get(n) for n in FEATURE_NAMES]

        img = None
        if img_sample:
            # try .jpg then .png
            for ext in ("jpg", "jpeg", "png"):
                full = SAMPLE_DIR / f"{img_sample}.{ext}"
                if full.exists():
                    img = Image.open(full)
                    break
        return feature_vals + [img]

    def _clear_all():
        return [None] * 36 + [None]

    all_outputs = all_inputs + [img_input]

    btn_all.click(  fn=lambda: _make_preset_vals("all"),               outputs=all_outputs)
    btn_ha_im.click(fn=lambda: _make_preset_vals("hormones_age_image"),outputs=all_outputs)
    btn_im.click(   fn=lambda: _make_preset_vals("image_only"),        outputs=all_outputs)
    btn_ha.click(   fn=lambda: _make_preset_vals("hormones_age_only"), outputs=all_outputs)
    btn_pos.click(  fn=lambda: _make_preset_vals("pregnant_sample"),   outputs=all_outputs)
    btn_clear.click(fn=_clear_all,                                     outputs=all_outputs)

    # ── Info footer ──
    gr.Markdown("""
---
**How reliability is determined**

| Reliability | Condition |
|---|---|
| 🟢 High   | All 36 clinical inputs + embryo image provided (completeness ≥ 75%) |
| 🟡 Medium | Hormones+age group + image, or most clinical data provided |
| 🔴 Low    | Image only, or few clinical fields filled |

> Model: 5-fold ensemble of ConvNeXt-Tiny + EfficientNet-B3 (image) and XGBoost + LightGBM (clinical),
> fused by Logistic Regression meta-learner. Threshold ≈ 38.4%.
""")

# ── Launch ───────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import os

    demo.launch(
        css=CSS,
        server_name="0.0.0.0",
        server_port=int(os.environ.get("PORT", 7860)),
        share=False,
    )
