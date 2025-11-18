# =====================================================================
#  PPM ENGINE — SIGMA-Q
#  Versão unificada, revisada e 100% compatível com a Página 7.
# =====================================================================

from __future__ import annotations
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, Literal

ROOT = Path.cwd()
PATH_RAW = ROOT / "data" / "raw"

# =====================================================================
# [BLOCK 1] — Utilidades
# =====================================================================

def normalize_model_name(s: str) -> str:
    if s is None:
        return ""
    s = str(s).upper().strip()
    s = " ".join(s.split())
    return s


# =====================================================================
# [BLOCK 2] — Mapeamento oficial de semiacabados → modelos finais
# =====================================================================

MODEL_MAP = {
    "ALTO FALANTE 8\" 3 OHMS CM-250": "CAIXA AMPLIFICADA CM-250 BIVOLT",
    "ALTO FALANTE 10POL TW": "TORRE DE SOM AWS-T2W-02 BIVOLT BLUETOOTH",
    "MICROONDAS MO-01-21-W": "MICRO-ONDAS MO-01-21-W 220V/60HZ",
    "MICRO-ONDAS MO-01-21-E 127V/60HZ": "MICRO-ONDAS MO-01-21-E 220V/60HZ",
}

# Modelos SEM produção neste mês (apenas sinalização)
NON_COUNT_MODELS = {
    "EVAPORADOR AWS-EV-9QF 220V",
    "TORRE DE SOM TM-2200 BIV",
}


# =====================================================================
# [BLOCK 3] — Carregamento das bases
# =====================================================================

def carregar_base_producao(path: Optional[Path] = None) -> pd.DataFrame:
    p = Path(path) if path else PATH_RAW / "base_de_dados_prod.xlsx"
    df = pd.read_excel(p)

    df.columns = [c.upper().strip() for c in df.columns]

    # Procurar coluna de modelo
    modelo_cols = ["DESCRIÇÃO DO MATERIAL", "DESCRICAO DO MATERIAL", "DESCRIÇÃO", "DESCRICAO"]

    col_modelo = None
    for c in df.columns:
        if c.upper() in [x.upper() for x in modelo_cols]:
            col_modelo = c
            break

    if col_modelo is None:
        raise ValueError("Coluna de MODELO não encontrada na base de produção.")

    df["MODELO"] = df[col_modelo].astype(str).apply(normalize_model_name)

    df["DATA"] = pd.to_datetime(df["DATA"], dayfirst=True, errors="coerce")
    df["QTY_GERAL"] = pd.to_numeric(df["QTY_GERAL"], errors="coerce")

    return df


def carregar_base_defeitos(path: Optional[Path] = None) -> pd.DataFrame:
    p = Path(path) if path else PATH_RAW / "base_de_dados_defeitos.xlsx"
    df = pd.read_excel(p)

    df.columns = [c.upper().strip() for c in df.columns]

    if "DESCRICAO" not in df.columns:
        raise ValueError("Base de defeitos precisa ter coluna DESCRICAO.")

    df["MODELO"] = df["DESCRICAO"].astype(str).apply(normalize_model_name)

    df["DATA"] = pd.to_datetime(df["DATA"], dayfirst=True, errors="coerce")

    return df


# =====================================================================
# [BLOCK 4] — Agregações
# =====================================================================

def agregacao_defeitos(df_def: pd.DataFrame) -> pd.DataFrame:
    return df_def.groupby("MODELO", as_index=False).agg(QTD_DEFEITOS=("ORDEM", "count"))


def agregacao_producao(df_prod: pd.DataFrame) -> pd.DataFrame:
    return df_prod.groupby("MODELO", as_index=False).agg(QTY_GERAL=("QTY_GERAL", "sum"))


# =====================================================================
# [BLOCK 5] — Normalização + Mapeamento modelos finais
# =====================================================================

def aplicar_mapeamento_modelos(df_def: pd.DataFrame) -> pd.DataFrame:
    df2 = df_def.copy()
    df2["MODELO"] = df2["MODELO"].apply(lambda m: MODEL_MAP.get(m, m))
    return df2


# =====================================================================
# [BLOCK 6] — Cálculo de PPM
# =====================================================================

def calcular_ppm_por_modelo(df_def: pd.DataFrame, df_prod: pd.DataFrame) -> pd.DataFrame:
    df_def = aplicar_mapeamento_modelos(df_def)

    def_agg = agregacao_defeitos(df_def)
    prod_agg = agregacao_producao(df_prod)

    df = def_agg.merge(prod_agg, on="MODELO", how="left")

    df["QTY_GERAL"] = df["QTY_GERAL"].fillna(0)

    df["PPM"] = np.where(df["QTY_GERAL"] > 0,
                         (df["QTD_DEFEITOS"] / df["QTY_GERAL"]) * 1_000_000,
                         np.nan)

    return df.sort_values("PPM", ascending=False)


# =====================================================================
# [BLOCK 7] — API para Página 7
# =====================================================================

def gerar_tabela_ppm(df_def: pd.DataFrame, df_prod: pd.DataFrame, modelo: Optional[str] = None) -> pd.DataFrame:

    df_ppm = calcular_ppm_por_modelo(df_def, df_prod)

    # aplicar filtro se necessário
    if modelo:
        modelo = modelo.upper().strip()
        df_ppm = df_ppm[df_ppm["MODELO"].str.contains(modelo, case=False, na=False)]

    # adicionar coluna "OBS"
    df_ppm["OBS"] = df_ppm["MODELO"].apply(
        lambda m: "NÃO CONTABILIZADO" if m in NON_COUNT_MODELS else ""
    )

    return df_ppm


# =====================================================================
# [BLOCK 8] — Sanity Check
# =====================================================================

def sanity_check_joinable(df_def: pd.DataFrame, df_prod: pd.DataFrame) -> dict:
    set_def = set(df_def["MODELO"].unique())
    set_prod = set(df_prod["MODELO"].unique())

    return {
        "missing_in_prod": sorted(list(set_def - set_prod)),
        "missing_in_def": sorted(list(set_prod - set_def)),
        "count_def_models": len(set_def),
        "count_prod_models": len(set_prod),
    }


# =====================================================================
# FIM DO ARQUIVO
# =====================================================================
