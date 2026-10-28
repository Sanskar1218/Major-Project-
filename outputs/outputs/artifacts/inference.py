
import json, pickle
from pathlib import Path
import numpy as np
import pandas as pd
from PIL import Image

EPS = 1e-4
def logit(p):
    p = np.clip(np.asarray(p, dtype=float), EPS, 1 - EPS)
    return np.log(p / (1 - p))

def sigmoid(z):
    return 1.0 / (1.0 + np.exp(-np.asarray(z, dtype=float)))

def meta_features(lc, li, comp, has_c, has_i):
    lc = np.atleast_1d(np.asarray(lc, dtype=float)); li = np.atleast_1d(np.asarray(li, dtype=float))
    comp = np.broadcast_to(np.asarray(comp, dtype=float), lc.shape)
    hc = np.full(lc.shape, float(has_c)); hi = np.full(lc.shape, float(has_i))
    lc = lc * hc; li = li * hi
    return np.c_[lc, li, lc * comp, hc, hi, comp]

def make_eval_tf(img_size, mean, std):
    import torch
    import torchvision.transforms.v2 as T
    return T.Compose([T.Resize(img_size, antialias=True), T.ToDtype(torch.float32, scale=True), T.Normalize(mean, std)])


class IVFPredictor:
    def __init__(self, art_dir, device=None):
        import torch, timm
        import xgboost as xgb, lightgbm as lgb
        self.torch = torch
        art = Path(art_dir)
        self.cfg = json.load(open(art / 'config.json'))
        self.meta = pickle.load(open(art / 'meta.pkl', 'rb'))
        self.device = device or ('cuda' if torch.cuda.is_available() else 'cpu')
        n = self.cfg['n_folds']
        self.xgb, self.lgb = [], []
        for k in range(n):
            m = xgb.XGBClassifier(); m.load_model(str(art / 'gbm' / f'xgb_fold{k}.json')); self.xgb.append(m)
            self.lgb.append(lgb.Booster(model_file=str(art / 'gbm' / f'lgb_fold{k}.txt')))
        self.cnns = []
        for name in self.cfg['backbones']:
            for k in range(n):
                m = timm.create_model(name, pretrained=False, num_classes=1)
                sd = torch.load(art / 'cnn' / f'{name}_fold{k}.pt', map_location='cpu')
                m.load_state_dict({a: b.float() for a, b in sd.items()})
                self.cnns.append(m.eval().to(self.device))
        self.tf = make_eval_tf(self.cfg['img_size'], self.cfg['mean'], self.cfg['std'])

    def clinical_frame(self, clinical):
        row = {}
        for c in self.cfg['features']:
            v = None if clinical is None else clinical.get(c)
            if v is None or v == '' or (isinstance(v, float) and v != v):
                row[c] = np.nan
            elif c in self.cfg['cat_maps']:
                row[c] = self.cfg['cat_maps'][c].get(str(v), np.nan)
            else:
                try: row[c] = float(v)
                except (TypeError, ValueError): row[c] = np.nan
        return pd.DataFrame([row], columns=self.cfg['features'])

    def clinical_prob(self, X):
        ps = [0.5 * (m.predict_proba(X)[:, 1] + b.predict(X.values)) for m, b in zip(self.xgb, self.lgb)]
        return float(np.mean(ps))

    def image_logit(self, img):
        torch = self.torch
        cs = self.cfg['cache_size']
        im = img.convert('RGB').resize((cs, cs), Image.BICUBIC)
        x = torch.from_numpy(np.asarray(im, dtype=np.uint8).copy()).permute(2, 0, 1)
        x = self.tf(x).unsqueeze(0).to(self.device)
        outs = []
        with torch.no_grad():
            for m in self.cnns:
                for xx in (x, x.flip(-1), x.flip(-2)):
                    outs.append(float(m(xx).float().squeeze()))
        return float(np.mean(outs))

    def predict(self, clinical=None, image=None):
        X = self.clinical_frame(clinical)
        n_given = int(X.notna().sum(axis=1).iloc[0])
        has_c, has_i = n_given > 0, image is not None
        if not (has_c or has_i):
            raise ValueError('Provide at least some clinical values or an embryo image.')
        comp = n_given / len(self.cfg['features'])
        lc = float(logit(self.clinical_prob(X))) if has_c else 0.0
        li = self.image_logit(image) if has_i else 0.0
        z = self.meta.decision_function(meta_features([lc], [li], comp, has_c, has_i))[0]
        p = float(sigmoid(z)); thr = self.cfg['threshold']
        if has_c and has_i and comp >= 0.75: rel = 'High'
        elif (has_c and has_i and comp >= 0.15) or (has_c and comp >= 0.75): rel = 'Medium'
        else: rel = 'Low'
        return {'probability': p, 'threshold': thr,
                'prediction': 'Implantation / pregnancy likely' if p >= thr else 'Implantation / pregnancy unlikely',
                'clinical_score': float(sigmoid(lc)) if has_c else None,
                'image_score': float(sigmoid(li)) if has_i else None,
                'inputs_provided': n_given, 'inputs_total': len(self.cfg['features']),
                'used_image': has_i, 'completeness': comp, 'reliability': rel}
