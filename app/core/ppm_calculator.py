# ================================================================
# app/core/ppm_calculator.py
# Módulo oficial de PPM (Parts Per Million) do SIGMA-Q
#
# RELAÇÃO:
#   base_de_dados_defeitos.xlsx   → defeitos por modelo/data
#   base_de_dados_prod.xlsx       → produção diária por modelo
#
# O objetivo é permitir cálculos robustos:
#   - PPM por dia
#   - PPM por mês
#   - PPM por ano
#   - PPM por modelo
#   - PPM por categoria
#
# ESTE MÓDULO NÃO USA PARQUET.
# SOMENTE trabalha com as bases EXCEL oficiais.
# ================================================================

import pandas as pd


# ================================================================
# 1) Carregar bases oficiais
# ================================================================
def carregar_base_producao(path="data/raw/base_de_dados_prod.xlsx"):
    """Carrega base de produção e padroniza colunas."""
    df = pd.read_excel(path)

    # Padronizar nomes
    renomear = {
        "Data": "DATA",
        "Qty_Geral": "QTY_GERAL",
        "Processo": "PROCESSO",
        "Turno": "TURNO",
        "Modelo": "MODELO",
        "Categoria": "CATEGORIA",
    }

    df = df.rename(columns=renomear)

    # Garantir tipos corretos
    df["DATA"] = pd.to_datetime(df["DATA"], format="%d/%m/%Y", dayfirst=True, errors="coerce")
    df["MODELO"] = df["MODELO"].astype(str).str.strip()
    df["CATEGORIA"] = df["CATEGORIA"].astype(str).str.strip()

    return df


def carregar_base_defeitos(path="data/raw/base_de_dados_defeitos.xlsx"):
    """Carrega base de defeitos e padroniza estrutura."""
    df = pd.read_excel(path)

    # Padronização de colunas importantes
    renomear = {
        "DESC. FALHA": "DESC_FALHA",
        "DESC. COMPONENTE": "DESC_COMPONENTE",
        "DESC. MOTIVO": "DESC_MOTIVO",
        "REGISTRADO POR": "REGISTRADO_POR",
    }
    df = df.rename(columns=renomear)

    df["DATA"] = pd.to_datetime(df["DATA"], format="%d/%m/%Y", dayfirst=True, errors="coerce")
    df["MODELO"] = df["DESCRICAO"].astype(str)  # Ex: MICRO-ONDAS MO-01...
    df["CATEGORIA"] = df["CATEGORIA"].astype(str).str.strip()

    return df


# ================================================================
# 2) Preparação e unificação
# ================================================================
def preparar_bases(df_def, df_prod):
    """Padroniza datas, modelos e categorias para permitir merge futuro."""

    df_def = df_def.copy()
    df_prod = df_prod.copy()

    df_def["MODELO"] = df_def["MODELO"].astype(str).str.strip()
    df_prod["MODELO"] = df_prod["MODELO"].astype(str).str.strip()

    df_def["CATEGORIA"] = df_def["CATEGORIA"].astype(str).str.strip()
    df_prod["CATEGORIA"] = df_prod["CATEGORIA"].astype(str).str.strip()

    df_def["DATA"] = pd.to_datetime(df_def["DATA"], errors="coerce")
    df_prod["DATA"] = pd.to_datetime(df_prod["DATA"], errors="coerce")

    return df_def, df_prod


# ================================================================
# 3) Cálculo de PPM em diferentes modos
# ================================================================
def calcular_ppm(df_def, df_prod, modo="mensal"):
    """
    Calcula PPM por:
        - diario
        - mensal
        - anual
        - modelo
        - categoria
    """

    df_def, df_prod = preparar_bases(df_def, df_prod)

    # ----------------------------------------
    # 3.1 — Agrupamento de defeitos
    # ----------------------------------------
    df_def["QTD_DEFEITOS"] = 1

    if modo == "diario":
        group_def = df_def.groupby(["DATA", "MODELO", "CATEGORIA"])["QTD_DEFEITOS"].sum().reset_index()
        group_prod = df_prod.groupby(["DATA", "MODELO", "CATEGORIA"])["QTY_GERAL"].sum().reset_index()

    elif modo == "mensal":
        df_def["ANO"] = df_def["DATA"].dt.year
        df_def["MES"] = df_def["DATA"].dt.month

        df_prod["ANO"] = df_prod["DATA"].dt.year
        df_prod["MES"] = df_prod["DATA"].dt.month

        group_def = df_def.groupby(["ANO", "MES", "MODELO", "CATEGORIA"])["QTD_DEFEITOS"].sum().reset_index()
        group_prod = df_prod.groupby(["ANO", "MES", "MODELO", "CATEGORIA"])["QTY_GERAL"].sum().reset_index()

    elif modo == "anual":
        df_def["ANO"] = df_def["DATA"].dt.year
        df_prod["ANO"] = df_prod["DATA"].dt.year

        group_def = df_def.groupby(["ANO", "MODELO", "CATEGORIA"])["QTD_DEFEITOS"].sum().reset_index()
        group_prod = df_prod.groupby(["ANO", "MODELO", "CATEGORIA"])["QTY_GERAL"].sum().reset_index()

    elif modo == "modelo":
        group_def = df_def.groupby(["MODELO", "CATEGORIA"])["QTD_DEFEITOS"].sum().reset_index()
        group_prod = df_prod.groupby(["MODELO", "CATEGORIA"])["QTY_GERAL"].sum().reset_index()

    elif modo == "categoria":
        group_def = df_def.groupby(["CATEGORIA"])["QTD_DEFEITOS"].sum().reset_index()
        group_prod = df_prod.groupby(["CATEGORIA"])["QTY_GERAL"].sum().reset_index()

    else:
        raise ValueError("Modo inválido. Use: diario | mensal | anual | modelo | categoria")

    # ----------------------------------------
    # 3.2 — Merge das bases agregadas
    # ----------------------------------------
    df = pd.merge(group_def, group_prod, on=[c for c in group_def.columns if c in group_prod.columns], how="left")

    # ----------------------------------------
    # 3.3 — Calcular PPM
    # ----------------------------------------
    df["PPM"] = (df["QTD_DEFEITOS"] / df["QTY_GERAL"]) * 1_000_000

    df["PPM"] = df["PPM"].fillna(0)

    return df


# ================================================================
# 4) Criar tabela detalhada com filtros opcionais
# ================================================================
def gerar_tabela_ppm(df_def, df_prod, modelo=None, categoria=None, modo="mensal"):
    df = calcular_ppm(df_def, df_prod, modo=modo)

    if modelo:
        df = df[df["MODELO"] == modelo]

    if categoria:
        df = df[df["CATEGORIA"] == categoria]

    return df.reset_index(drop=True)
