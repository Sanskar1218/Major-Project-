---
title: IVF Implantation Success Predictor
emoji: 🔬
colorFrom: blue
colorTo: teal
sdk: docker
app_port: 7860
pinned: false
---

# Intelligent IVF Implantation Success Predictor

A multimodal deep learning and clinical decision support system for predicting embryo implantation and clinical pregnancy success during in-vitro fertilization (IVF).

## 🚀 Overview

The system combines **36 clinical and laboratory features** across 6 clinical panels with deep convolutional neural network embeddings of **blastocyst microphotographs** using a calibrated multimodal fusion architecture.

### Model Architecture
- **Clinical Branch**: Optuna-tuned ensemble of **XGBoost** and **LightGBM** models trained with section dropout to allow flexible partial or missing inputs.
- **Vision Branch**: 5-fold ensemble of **ConvNeXt-Tiny** and **EfficientNet-B3** backbones with Test-Time Augmentation (TTA).
- **Multimodal Fusion**: Calibrated logistic regression meta-classifier with missing-modality compensation.

### Benchmark Performance Across Scenarios
| Scenario | AUC (95% CI) | Accuracy | Sensitivity | Specificity | F1 Score |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **All clinical + image (full fusion)** | **0.875** (0.839–0.906) | 77.6% | 73.5% | 79.5% | 0.677 |
| **Female hormones + blood + image** | **0.796** (0.751–0.838) | 71.0% | 60.0% | 76.1% | 0.569 |
| **Male data + image** | **0.735** (0.691–0.780) | 65.8% | 67.7% | 65.0% | 0.559 |
| **Female hormones + age + image** | **0.707** (0.658–0.753) | 67.3% | 57.4% | 71.9% | 0.528 |
| **Female hormones + age only** | **0.703** (0.654–0.748) | 65.6% | 55.5% | 70.4% | 0.507 |
| **All clinical only** | **0.875** (0.838–0.906) | 77.6% | 72.9% | 79.8% | 0.675 |
| **Image only** | **0.540** (0.486–0.597) | 43.8% | 74.2% | 29.6% | 0.457 |

---

## 🛠️ Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/Sanskar1218/<repo-name>.git
cd <repo-name>
```

### 2. Create Virtual Environment & Install Dependencies
```bash
python -m venv venv
.\venv\Scripts\activate   # Windows (or: source venv/bin/activate on Linux/Mac)
pip install -r requirements.txt
```

### 3. Run the Web Application
```bash
python app.py
```
Open **http://127.0.0.1:5000** in your browser. (On Windows, you can also double-click `run.bat`).

---

## 📋 Input Groups
The web application organizes the 36 clinical parameters into 6 collapsible sections:
1. **Female Hormones & Age** (6 inputs)
2. **Female Blood & General Tests** (10 inputs)
3. **Male Semen Analysis** (6 inputs)
4. **Male Blood Tests** (6 inputs)
5. **Cycle Details** (3 inputs)
6. **Post-Processed Semen** (5 inputs)
Plus an optional **Blastocyst Microphotograph Upload**.

---

## 📄 License
This project is for research and educational purposes.

