# ============================================================
# app/core/analytics.py
# Camada central de cálculos analíticos reutilizáveis
# ============================================================

import pandas as pd
import numpy as np


# ============================================================
# 1) KPI — acurácia da IA (lexicon vs real)
# ============================================================

def compute_kpi_and_divergences(df):
    """
    Retorna:
    - kpi_acuracia (0 a 1)
    - df_divergencias (ORDEM, DESC_FALHA, TEXTO_NORMALIZADO, COD_FALHA, CODIGO_IA)
    """
    df_ok = df[df["COD_FALHA"] == df["CODIGO_IA"]]
    df_bad = df[df["COD_FALHA"] != df["CODIGO_IA"]]

    kpi = len(df_ok) / len(df) if len(df) > 0 else 0

    cols = ["ORDEM", "DESC_FALHA", "TEXTO_NORMALIZADO", "COD_FALHA", "CODIGO_IA"]
    df_bad = df_bad[cols]

    return kpi, df_bad



# ============================================================
# 2) Top categorias com mais incidência
# ============================================================

def top_categories(df, top_n=10):
    if "CATEGORIA" not in df.columns:
        return pd.DataFrame({"CATEGORIA": [], "COUNT": []})

    return (
        df.groupby("CATEGORIA")
          .size()
          .reset_index(name="COUNT")
          .sort_values("COUNT", ascending=False)
          .head(top_n)
    )


# ============================================================
# 3) Top modelos com mais falhas
# ============================================================

def top_models(df, top_n=10):
    if "MODELO_ID" not in df.columns:
        return pd.DataFrame({"MODELO_ID": [], "COUNT": []})

    return (
        df.groupby("MODELO_ID")
          .size()
          .reset_index(name="COUNT")
          .sort_values("COUNT", ascending=False)
          .head(top_n)
    )


# ============================================================
# 4) Tabela de falhas por modelo (para heatmap)
# ============================================================

def failures_by_model_and_month(df):
    """
    Retorna uma tabela pivot:
    INDEX = MODELO_ID
    COLUNAS = MES_CORR
    VALOR = quantidade de falhas
    """

    if not {"MODELO_ID", "MES_CORR"}.issubset(df.columns):
        return pd.DataFrame()

    pivot = (
        df.pivot_table(
            index="MODELO_ID",
            columns="MES_CORR",
            values="COD_FALHA",
            aggfunc="count",
            fill_value=0
        )
    )

    return pivot


# ============================================================
# 5) Detector simples de anomalias (Z-score por falha)
# ============================================================

def detect_anomalies(df, z_threshold=2.5):
    """
    Detecta falhas cujo volume está MUITO acima da média.
    """

    if "COD_FALHA" not in df.columns:
        return pd.DataFrame()

    g = df.groupby("COD_FALHA").size().reset_index(name="COUNT")

    g["Z_SCORE"] = (g["COUNT"] - g["COUNT"].mean()) / g["COUNT"].std(ddof=0)
    anomalies = g[g["Z_SCORE"] >= z_threshold]

    return anomalies


# ============================================================
# 6) Falhas em extinção
# ============================================================

def failures_going_extinct(df, threshold=3):
    """
    Falhas que tiveram pouquíssimas ocorrências recentemente
    (ex.: últimas 8 semanas de dados)
    """

    if "COD_FALHA" not in df.columns:
        return pd.DataFrame()

    g = df.groupby("COD_FALHA").size().reset_index(name="COUNT")
    low = g[g["COUNT"] <= threshold]

    return low


# ============================================================
# 7) Para página 4 — tabela para exibição de divergências
# ============================================================

def divergences_table_for_display(df):
    """
    Deixa apenas as colunas:
    - ORDEM
    - DESC_FALHA
    - TEXTO_NORMALIZADO
    - COD_FALHA (real)
    - CODIGO_IA (IA)
    """
    cols = ["ORDEM", "DESC_FALHA", "TEXTO_NORMALIZADO", "COD_FALHA", "CODIGO_IA"]
    cols = [c for c in cols if c in df.columns]
    return df[cols]
