"""
Script para completar la Fase 2 de fine-tuning del notebook 08 (CNN)
Sin modificar el notebook original
"""
import warnings
warnings.filterwarnings('ignore')
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.utils.class_weight import compute_class_weight
from sklearn.manifold import TSNE
from sklearn.metrics import (accuracy_score, precision_score, recall_score,
                             f1_score, confusion_matrix, classification_report,
                             roc_auc_score, roc_curve, precision_recall_curve)
import tensorflow as tf
from tensorflow.keras import layers, Sequential
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
import tensorflow.keras.backend as K

SEED = 42
np.random.seed(SEED)
tf.random.set_seed(SEED)

print('=== Completando Fase 2 de Fine-tuning - Notebook 08 ===')

# Configuración de rutas
ROOT = Path.cwd()
DATA_PATH = ROOT / "data" / "processed" / "dataset_maestro.csv"
OUTPUT_DIR = ROOT / "outputs" / "models" / "cnn"
TRAIN_DIR = OUTPUT_DIR / '02_ENTRENAMIENTO'
EVAL_DIR = OUTPUT_DIR / '03_EVALUACION'
TRAIN_DIR.mkdir(parents=True, exist_ok=True)
EVAL_DIR.mkdir(parents=True, exist_ok=True)

print(f'Ruta datos: {DATA_PATH}')
print(f'Ruta salida: {OUTPUT_DIR}')

# Carga del dataset
df = pd.read_csv(DATA_PATH, encoding='utf-8')
print('Dataset:', df.shape[0], 'filas x', df.shape[1], 'cols')

# Feature Selection
y = (df['resultado'] == 'INCONSISTENTE').astype(int).values
print('Target: 0=CONSISTENTE (%d), 1=INCONSISTENTE (%d)' % (sum(y==0), sum(y==1)))

num_features = ['edad', 'cantidad_realizada', 'cantidad_facturada',
                'valor_unitario', 'valor_total', 'mes_atencion']
cat_features = ['sexo', 'eps_atencion', 'tipo_afiliacion', 'ciudad',
                'tipo_documento', 'tipo_atencion', 'sede', 'tipo_item',
                'soporte_clinico', 'grupo_etario',
                'diagnostico_principal_cie10', 'medico_tratante',
                'profesional_responsable']

# Verificar columnas
missing = [c for c in num_features + cat_features if c not in df.columns]
if missing:
    print('FALTAN:', missing)
    cat_features = [c for c in cat_features if c in df.columns]
    num_features = [c for c in num_features if c in df.columns]

# Imputacion de nulos
for col in num_features:
    n = df[col].isna().sum()
    if n > 0:
        df[col] = df[col].fillna(0)
for col in cat_features:
    n = df[col].isna().sum()
    if n > 0:
        df[col] = df[col].fillna('SIN_DATO')

# Encoding con limite de cardinalidad
cat_limits = {'eps_atencion': 10, 'ciudad': 10, 'medico_tratante': 25,
              'sede': 10, 'diagnostico_principal_cie10': 25,
              'profesional_responsable': 20}

encoded_dfs = []
for col in cat_features:
    lim = cat_limits.get(col, 15)
    top = set(df[col].value_counts().nlargest(lim).index)
    df[col + '_grp'] = df[col].apply(lambda x: x if x in top else 'OTRO_'+col)
    dums = pd.get_dummies(df[col + '_grp'], prefix=col, drop_first=False)
    encoded_dfs.append(dums)

X_cat = pd.concat(encoded_dfs, axis=1)
X_num = df[num_features].copy().values

# Split estratificado PRIMERO
X_cat_values = X_cat.values.astype(np.float64)
X_raw = np.concatenate([X_num, X_cat_values], axis=1)
n_num = X_num.shape[1]

X_train_raw, X_test_raw, y_train, y_test = train_test_split(
    X_raw, y, test_size=0.3, random_state=SEED, stratify=y)

# Escalado
scaler = StandardScaler()
X_train_num_scaled = scaler.fit_transform(X_train_raw[:, :n_num])
X_test_num_scaled = scaler.transform(X_test_raw[:, :n_num])

X_train = np.concatenate([X_train_num_scaled, X_train_raw[:, n_num:]], axis=1)
X_test = np.concatenate([X_test_num_scaled, X_test_raw[:, n_num:]], axis=1)

print('Feature matrix train:', X_train.shape, '| test:', X_test.shape)

# Class weights
classes = np.array([0, 1])
w = compute_class_weight('balanced', classes=classes, y=y_train)
class_weight = dict(zip(classes, w))

# CONVERSION TABULAR-TO-IMAGE
IMG_SIZE = 32

def build_feature_positions(X_data, grid_size=IMG_SIZE, rs=42):
    nf = X_data.shape[1]
    corr = np.corrcoef(X_data.T)
    dist = 1 - np.abs(corr)
    np.fill_diagonal(dist, 0)
    tsne = TSNE(n_components=2, metric='precomputed', random_state=rs,
                perplexity=min(30, nf-1), init='random', learning_rate='auto')
    pos = tsne.fit_transform(dist)
    pos = (pos - pos.min(axis=0)) / (pos.max(axis=0) - pos.min(axis=0) + 1e-10)
    pos = (pos * (grid_size - 1)).astype(int)
    return pos

def rows_to_images(X_data, positions, grid_size=IMG_SIZE,
                   global_min=None, global_max=None):
    n = X_data.shape[0]
    imgs = np.zeros((n, grid_size, grid_size), dtype=np.float32)
    for fi, (x, y) in enumerate(positions):
        imgs[:, y, x] = X_data[:, fi]
    mn = global_min if global_min is not None else imgs.min()
    mx = global_max if global_max is not None else imgs.max()
    if mx > mn:
        imgs = (imgs - mn) / (mx - mn)
    imgs = np.clip(imgs, 0, 1)
    return np.stack([imgs, imgs, imgs], axis=-1)

print('Construyendo mapa de features...')
feature_positions = build_feature_positions(X_train)

# Stats globales de normalizacion
raw_train = np.zeros((len(X_train), IMG_SIZE, IMG_SIZE), dtype=np.float32)
for fi, (x, y) in enumerate(feature_positions):
    raw_train[:, y, x] = X_train[:, fi]
GLOBAL_MIN, GLOBAL_MAX = raw_train.min(), raw_train.max()

print('Convirtiendo train y test a imagenes...')
X_train_img = rows_to_images(X_train, feature_positions,
                             global_min=GLOBAL_MIN, global_max=GLOBAL_MAX)
X_test_img = rows_to_images(X_test, feature_positions,
                            global_min=GLOBAL_MIN, global_max=GLOBAL_MAX)
print('Train images:', X_train_img.shape)
print('Test images:', X_test_img.shape)

# Focal loss
def focal_loss(gamma=2.0, alpha=0.6):
    def loss_fn(y_true, y_pred):
        y_pred = K.clip(y_pred, K.epsilon(), 1 - K.epsilon())
        pt = tf.where(K.equal(y_true, 1), y_pred, 1 - y_pred)
        alpha_t = tf.where(K.equal(y_true, 1), alpha, 1 - alpha)
        return -K.mean(alpha_t * K.pow(1 - pt, gamma) * K.log(pt))
    return loss_fn

# Cargar modelo base MobileNetV2
base_model = MobileNetV2(weights='imagenet', include_top=False,
                         input_shape=(IMG_SIZE, IMG_SIZE, 3))
base_model.trainable = False

# Reconstruir el modelo
model = Sequential(name='AuditorMedico_CNN')
model.add(layers.Input(shape=(IMG_SIZE, IMG_SIZE, 3)))
model.add(layers.Rescaling(scale=2., offset=-1))
model.add(base_model)
model.add(layers.GlobalAveragePooling2D())
model.add(layers.BatchNormalization())
model.add(layers.Dense(128, activation='relu'))
model.add(layers.Dropout(0.5))
model.add(layers.Dense(64, activation='relu'))
model.add(layers.Dropout(0.3))
model.add(layers.Dense(1, activation='sigmoid'))

model.compile(optimizer=Adam(learning_rate=1e-3),
              loss=focal_loss(gamma=2.0, alpha=0.6),
              metrics=['accuracy',
                       tf.keras.metrics.Precision(name='precision'),
                       tf.keras.metrics.Recall(name='recall')])

print('\n=== FASE 1: ENTRENANDO HEAD (BASE CONGELADA) ===')
early_stop = EarlyStopping(monitor='val_loss', patience=10,
                           restore_best_weights=True, verbose=1)
reduce_lr = ReduceLROnPlateau(monitor='val_loss', factor=0.5,
                              patience=5, min_lr=1e-6, verbose=1)

history_phase1 = model.fit(
    X_train_img, y_train,
    validation_data=(X_test_img, y_test),
    epochs=50, batch_size=32,
    class_weight=class_weight,
    callbacks=[early_stop, reduce_lr],
    verbose=1)

print('\nFase 1 completada')

# Evaluacion Fase 1
y_pred_prob = model.predict(X_test_img, verbose=0).ravel()
y_pred = (y_pred_prob >= 0.5).astype(int)

acc = accuracy_score(y_test, y_pred)
prec = precision_score(y_test, y_pred)
rec = recall_score(y_test, y_pred)
f1 = f1_score(y_test, y_pred)
auc = roc_auc_score(y_test, y_pred_prob)

print('=== FASE 1 ===')
print('Accuracy:  %.4f' % acc)
print('Precision: %.4f' % prec)
print('Recall:    %.4f' % rec)
print('F1-Score:  %.4f' % f1)
print('AUC-ROC:   %.4f' % auc)

# Optimizacion de threshold
def mejor_threshold(y_true, y_prob, recall_minimo=0.6):
    prec, rec, thresh = precision_recall_curve(y_true, y_prob)
    f1s = 2 * prec * rec / (prec + rec + 1e-10)
    validos = rec[:-1] >= recall_minimo
    if not validos.any():
        idx = np.argmax(f1s[:-1])
    else:
        idx = np.where(validos)[0][np.argmax(f1s[:-1][validos])]
    return thresh[idx], prec[idx], rec[idx], f1s[idx]

th, p, r, f1_opt = mejor_threshold(y_test, y_pred_prob, recall_minimo=0.6)
print('\nThreshold optimo Fase 1: %.3f' % th)
print('Precision: %.4f | Recall: %.4f | F1: %.4f' % (p, r, f1_opt))

# =========================================================================
# FASE 2: FINE-TUNING
# =========================================================================
print('\n=== FASE 2: FINE-TUNING ===')
base_model.trainable = True

for layer in base_model.layers[:-15]:
    layer.trainable = False

for layer in base_model.layers[-15:]:
    if isinstance(layer, layers.BatchNormalization):
        layer.trainable = False
    else:
        layer.trainable = True

print('Capas entrenables:', sum(l.trainable for l in base_model.layers))
print('Capas congeladas:', sum(not l.trainable for l in base_model.layers))

model.compile(optimizer=Adam(learning_rate=3e-6),
              loss=focal_loss(gamma=2.0, alpha=0.6),
              metrics=['accuracy',
                       tf.keras.metrics.Precision(name='precision'),
                       tf.keras.metrics.Recall(name='recall'),
                       tf.keras.metrics.AUC(name='auc')])

early_stop_ft = EarlyStopping(monitor='val_auc', mode='max', patience=8,
                              restore_best_weights=True, verbose=1)
reduce_lr_ft = ReduceLROnPlateau(monitor='val_auc', mode='max', factor=0.5,
                                 patience=4, min_lr=1e-7, verbose=1)

history_phase2 = model.fit(
    X_train_img, y_train,
    validation_data=(X_test_img, y_test),
    epochs=30, batch_size=32,
    callbacks=[early_stop_ft, reduce_lr_ft],
    verbose=1)

print('\nFase 2 completada')

# Evaluacion Fase 2
y_pred_prob_ft = model.predict(X_test_img, verbose=0).ravel()
y_pred_ft = (y_pred_prob_ft >= 0.5).astype(int)

acc_ft = accuracy_score(y_test, y_pred_ft)
prec_ft = precision_score(y_test, y_pred_ft)
rec_ft = recall_score(y_test, y_pred_ft)
f1_ft = f1_score(y_test, y_pred_ft)
auc_ft = roc_auc_score(y_test, y_pred_prob_ft)
tn, fp, fn, tp = confusion_matrix(y_test, y_pred_ft).ravel()

print('\n=== FASE 2 (Fine-tuning) ===')
print('Accuracy:  %.4f' % acc_ft)
print('Precision: %.4f' % prec_ft)
print('Recall:    %.4f' % rec_ft)
print('F1-Score:  %.4f' % f1_ft)
print('AUC-ROC:   %.4f' % auc_ft)
print('\nMatriz de Confusion:')
print('               | Pred: CONS  | Pred: INCONS')
print('Actual CONS    | %6d TN | %6d FP' % (tn, fp))
print('Actual INCONS  | %6d FN | %6d TP' % (fn, tp))
print('\nSensitivity (TPR): %.4f' % (tp/(tp+fn+1e-10)))
print('Specificity (TNR): %.4f' % (tn/(tn+fp+1e-10)))

# Threshold optimo Fase 2
th_ft, p_ft, r_ft, f1_opt_ft = mejor_threshold(y_test, y_pred_prob_ft, recall_minimo=0.6)
print('\nThreshold optimo Fase 2: %.3f' % th_ft)
print('Precision: %.4f | Recall: %.4f | F1: %.4f' % (p_ft, r_ft, f1_opt_ft))

# Guardar modelo
model.save(str(OUTPUT_DIR / 'modelo_cnn_fase2.keras'))
print(f'\nModelo guardado en: {OUTPUT_DIR / "modelo_cnn_fase2.keras"}')

# Guardar métricas
metrics_ft = {
    'fase2': {
        'threshold_0.5': {
            'accuracy': float(acc_ft),
            'precision': float(prec_ft),
            'recall': float(rec_ft),
            'f1': float(f1_ft),
            'auc': float(auc_ft),
            'confusion_matrix': {'tn': int(tn), 'fp': int(fp), 'fn': int(fn), 'tp': int(tp)}
        },
        'threshold_optimo': {
            'threshold': float(th_ft),
            'precision': float(p_ft),
            'recall': float(r_ft),
            'f1': float(f1_opt_ft)
        },
        'mejor_val_auc': float(max(history_phase2.history['val_auc'])),
        'epocas_fase2': len(history_phase2.history['loss'])
    }
}

import json
with open(OUTPUT_DIR / 'metrics_fase2.json', 'w', encoding='utf-8') as f:
    json.dump(metrics_ft, f, indent=2)

print(f'Métricas guardadas en: {OUTPUT_DIR / "metrics_fase2.json"}')
print('\n=== Completado ===')
