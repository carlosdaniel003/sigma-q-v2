# pipeline/text_processor.py
# SIGMA-Q V2 — Fase 2 completa (compatível com seu text_vectorizer.py)

import logging
import pandas as pd
import numpy as np
import joblib

from config.config import PATH_DATA_PROCESSED, PATH_SPACY_MODEL
from services.text_cleaner import clean_text
from services.text_normalizer import normalizar_texto
from services.text_vectorizer import embed_batch, gerar_tfidf

logging.basicConfig(level=logging.INFO, format="%(asctime)s — %(levelname)s — %(message)s")
logger = logging.getLogger(__name__)


def run():
    logger.info("[Pipeline] Carregando base unificada...")
    df = pd.read_parquet(PATH_DATA_PROCESSED / "base_final.parquet")

    # ============================================================
    #  TEXT CLEANING
    # ============================================================
    logger.info("[Pipeline] Limpando texto (TEXTO_LIMPO)...")
    df["TEXTO_LIMPO"] = df["DESC_FALHA_CORR"].astype(str).apply(clean_text)

    logger.info("[Pipeline] Normalizando texto (TEXTO_NORMALIZADO)...")
    df["TEXTO_NORMALIZADO"] = df["TEXTO_LIMPO"].apply(normalizar_texto)

    textos = df["TEXTO_NORMALIZADO"].astype(str).tolist()

    # ============================================================
    #  EMBEDDINGS (spaCy)
    # ============================================================
    logger.info("[Pipeline] Gerando embeddings spaCy (pode demorar)...")
    embeddings = embed_batch(textos)
    emb_path = PATH_SPACY_MODEL / "embeddings.npy"
    np.save(emb_path, embeddings)
    logger.info(f"[OK] Embeddings salvos em: {emb_path}")

    # ============================================================
    #  TF-IDF
    # ============================================================
    logger.info("[Pipeline] Gerando matriz TF-IDF...")
    vectorizer, matriz_tfidf = gerar_tfidf(textos)

    tfidf_vec_path = PATH_SPACY_MODEL / "tfidf_vectorizer.pkl"
    tfidf_mat_path = PATH_SPACY_MODEL / "tfidf_matrix.npy"

    joblib.dump(vectorizer, tfidf_vec_path)
    logger.info(f"[OK] TF-IDF vectorizer salvo em: {tfidf_vec_path}")

    np.save(tfidf_mat_path, matriz_tfidf)
    logger.info(f"[OK] TF-IDF matrix salva em: {tfidf_mat_path}")

    # ============================================================
    #  Salvar o resultado em parquet
    # ============================================================
    out_path = PATH_DATA_PROCESSED / "texto_processado.parquet"
    df.to_parquet(out_path, index=False)

    logger.info("✔ Pipeline Fase 2 concluída com sucesso!")
    logger.info(f"✔ Arquivo final salvo em: {out_path}")


if __name__ == "__main__":
    run()
