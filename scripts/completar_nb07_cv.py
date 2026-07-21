"""
Script para completar la cross-validation 5-fold del notebook 07
Sin modificar el notebook original
"""
import warnings
warnings.filterwarnings("ignore")

import os, sys, json, pickle
from pathlib import Path
from datetime import datetime

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import roc_auc_score, f1_score, recall_score, precision_score

# Configuración de rutas
ROOT = Path.cwd()
DATA_PROC = ROOT / "data" / "processed"
DATA_PATH = DATA_PROC / "dataset_maestro.csv"
OUT_DIR = ROOT / "outputs" / "models" / "xgboost_avanzado"

print("=== Completando Cross-Validation 5-fold - Notebook 07 ===")
print(f"Ruta datos: {DATA_PATH}")
print(f"Ruta salida: {OUT_DIR}")

# Cargar datos
df = pd.read_csv(DATA_PATH, low_memory=False)
df["target"] = (df["resultado"] == "INCONSISTENTE").astype(int)

# Feature engineering (mismo que notebook 07)
df["codigo_cups_facturado"] = df["codigo_cups_facturado"].fillna("").astype(str).str.strip()
df["codigo_cups"] = df["codigo_cups"].fillna("").astype(str).str.strip()
df["diferencia_cantidad"] = (df["cantidad_facturada"] - df["cantidad_realizada"]).fillna(0)
df["ratio_cantidad"] = df["cantidad_facturada"] / (df["cantidad_realizada"] + 1)
df["coincide_codigo_cups"] = (
    (df["codigo_cups_facturado"] != "") & 
    (df["codigo_cups"] != "") & 
    (df["codigo_cups_facturado"] == df["codigo_cups"])
).astype(int)
df["soporte_clinico"] = df["soporte_clinico"].fillna("NO").astype(str).str.upper()
df["tiene_soporte_clinico"] = (df["soporte_clinico"] == "SI").astype(int)
df["dias_diferencia"] = (
    pd.to_datetime(df["fecha_facturacion"], errors="coerce") -
    pd.to_datetime(df["fecha_atencion"], errors="coerce")
).dt.days.fillna(0)

# Features
NUM = ["diferencia_cantidad", "ratio_cantidad", "coincide_codigo_cups",
       "tiene_soporte_clinico", "cantidad_facturada", "cantidad_realizada",
       "valor_unitario", "valor_total", "edad", "dias_diferencia"]
CAT = ["tipo_atencion", "sede", "eps_atencion", "tipo_afiliacion",
       "tipo_item", "grupo_etario", "sexo"]
DIAG = "diagnostico_principal_cie10"

# Verificar columnas
NUM_OK = [c for c in NUM if c in df.columns]
CAT_OK = [c for c in CAT if c in df.columns]

for c in CAT_OK:
    df[c] = df[c].fillna("SIN_DATO").astype(str)
if DIAG in df.columns:
    df[DIAG] = df[DIAG].fillna("SIN_DATO").astype(str)
else:
    df[DIAG] = "SIN_DATO"

for c in NUM_OK:
    df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)

# Cargar artefactos del entrenamiento previo
with open(OUT_DIR / "artefactos_xgboost.pkl", "rb") as f:
    artefactos = pickle.load(f)

with open(OUT_DIR / "modelo_xgboost.pkl", "rb") as f:
    best_model = pickle.load(f)

threshold_optimo = artefactos["threshold"]
scaler = artefactos["scaler"]
label_encoders = artefactos["label_encoders"]
top_diag = set(artefactos["top_diag"])
FEATURES = artefactos["feature_names"]

# Preparar datos
X_all = df[NUM_OK + CAT_OK + [DIAG]].copy()
y_all = df["target"].values

# Encoding
X_all["diag_encoded"] = X_all[DIAG].apply(lambda x: x if x in top_diag else "OTRO")
X_all = X_all.drop(columns=[DIAG])

ALL_CAT = CAT_OK + ["diag_encoded"]
for col in ALL_CAT:
    le = label_encoders[col]
    X_all[col] = X_all[col].apply(lambda x: x if x in le.classes_ else "SIN_DATO")
    X_all[col] = le.transform(X_all[col])

# Scaling
X_all[NUM_OK] = scaler.transform(X_all[NUM_OK])

# Cross-validation 5-fold (solo sobre train)
from sklearn.model_selection import train_test_split
X_train_full, X_test, y_train_full, y_test = train_test_split(
    X_all, y_all, test_size=0.3, stratify=y_all, random_state=42
)

print("\nEjecutando Cross-Validation 5-fold...")
cv_s = {"auc": [], "f1": [], "recall": [], "precision": []}
# Usar los mismos hiperparámetros que el GridSearchCV encontró
grid_params = {
    'learning_rate': 0.1,
    'max_depth': 8,
    'n_estimators': 200,
    'scale_pos_weight': 3.8193832599118944,
    'objective': 'binary:logistic',
    'eval_metric': 'auc'
}
for ti, vi in StratifiedKFold(5, shuffle=True, random_state=42).split(X_train_full, y_train_full):
    m = xgb.XGBClassifier(**grid_params, random_state=42, verbosity=0)
    m.fit(X_train_full.iloc[ti], y_train_full[ti])
    p = m.predict_proba(X_train_full.iloc[vi])[:, 1]
    d = (p >= threshold_optimo).astype(int)
    cv_s["auc"].append(roc_auc_score(y_train_full[vi], p))
    cv_s["f1"].append(f1_score(y_train_full[vi], d, zero_division=0))
    cv_s["recall"].append(recall_score(y_train_full[vi], d, zero_division=0))
    cv_s["precision"].append(precision_score(y_train_full[vi], d, zero_division=0))

print("\n=== Resultados Cross-Validation 5-fold ===")
for k in cv_s:
    print(f"  {k}: mean={np.mean(cv_s[k]):.4f} ± std={np.std(cv_s[k]):.4f}")

# Guardar resultados CV
cv_results = {
    "cv_5fold": {k: {"mean": float(np.mean(v)), "std": float(np.std(v))} for k, v in cv_s.items()},
    "threshold_usado": float(threshold_optimo)
}

with open(OUT_DIR / "cv_results.json", "w", encoding="utf-8") as f:
    json.dump(cv_results, f, indent=2)

print(f"\nResultados CV guardados en: {OUT_DIR / 'cv_results.json'}")
print("=== Completado ===")
