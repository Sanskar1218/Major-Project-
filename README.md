---
title: IVF Embryo Success Predictor
emoji: 🔬
colorFrom: blue
colorTo: teal
sdk: gradio
app_file: app.py
pinned: false
---

# IVF Embryo Implantation Success Predictor

A machine-learning web app that predicts the likelihood of clinical pregnancy from IVF blastocyst images and/or clinical laboratory data.

## Features

- **36 clinical inputs** organised into 6 sections (all optional)
- **Blastocyst image upload** (JPG / PNG)
- **Adaptive reliability** — High / Medium / Low depending on how much data is provided
- Quick **preset buttons** to load example patient data

## Model Architecture

| Component | Details |
|---|---|
| Image models | 5-fold ConvNeXt-Tiny + 5-fold EfficientNet-B3 ensemble |
| Clinical models | 5-fold XGBoost + 5-fold LightGBM ensemble |
| Meta-learner | Logistic Regression stacker |
| Decision threshold | ≈ 38.4% |
| Full-fusion AUC | 0.875 |

## Usage

Fill in any combination of clinical fields and/or upload an embryo image, then click **Predict**.  
Leave sections blank — the model still runs and shows the appropriate reliability level.

> ⚠️ For research use only. Not a substitute for clinical medical advice.
