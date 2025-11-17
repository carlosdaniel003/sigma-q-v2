# ---------- BLOCO 2 (training/train_classifier.py) ----------
"""
Script de treino do classificador (scikit-learn).
Regras:
- Se uma classe tiver apenas 1 amostra, removemos essas classes do conjunto de treino
  (pois train_test_split com stratify exige >=2 por classe).
- Treinador gera:
    - models/tfidf_vectorizer_v1.joblib
    - models/classifier_v1.joblib
- Usa LogisticRegression (leve, determinístico)
"""
import logging
from pathlib import Path
from collections import Counter

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import f1_score, accuracy_score

from services.text_normalizer import normalizar_texto

LOG = logging.getLogger("train")
logging.basicConfig(level=logging.INFO)

BASE_DIR = Path(__file__).resolve().parents[1]
MODELS_DIR = BASE_DIR / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)

TFIDF_PATH = MODELS_DIR / "tfidf_vectorizer_v1.joblib"
CLASSIFIER_PATH = MODELS_DIR / "classifier_v1.joblib"


def carregar_base_oficial(path: Path):
    LOG.info(f"Carregando base oficial: {path}")
    df = pd.read_excel(path)
    return df


def preparar_dataset(df: pd.DataFrame, texto_col: str = "DESC_FALHA", label_col: str = "COD_FALHA"):
    # renomeios mínimos (se necessário)
    renomear = {
        "DESC. FALHA": "DESC_FALHA",
        "DESC. COMPONENTE": "DESC_COMPONENTE",
        "DESC. MOTIVO": "DESC_MOTIVO",
        "REGISTRADO POR": "REGISTRADO_POR"
    }
    df = df.rename(columns=renomear)

    # remover linhas sem label
    df = df.dropna(subset=[label_col, texto_col])
    # criar coluna de texto normalizado
    df["TEXTO_NORMALIZADO"] = df[texto_col].astype(str).apply(normalizar_texto)

    # contar classes
    cnt = Counter(df[label_col].astype(str).tolist())

    # filtrar classes com 2+ amostras (necessário para stratify)
    valid_classes = {k for k, v in cnt.items() if v >= 2}
    LOG.info(f"Classes totais antes: {len(cnt)}; classes com >=2 amostras: {len(valid_classes)}")

    df = df[df[label_col].astype(str).isin(valid_classes)].reset_index(drop=True)
    return df


def train_and_persist(path_raw: Path, texto_col: str = "DESC_FALHA", label_col: str = "COD_FALHA"):
    df = carregar_base_oficial(path_raw)
    df = preparar_dataset(df, texto_col=texto_col, label_col=label_col)

    if df.shape[0] == 0:
        LOG.info("[TRAIN] Nenhum dado válido para treinar após filtro de classes.")
        return

    X_text = df["TEXTO_NORMALIZADO"].tolist()
    y = df[label_col].astype(str).tolist()

    # Treino TF-IDF
    vectorizer = TfidfVectorizer(lowercase=True, ngram_range=(1, 2), min_df=1)
    X = vectorizer.fit_transform(X_text)

    # Split (estratificado)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.20, stratify=y, random_state=42)

    # Modelo simples e efetivo
    clf = LogisticRegression(max_iter=2000, class_weight="balanced", solver="lbfgs")
    clf.fit(X_train, y_train)

    # Avaliação
    y_pred = clf.predict(X_test)
    f1 = f1_score(y_test, y_pred, average="macro")
    acc = accuracy_score(y_test, y_pred)

    LOG.info(f"[TRAIN] Treino concluído. F1-macro: {f1:.4f}  Acc: {acc:.4f}")

    # Persistência
    joblib.dump(vectorizer, TFIDF_PATH)
    joblib.dump(clf, CLASSIFIER_PATH)
    LOG.info(f"[TRAIN] Modelos salvos em: {TFIDF_PATH} e {CLASSIFIER_PATH}")

    return {
        "f1_macro": float(f1),
        "accuracy": float(acc),
        "n_samples": len(y)
    }


if __name__ == "__main__":
    RAW = BASE_DIR / "data" / "raw" / "base_de_dados_defeitos.xlsx"
    train_and_persist(RAW)
# ---------- FIM BLOCO 2 ----------
