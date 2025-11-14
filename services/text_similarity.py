"""
services/text_similarity.py

Responsabilidade:
- Calcular similaridade entre textos já vetorizados
- Suporta TF-IDF e Embeddings (spaCy)
- Base para insights, diagnóstico e recomendações (Fase 3/4)

Funções principais:
- cosine_similarity_matrix
- top_k_similares
- buscar_similares_no_dataframe
"""

import numpy as np
import pandas as pd
from typing import List, Tuple
from sklearn.metrics.pairwise import cosine_similarity


# ============================================================
# 1) Similaridade para vetores (TF-IDF ou Embeddings)
# ============================================================

def cosine_similarity_matrix(X: np.ndarray, Y: np.ndarray) -> np.ndarray:

    """
    Calcula similaridade coseno entre duas matrizes.
    X: (n_samples, n_features)
    Y: (m_samples, n_features)

    Retorno: matriz (n x m)
    """
    return cosine_similarity(X, Y)

# ============================================================
# 1b) Similaridade simples entre dois textos (TF-IDF interno)
# ============================================================

from sklearn.feature_extraction.text import TfidfVectorizer

def similarity(texto1: str, texto2: str) -> float:
    """
    Similaridade coseno direta entre dois textos brutos (TF-IDF).
    Usada para testes rápidos.
    """
    vect = TfidfVectorizer()
    tfidf = vect.fit_transform([texto1, texto2])
    sim = cosine_similarity(tfidf[0], tfidf[1])[0][0]
    return float(sim)

# ============================================================
# 2) Top-K para uma consulta
# ============================================================

def top_k_similares(
    embedding_query: np.ndarray,
    embeddings_base: np.ndarray,
    k: int = 5
) -> List[Tuple[int, float]]:
    """
    Retorna os K vetores mais semelhantes
    embedding_query: vetor (1, n_features)
    embeddings_base: matriz (N, n_features)

    Retorno:
      lista de tuplas (index, similaridade)
    """
    sim = cosine_similarity(embedding_query.reshape(1, -1), embeddings_base)[0]

    # ordena do maior → menor
    idx_sorted = np.argsort(sim)[::-1]

    return [(int(i), float(sim[i])) for i in idx_sorted[:k]]


# ============================================================
# 3) Procurar textos similares dentro do DataFrame
# ============================================================

def buscar_similares_no_dataframe(
    df: pd.DataFrame,
    texto_embedding: np.ndarray,
    coluna_embeddings: str = "EMBEDDING",
    coluna_texto: str = "TEXTO_PROCESSADO",
    k: int = 5
) -> pd.DataFrame:
    """
    Retorna os K defeitos mais semelhantes ao texto fornecido.
    """

    # empilha embeddings
    base = np.vstack(df[coluna_embeddings].values)

    # pega top-k
    topk = top_k_similares(texto_embedding, base, k=k)

    # monta resultado
    resultados = []
    for idx, score in topk:
        row = df.iloc[idx]
        resultados.append({
            "similaridade": round(score, 4),
            "texto_processado": row[coluna_texto],
            "modelo": row.get("MODELO_ID", None),
            "categoria": row.get("CATEGORIA", None),
            "codigo_defeito": row.get("CODIGO", None),
            "linha": int(row.get("LINHA", -1)) if "LINHA" in df.columns else None,
        })

    return pd.DataFrame(resultados)
