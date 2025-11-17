# training/train_classifier.py
# SIGMA-Q V2 — Fase 3 (corrigido)

import os
import joblib
import pandas as pd
from datetime import datetime
from sklearn.svm import LinearSVC
from sklearn.model_selection import train_test_split
import logging

from config.config import PATH_DATA_PROCESSED, PATH_MODELS, PATH_SPACY_MODEL
from utils.metrics import compute_metrics
from utils.checksum import generate_sha256

logging.basicConfig(level=logging.INFO, format="%(asctime)s — %(levelname)s — %(message)s")
logger = logging.getLogger(__name__)


def carregar_base():
    path = PATH_DATA_PROCESSED / "texto_processado.parquet"
    df = pd.read_parquet(path)

    # Remover entradas sem texto
    df = df.dropna(subset=["TEXTO_NORMALIZADO"])

    # Remover NaN real
    df = df.dropna(subset=["COD_FALHA_CORR"])

    # Remover string 'nan'
    df = df[df["COD_FALHA_CORR"].astype(str).str.upper() != "NAN"]

    # Filtrar classes com pelo menos 2 ocorrências
    contagem = df["COD_FALHA_CORR"].value_counts()
    classes_validas = contagem[contagem >= 2].index
    df = df[df["COD_FALHA_CORR"].isin(classes_validas)]

    logger.info(f"Base após filtragem: {df.shape[0]} linhas, {len(classes_validas)} classes válidas")
    return df


def carregar_tfidf():
    path_vec = PATH_SPACY_MODEL / "tfidf_vectorizer.pkl"
    vectorizer = joblib.load(path_vec)
    return vectorizer


def preparar_features(df, vectorizer):
    X = vectorizer.transform(df["TEXTO_NORMALIZADO"])
    y = df["COD_FALHA_CORR"].astype(str)
    return X, y


def treinar_baseline(X_train, y_train):
    model = LinearSVC()
    model.fit(X_train, y_train)
    return model


def salvar_modelo(model, vectorizer):
    PATH_MODELS.mkdir(exist_ok=True)

    joblib.dump(model, PATH_MODELS / "classifier_v1.joblib")
    joblib.dump(vectorizer, PATH_MODELS / "tfidf_vectorizer_v1.joblib")

    sha = generate_sha256(PATH_MODELS / "classifier_v1.joblib")
    with open(PATH_MODELS / "classifier_v1.sha256", "w") as f:
        f.write(sha)


def registrar_versao(metrics):
    entry = f"""
## Modelo classifier_v1 — {datetime.now().strftime("%d/%m/%Y %H:%M")}

- Target: COD_FALHA_CORR
- Texto: TEXTO_NORMALIZADO
- F1-Macro: {metrics['f1_macro']:.4f}
- Acurácia: {metrics['accuracy']:.4f}
- Precisão: {metrics['precision_macro']:.4f}
- Recall: {metrics['recall_macro']:.4f}

------------------------------------------
"""
    with open(PATH_MODELS / "VERSIONS.md", "a", encoding="utf-8") as f:
        f.write(entry)


def main():
    logger.info("===== INICIANDO TREINO FASE 3 =====")

    df = carregar_base()
    vectorizer = carregar_tfidf()
    X, y = preparar_features(df, vectorizer)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, stratify=y, random_state=42
    )

    model = treinar_baseline(X_train, y_train)

    y_pred = model.predict(X_test)
    metrics = compute_metrics(y_test, y_pred)
    logger.info(f"F1-Macro: {metrics['f1_macro']:.4f}")

    salvar_modelo(model, vectorizer)
    registrar_versao(metrics)

    logger.info("===== FIM DO TREINO =====")


if __name__ == "__main__":
    main()
