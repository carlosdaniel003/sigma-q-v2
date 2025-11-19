# app/core/classificacao_producao.py
# --------------------------------------
# Inteligência oficial do SIGMA-Q para validar a base de PRODUÇÃO
# Usa: base_de_dados_prod.xlsx + catalogo_modelos.xlsx
# --------------------------------------

import pandas as pd
from pathlib import Path

# Caminhos oficiais
ROOT = Path.cwd()
PATH_RAW = ROOT / "data" / "raw"

# ------------------------------------------------------------
# [BLOCK 1] - CARREGAMENTO DAS BASES OFICIAIS
# ------------------------------------------------------------
def carregar_base_producao() -> pd.DataFrame:
    path = PATH_RAW / "base_de_dados_prod.xlsx"
    df = pd.read_excel(path)

    df.columns = df.columns.str.upper()

    # Padronizar datas e pega colunas essenciais
    if "DATA" in df.columns:
        df["DATA"] = pd.to_datetime(df["DATA"], dayfirst=True, errors="coerce")

    if "MODELO" not in df.columns:
        raise ValueError("A base de PRODUÇÃO precisa conter a coluna MODELO.")

    df["MODELO"] = df["MODELO"].astype(str).str.strip().str.upper()

    return df


def carregar_catalogo_modelos() -> pd.DataFrame:
    path = PATH_RAW / "catalogo_modelos.xlsx"
    df = pd.read_excel(path)

    df.columns = df.columns.str.upper()

    obrigatorias = ["MODELOS DEFEITOS", "SE TRATA DE", "CORRESPONDE A", "MODELOS PRODUCAO"]
    for col in obrigatorias:
        if col not in df.columns:
            raise ValueError(f"A coluna obrigatória '{col}' não existe no catálogo.")

    # Normalização simples interna
    df["MODELOS DEFEITOS"] = df["MODELOS DEFEITOS"].astype(str).str.upper().str.strip()
    df["CORRESPONDE A"] = df["CORRESPONDE A"].astype(str).str.upper().str.strip()
    df["MODELOS PRODUCAO"] = df["MODELOS PRODUCAO"].astype(str).str.upper().str.strip()

    return df

# ------------------------------------------------------------
# [BLOCK 2] - LÓGICA DE VALIDAÇÃO (IA DE PRODUÇÃO)
# ------------------------------------------------------------
def validar_modelos_producao(df_prod: pd.DataFrame, df_cat: pd.DataFrame):
    """
    - Verifica se MODELO da produção está mapeado no catálogo.
    - Gera KPI.
    - Gera divergências.
    """

    modelos_prod = set(df_prod["MODELO"].unique())
    modelos_catalogo = set(df_cat["MODELOS PRODUCAO"].unique())

    # Modelos da produção que foram compreendidos pela IA
    modelos_validos = modelos_prod.intersection(modelos_catalogo)

    # Divergências reais
    divergencias = modelos_prod - modelos_catalogo

    # KPI
    total = len(modelos_prod)
    entendidos = len(modelos_validos)

    kpi = (entendidos / total * 100) if total > 0 else 100

    return {
        "kpi": kpi,
        "total_modelos": total,
        "entendidos": entendidos,
        "divergentes": sorted(list(divergencias)),
        "modelos_validos": sorted(list(modelos_validos)),
    }


def modelos_sem_defeitos(df_prod: pd.DataFrame, df_cat: pd.DataFrame):
    """
    Retorna os MODELOS PRODUCAO que NÃO aparecem em nenhum defeito.
    (Não é erro — é apenas informação).
    """

    modelos_prod = set(df_prod["MODELO"].unique())
    modelos_catalogo = set(df_cat["MODELOS PRODUCAO"].unique())

    # Somente os modelos acabados, ignorando semi-acabados
    modelos_finais = {m for m in modelos_prod if m in modelos_catalogo}

    # Modelos que possuem defeitos na coluna "MODELOS DEFEITOS"
    modelos_com_defeito = set(df_cat["CORRESPONDE A"].unique())

    # Quem está na produção mas não aparece em nenhum defeito
    sem_defeito = modelos_finais - modelos_com_defeito

    return sorted(list(sem_defeito))


def modelos_defeito_sem_producao(df_prod: pd.DataFrame, df_cat: pd.DataFrame):
    """
    Produtos acabados que aparecem na coluna CORRESPONDE A
    mas não existem na planilha de produção.

    Estes são os “não contabilizados”.
    """

    modelos_prod = set(df_prod["MODELO"].unique())
    modelos_correspondentes = set(df_cat["CORRESPONDE A"].unique())

    nao_contabilizados = modelos_correspondentes - modelos_prod

    return sorted(list(nao_contabilizados))