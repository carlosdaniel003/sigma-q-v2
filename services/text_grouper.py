"""
services/text_grouper.py

Responsabilidade:
- Agrupar textos similares usando DBSCAN ou HDBSCAN
- Baseado nos embeddings gerados na Fase 2
- Retorna labels de cluster
- Salvamento opcional para auditoria

Usado na Fase 2:
( 🔹 Etapa 4: Agrupamento de causas semelhantes )
"""

import numpy as np
import pandas as pd
from typing import Optional
from sklearn.cluster import DBSCAN

try:
    import hdbscan
    _HDBSCAN_AVAILABLE = True
except ImportError:
    _HDBSCAN_AVAILABLE = False


# ============================================================
# 1) Agrupador DBSCAN
# ============================================================

def cluster_dbscan(embeddings: np.ndarray, eps: float = 0.8, min_samples: int = 5):
    """
    Aplica DBSCAN sobre embeddings (spaCy ou TF-IDF).
    Retorna array de labels: [-1, 0, 1, ...]
    """
    print("[Grouper] Executando DBSCAN...")
    model = DBSCAN(eps=eps, min_samples=min_samples, metric="cosine")
    labels = model.fit_predict(embeddings)
    return labels


# ============================================================
# 2) Agrupador HDBSCAN (opcional, recomendado)
# ============================================================

def cluster_hdbscan(embeddings: np.ndarray, min_cluster_size: int = 8):
    """
    HDBSCAN cria clusters de tamanhos diferentes e aceita ruído.
    """
    if not _HDBSCAN_AVAILABLE:
        raise ImportError("HDBSCAN não está instalado. Use pip install hdbscan")

    print("[Grouper] Executando HDBSCAN...")
    model = hdbscan.HDBSCAN(
        min_cluster_size=min_cluster_size,
        metric="euclidean",
        cluster_selection_method="leaf"
    )
    labels = model.fit_predict(embeddings)
    return labels


# ============================================================
# 3) Função de alto nível — decide automaticamente
# ============================================================

def agrupar_textos(embeddings: np.ndarray, metodo: str = "auto"):
    """
    método:
        "auto" → usa HDBSCAN se disponível, senão DBSCAN
        "hdbscan"
        "dbscan"
    Retorna: labels (clusters)
    """
    if metodo == "hdbscan":
        return cluster_hdbscan(embeddings)

    if metodo == "dbscan":
        return cluster_dbscan(embeddings)

    # modo AUTO
    if _HDBSCAN_AVAILABLE:
        return cluster_hdbscan(embeddings)

    return cluster_dbscan(embeddings)


# ============================================================
# 4) Anexar clusters ao DataFrame
# ============================================================

def adicionar_grupo_no_dataframe(df: pd.DataFrame, embeddings_col: str = "EMBEDDING",
                                 metodo: str = "auto"):
    """
    Cria coluna GRUPO_TEXTO contendo o cluster de cada defeito.
    """
    print("[Grouper] Agrupando textos...")

    # converter lista de vetores → matrix numpy
    vecs = np.vstack(df[embeddings_col].values)

    labels = agrupar_textos(vecs, metodo=metodo)

    df["GRUPO_TEXTO"] = labels.astype(int)

    return df
