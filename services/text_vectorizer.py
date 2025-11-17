"""
services/text_vectorizer.py

Responsabilidade:
- Transformar textos limpos / normalizados em vetores
- Suporte a TF-IDF
- Suporte a embeddings spaCy
- Modular, funções pequenas, PT-BR

Este módulo DEVE SER independente de UI.
"""

import spacy
import numpy as np
from typing import List, Optional
from sklearn.feature_extraction.text import TfidfVectorizer


# ============================================================
# 1) Carregamento do modelo spaCy
# ============================================================

_spacy_model = None

def load_spacy_model(model_name: str = "pt_core_news_md"):
    """Carrega o modelo spaCy apenas uma vez (singleton)."""
    global _spacy_model

    if _spacy_model is None:
        print(f"[spaCy] Carregando modelo {model_name}...")
        _spacy_model = spacy.load(model_name)

    return _spacy_model


# ============================================================
# 2) Embeddings (vetores semânticos)
# ============================================================

def embed_text(text: str, model=None) -> np.ndarray:
    """
    Retorna embedding spaCy para um único texto.
    """
    if model is None:
        model = load_spacy_model()

    if not text or text.strip() == "":
        return np.zeros(model.vocab.vectors_length)

    doc = model(text)
    return doc.vector


def embed_batch(texts: List[str], model=None) -> np.ndarray:
    """
    Processa uma lista de textos e retorna matriz (N x D).
    """
    if model is None:
        model = load_spacy_model()

    vectors = []
    for t in texts:
        vectors.append(embed_text(t, model=model))
    return np.vstack(vectors)


# ============================================================
# 3) TF-IDF (estatístico)
# ============================================================

def gerar_tfidf(texts: List[str]) -> tuple[TfidfVectorizer, np.ndarray]:
    """
    Gera matriz TF-IDF para uma lista de textos normalizados.

    Retorna:
    - vetorizador treinado (para transformar novos textos)
    - matriz TF-IDF (numpy)
    """
    vectorizer = TfidfVectorizer(
        lowercase=True,
        ngram_range=(1, 2),   # unigrama + bigrama (melhor para defeitos)
    min_df=1,             # evita ruído raro demais
    )
    X = vectorizer.fit_transform(texts)
    return vectorizer, X.toarray()


def tfidf_transform(vectorizer: TfidfVectorizer, texts: List[str]) -> np.ndarray:
    """Transforma novos textos usando o TF-IDF treinado."""
    return vectorizer.transform(texts).toarray()


# ============================================================
# 4) Empacotamento para DataFrame — pipeline final
# ============================================================

def vetorizar_dataframe(df, col_texto_normalizado: str):
    """
    Adiciona ao DataFrame:
    - 'EMBEDDING' (spaCy)
    - 'TFIDF_VETOR' (lista)
    - 'TFIDF_OBJ'  (objeto vetorizador)

    Retorna:
    df_modificado, vectorizer_tfidf
    """
    textos = df[col_texto_normalizado].astype(str).tolist()

    # Embeddings spaCy
    print("[Vectorizer] Gerando embeddings spaCy...")
    model = load_spacy_model()
    embeddings = embed_batch(textos, model=model)
    df["EMBEDDING"] = list(embeddings)

    # TF-IDF
    print("[Vectorizer] Gerando TF-IDF...")
    vectorizer, X_tfidf = gerar_tfidf(textos)
    df["TFIDF_VETOR"] = list(X_tfidf)

    return df, vectorizer
