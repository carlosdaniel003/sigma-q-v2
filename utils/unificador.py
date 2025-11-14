# utils/unificador.py
"""
Unificador SIGMA-Q v2 (corrigido)
- garante unicidade nas chaves de produção agregada
- remove duplicatas no arquivo de correções antes de aplicar
- geração segura do arquivo de correções (não sobrescreve se já existir)
- mantém regras do projeto (pequenas funções, docstrings em PT-BR)
"""

from pathlib import Path
import pandas as pd
import re
from typing import Optional, List

from config.config import FILE_PRODUCAO, FILE_DEFEITOS, BASE_UNIFICADA, BASE_DIR

# Base do projeto
BASE_DIR = Path(__file__).resolve().parents[1]
CORRECOES_FILE = BASE_DIR / "data" / "processed" / "correcoes_manuais.xlsx"

# -----------------------
# Leitura
# -----------------------
def ler_planilha_producao(path: Path, sheet_name: str = "Plan1") -> pd.DataFrame:
    """Lê a aba principal da planilha de produção."""
    return pd.read_excel(path, sheet_name=sheet_name, engine="openpyxl")


def ler_planilha_defeitos(path: Path) -> pd.DataFrame:
    """Lê a planilha de defeitos (única aba)."""
    return pd.read_excel(path)


# -----------------------
# Normalizações
# -----------------------
def normalizar_colunas(df: pd.DataFrame) -> pd.DataFrame:
    """Padroniza colunas (Caixa alta, sem acentos, underscores)."""
    cols = (
        df.columns.astype(str)
        .str.normalize("NFKD")
        .str.encode("ascii", errors="ignore")
        .str.decode("utf-8")
        .str.upper()
        .str.replace(r"[^\w\s]", " ", regex=True)
        .str.replace(r"\s+", "_", regex=True)
        .str.strip()
    )
    df.columns = cols
    return df


def normalizar_texto(s: Optional[str]) -> str:
    if pd.isna(s):
        return ""
    t = str(s).upper()
    t = t.replace("–", "-").replace("—", "-")
    t = re.sub(r"[^A-Z0-9\-\s/]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


# -----------------------
# Extração MODELO_ID (heurísticas)
# -----------------------
MANUAL_MAP = {
    "ALTO FALANTE 10POL TW": "AWS-T2W-02",
    "CAIXA AMPLIFICADA": "CM-250",
    "FORNO": "MO-01-21-E",
}

KEYWORD_MAP = {
    "BOOMBOX": ["AWS-BBS-01-B", "AWS-BBS-01-LBL"],
    "TV 32":   ["AWS-TV-32-BL-02-A"],
    "TV 50":   ["AWS-TV-50-BL-02-A"],
    "MICRO":   ["MO-01-21-E"],
    "MO-01":   ["MO-01-21-E"],
    "EVAPORADOR": ["AWS-EV-18F", "AWS-EV-18QF"],
    "CONDENSADOR": ["AWS-C-18F", "AWS-C-18QF"],
}

REGEX_PATTERNS = [
    r"(AWS-[A-Z0-9\-]+)",
    r"(MO-[A-Z0-9\-]+)",
    r"(CM-[A-Z0-9\-]+)",
    r"([A-Z]{2,5}-[A-Z0-9]{2,10}-?[A-Z0-9]{0,4})",
]


def extrair_por_regex(s: str) -> Optional[str]:
    for p in REGEX_PATTERNS:
        m = re.search(p, s)
        if m:
            return m.group(1)
    return None


def token_overlap(a: str, b: str) -> int:
    t1 = set(re.split(r"[\s\-/]+", a))
    t2 = set(re.split(r"[\s\-/]+", b))
    return len(t1 & t2)


def escolher_por_similaridade(texto: str, candidatos: List[str]) -> Optional[str]:
    melhor, melhor_score = None, -1
    for c in candidatos:
        sc = token_overlap(texto, c)
        if sc > melhor_score:
            melhor, melhor_score = c, sc
    return melhor


def construir_lista_modelos_producao(df_prod: pd.DataFrame) -> List[str]:
    if "MODELO" not in df_prod.columns:
        return []
    ms = df_prod["MODELO"].dropna().astype(str).unique().tolist()
    return [normalizar_texto(m) for m in ms]


def extrair_modelo_id(texto: str, modelos_producao: List[str]) -> Optional[str]:
    s = normalizar_texto(texto)
    if not s:
        return None

    # 1) regex
    r = extrair_por_regex(s)
    if r:
        return r

    # 2) manual exato
    for k, v in MANUAL_MAP.items():
        if k in s:
            return v

    # 3) keywords
    for k, lst in KEYWORD_MAP.items():
        if k in s:
            if len(lst) == 1:
                return lst[0]
            return escolher_por_similaridade(s, lst)

    # 4) similaridade com modelos da produção
    if modelos_producao:
        pick = escolher_por_similaridade(s, modelos_producao)
        if pick:
            r2 = extrair_por_regex(pick)
            return r2 if r2 else pick

    # 5) fallback (maior token)
    toks = re.split(r"[\s/]+", s)
    toks = [t for t in toks if t]
    if not toks:
        return None
    maior = max(toks, key=len)
    return maior


# -----------------------
# Produção mensal — agregação e limpeza
# -----------------------
def preparar_producao_mensal(df_prod: pd.DataFrame, modelos_producao: List[str]) -> pd.DataFrame:
    """Extrai MODELO_ID da produção e soma produção por (ANO, MES, MODELO_ID)."""
    df = df_prod.copy()
    df = normalizar_colunas(df)

    df["DATA"] = pd.to_datetime(df["DATA"], errors="coerce", dayfirst=True)
    df["MODELO_ID"] = df["MODELO"].astype(str).apply(lambda s: extrair_modelo_id(s, modelos_producao))
    df["ANO"] = df["DATA"].dt.year
    df["MES_NUM"] = df["DATA"].dt.month

    # agrega (soma) e garante unicidade da chave
    df_agg = (
        df.groupby(["ANO", "MES_NUM", "MODELO_ID"], dropna=False)["QTY_GERAL"]
        .sum()
        .reset_index()
    )

    df_agg["CHAVE_MES"] = (
        df_agg["ANO"].astype(int).astype(str)
        + "-"
        + df_agg["MES_NUM"].astype(int).astype(str).str.zfill(2)
        + "-"
        + df_agg["MODELO_ID"].fillna("NA").astype(str)
    )

    df_agg = df_agg.rename(columns={"QTY_GERAL": "PROD_QTY_GERAL"})

    # segurança: garantir uma única linha por CHAVE_MES
    df_agg = df_agg.drop_duplicates(subset=["CHAVE_MES"], keep="last").reset_index(drop=True)

    # limpar espaços acidentais na chave
    df_agg["CHAVE_MES"] = df_agg["CHAVE_MES"].astype(str).str.strip()

    return df_agg


# -----------------------
# Preparar defeitos (extrair modelo_id + chave)
# -----------------------
def preparar_defeitos(df_def: pd.DataFrame, modelos_producao: List[str]) -> pd.DataFrame:
    df = df_def.copy()
    df = normalizar_colunas(df)
    df["DATA"] = pd.to_datetime(df["DATA"], errors="coerce", dayfirst=True)

    df["MODELO_ID"] = df["DESCRICAO"].astype(str).apply(lambda s: extrair_modelo_id(s, modelos_producao))
    df["ANO"] = df["DATA"].dt.year
    df["MES_NUM"] = df["DATA"].dt.month

    df["CHAVE_MES"] = (
        df["ANO"].astype(int).astype(str)
        + "-"
        + df["MES_NUM"].astype(int).astype(str).str.zfill(2)
        + "-"
        + df["MODELO_ID"].fillna("NA").astype(str)
    )
    df["CHAVE_MES"] = df["CHAVE_MES"].astype(str).str.strip()
    return df


# -----------------------
# Merge (defeitos <- produção mensal)
# -----------------------
def unir_bases(df_prod_raw: pd.DataFrame, df_def_raw: pd.DataFrame) -> pd.DataFrame:
    # normalizar colunas
    df_prod = normalizar_colunas(df_prod_raw.copy())
    df_def = normalizar_colunas(df_def_raw.copy())

    # datas
    df_prod["DATA"] = pd.to_datetime(df_prod["DATA"], errors="coerce", dayfirst=True)
    df_def["DATA"] = pd.to_datetime(df_def["DATA"], errors="coerce", dayfirst=True)

    # lista de modelos da produção (texto normalizado)
    modelos_producao = construir_lista_modelos_producao(df_prod)

    # preparar produção mensal (agregada e única por CHAVE_MES)
    df_prod_mensal = preparar_producao_mensal(df_prod, modelos_producao)

    # preparar defeitos (com CHAVE_MES)
    df_def_prep = preparar_defeitos(df_def, modelos_producao)

    # garantir unicidade na tabela de produção antes de merge
    df_prod_mensal = df_prod_mensal.drop_duplicates(subset=["CHAVE_MES"], keep="last").reset_index(drop=True)

    # merge left por CHAVE_MES — produção já está agregada (1 linha por CHAVE_MES)
    merged = pd.merge(
        df_def_prep,
        df_prod_mensal,
        on="CHAVE_MES",
        how="left",
        suffixes=("", "_PROD")
    )

    # limpeza final: garantir colunas e tipos
    if "PROD_QTY_GERAL" in merged.columns:
        merged["PROD_QTY_GERAL"] = pd.to_numeric(merged["PROD_QTY_GERAL"], errors="coerce")

    return merged


# -----------------------
# Arquivo de correções (gera apenas se não existir)
# -----------------------
def gerar_arquivo_correcoes(df: pd.DataFrame):
    """
    Cria correcoes_manuais.xlsx apenas se ainda NÃO existir.
    (OPÇÃO X)
    """
    if CORRECOES_FILE.exists():
        return  # não recriar

    df_faltando = df[df["PROD_QTY_GERAL"].isna()].copy()

    if df_faltando.empty:
        df_faltando = df.head(0)

    CORRECOES_FILE.parent.mkdir(parents=True, exist_ok=True)
    df_faltando.to_excel(CORRECOES_FILE, index=False)
    print(f"Arquivo de correções criado em: {CORRECOES_FILE}")

def aplicar_correcoes_manuais(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aplica correções manuais SEMPRE sobrescrevendo (OPÇÃO B).
    O match é feito por DATA + CODIGO + DESCRICAO.
    """
    path_corr = BASE_DIR / "data" / "processed" / "correcoes_manuais.xlsx"

    if not path_corr.exists():
        return df

    df_corr = pd.read_excel(path_corr)

    # Normalizar tipos
    df_corr["DATA"] = pd.to_datetime(df_corr["DATA"], errors="coerce")
    df["DATA"] = pd.to_datetime(df["DATA"], errors="coerce")

    # Chave única para merge
    df["__KEY__"] = df["DATA"].astype(str) + "|" + df["CODIGO"].astype(str) + "|" + df["DESCRICAO"].astype(str)
    df_corr["__KEY__"] = df_corr["DATA"].astype(str) + "|" + df_corr["CODIGO"].astype(str) + "|" + df_corr["DESCRICAO"].astype(str)

    # Merge
    df = df.merge(
        df_corr.drop_duplicates("__KEY__"),
        on="__KEY__",
        how="left",
        suffixes=("", "_CORR")
    )

    # Campos que podem ser sobrescritos
    campos = [
        "MODELO_ID", "ANO", "MES_NUM", "CHAVE_MES",
        "ANO_PROD", "MES_NUM_PROD", "MODELO_ID_PROD",
        "PROD_QTY_GERAL"
    ]

    for c in campos:
        if f"{c}_CORR" in df.columns:
            df[c] = df[f"{c}_CORR"].combine_first(df[c])
            df.drop(columns=[f"{c}_CORR"], inplace=True)

    df.drop(columns=["__KEY__"], inplace=True)

    return df

# -----------------------
# Salvar / Orquestrar
# -----------------------
def salvar_base_unificada(df: pd.DataFrame, path: Path = BASE_UNIFICADA):
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_excel(path, index=False)


def criar_base_unificada(path_prod: Path = FILE_PRODUCAO, path_def: Path = FILE_DEFEITOS) -> pd.DataFrame:
    df_prod = ler_planilha_producao(path_prod)
    df_def = ler_planilha_defeitos(path_def)

    merged = unir_bases(df_prod, df_def)

    # gerar arquivo inicial de correções (se ainda não existir)
    gerar_arquivo_correcoes(merged)

    # aplicar correções preenchidas manualmente
    merged = aplicar_correcoes_manuais(merged)

    salvar_base_unificada(merged)
    return merged   # ← ESTAVA FALTANDO ISSO
