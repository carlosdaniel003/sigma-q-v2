"""
utils/unificador.py

Responsabilidade:
- Ler as duas bases brutas (produção e defeitos)
- Padronizar nomes de colunas e formatos
- Criar chaves de união (DATA + TURNO + LINHA + MODELO quando aplicável)
- Fazer o merge/união e salvar a base unificada

Seguir guia do projeto: funções pequenas, docstrings em PT-BR, usar config.
"""

from pathlib import Path
import pandas as pd
from typing import Tuple, List
import re

from config.config import FILE_PRODUCAO, FILE_DEFEITOS, BASE_UNIFICADA, DATE_FORMATS


# -----------------------
# I/O
# -----------------------
def ler_planilha_producao(path: Path, sheet_name: str = "Produção_Geral") -> pd.DataFrame:
    """Lê a aba principal da planilha de produção."""
    return pd.read_excel(path, sheet_name=sheet_name, engine="openpyxl")


def ler_planilha_defeitos(path: Path) -> pd.DataFrame:
    """Lê a planilha de defeitos (única aba)."""
    # .xls pode exigir engine xlrd; pandas tenta automaticamente
    return pd.read_excel(path)


# -----------------------
# Padronização de colunas
# -----------------------
def normalizar_colunas(df: pd.DataFrame) -> pd.DataFrame:
    """Padroniza nomes de colunas: maiúsculas, sem acento, underscores."""
    def clean(name: str) -> str:
        if not isinstance(name, str):
            return name
        s = name.strip()
        s = s.upper()
        s = s.replace("Ç", "C").replace("Ã", "A").replace("Á", "A").replace("É", "E").replace("Í", "I").replace("Ó", "O").replace("Ú", "U")
        s = re.sub(r"[^\w\s]", " ", s)  # remove pontuação
        s = re.sub(r"\s+", "_", s)
        return s

    df = df.rename(columns={c: clean(c) for c in df.columns})
    return df


# -----------------------
# Mapeamento / Harmonização de colunas
# -----------------------
def mapear_colunas_producao(df: pd.DataFrame) -> pd.DataFrame:
    """Renomeia colunas da planilha de produção para os padrões do SIGMA-Q."""
    m = {
        "DATA": "DATA",
        "SITE": "SITE",
        "QTY_GERAL": "QUANTIDADE_PRODUZIDA",
        "PROCESSO": "PROCESSO",
        "LINHA": "LINHA_PROD",
        "TURNO": "TURNO_PROD",
        "MODELO": "MODELO",
        "CATEGORIA": "CATEGORIA_PROD",
    }
    # renomeia somente colunas existentes
    cols = {k: v for k, v in m.items() if k in df.columns}
    return df.rename(columns=cols)


def mapear_colunas_defeitos(df: pd.DataFrame) -> pd.DataFrame:
    """Renomeia colunas da planilha de defeitos para os padrões do SIGMA-Q."""
    m = {
        "DATA": "DATA",
        "MES": "MES",
        "SEMANA": "SEMANA",
        "TURNO": "TURNO_DEFEITO",
        "CÓDIGO": "CODIGO_DEFEITO",
        "CODIGO": "CODIGO_DEFEITO",
        "DESCRICAO": "DESCRICAO_ORIGINAL",
        "CATEGORIA": "CATEGORIA_DEFEITO",
        "LINHA": "LINHA_DEFEITO",
        "REGISTRADO_POR": "REGISTRADO_POR",
        "COD_FALHA": "COD_FALHA",
        "DESC_FALHA": "DESC_FALHA",
        "COMPONENTE": "COMPONENTE",
        "DESC_COMPONENTE": "DESC_COMPONENTE",
        "REFERENCIA": "REFERENCIA",
        "ANALISE": "ANALISE",
        "QTD": "QUANTIDADE_DEFEITO",
        "QTD.": "QUANTIDADE_DEFEITO",
        "QTD": "QUANTIDADE_DEFEITO",
        "MOTIVO": "MOTIVO",
        "DESC_MOTIVO": "DESC_MOTIVO",
    }
    cols = {}
    for c in df.columns:
        if c in m:
            cols[c] = m[c]
    return df.rename(columns=cols)


# -----------------------
# Padronização de valores
# -----------------------
def padronizar_data(df: pd.DataFrame, col: str = "DATA") -> pd.DataFrame:
    """Tenta normalizar a coluna de data para datetime."""
    if col not in df.columns:
        return df
    df[col] = pd.to_datetime(df[col], errors="coerce", dayfirst=True)
    return df


def padronizar_turno(df: pd.DataFrame, col_candidates: List[str]) -> pd.DataFrame:
    """Padroniza colunas de turno garantindo formato simples A/B/C ou 1/2/3."""
    for c in col_candidates:
        if c in df.columns:
            df[c] = df[c].astype(str).str.upper().str.strip()
            df[c] = df[c].replace({"TURNO_A": "A", "TURNOA": "A", "1": "A", "TURNO_1": "A", "A1": "A"})
    return df


def padronizar_modelo(valor: str) -> str:
    """Normaliza texto do modelo, exemplo CM-400 -> CM400."""
    if pd.isna(valor):
        return valor
    s = str(valor).upper()
    s = re.sub(r"[^A-Z0-9]", "", s)
    return s


def aplicar_padronizacoes_valores(df: pd.DataFrame) -> pd.DataFrame:
    """Aplica padronizações gerais nos campos críticos (DATA, TURNO, MODELO, LINHA)."""
    df = padronizar_data(df, "DATA")
    # modelo se aplica apenas se existir
    if "MODELO" in df.columns:
        df["MODELO"] = df["MODELO"].apply(padronizar_modelo)
    if "LINHA_PROD" in df.columns:
        df["LINHA_PROD"] = df["LINHA_PROD"].astype(str).str.extract(r"(\d+)").astype(float).fillna(0).astype(int)
    if "LINHA_DEFEITO" in df.columns:
        df["LINHA_DEFEITO"] = df["LINHA_DEFEITO"].astype(str).str.extract(r"(\d+)").astype(float).fillna(0).astype(int)
    return df


# -----------------------
# Junção / Merge
# -----------------------
def gerar_chave_unica(df: pd.DataFrame, cols: list, new_col: str = "CHAVE_UNICA") -> pd.DataFrame:
    """Gera chave única concatenando colunas (DATA|TURNO|LINHA|MODELO) para junções robustas."""
    def to_key(row):
        parts = []
        for c in cols:
            val = row.get(c)
            if pd.isna(val):
                parts.append("NA")
            else:
                parts.append(str(val))
        return "|".join(parts)

    df[new_col] = df.apply(to_key, axis=1)
    return df


def unir_bases(df_prod: pd.DataFrame, df_def: pd.DataFrame) -> pd.DataFrame:
    """
    Une as duas bases usando chaves consistentes.
    Resultado: dataframe de defeitos enriquecido com colunas de produção.
    """
    # garantir colunas padronizadas
    df_prod = normalizar_colunas(df_prod)
    df_def = normalizar_colunas(df_def)

    df_prod = mapear_colunas_producao(df_prod)
    df_def = mapear_colunas_defeitos(df_def)

    df_prod = aplicar_padronizacoes_valores(df_prod)
    df_def = aplicar_padronizacoes_valores(df_def)

    # gerar chaves
    prod_key_cols = ["DATA", "TURNO_PROD", "LINHA_PROD", "MODELO"]
    def_key_cols = ["DATA", "TURNO_DEFEITO", "LINHA_DEFEITO", "MODELO"]
    # criar colunas MODELO vazias nas defeitos se não existir
    if "MODELO" not in df_def.columns:
        df_def["MODELO"] = pd.NA

    df_prod = df_prod.rename(columns={"TURNO_PROD": "TURNO_PROD"})  # garantir
    df_def = df_def.rename(columns={"TURNO_DEFEITO": "TURNO_DEFEITO"})

    df_prod = gerar_chave_unica(df_prod, prod_key_cols, new_col="CHAVE_UNICA_PROD")
    # para defeitos usamos as mesmas colunas (troca nome turno)
    df_def = gerar_chave_unica(df_def, def_key_cols, new_col="CHAVE_UNICA_DEFEITO")

    # tentativa de merge por CHAVE_UNICA (left join pelos defeitos)
    merged = pd.merge(
        df_def,
        df_prod.add_prefix("PROD_"),
        left_on="CHAVE_UNICA_DEFEITO",
        right_on="PROD_CHAVE_UNICA_PROD",
        how="left",
        suffixes=("", "_PROD")
    )

    # renomear colunas de produção para padrão final (sem prefixo)
    # evitar sobrescrita de colunas existentes
    prod_cols_map = {}
    for c in merged.columns:
        if c.startswith("PROD_") and not c.startswith("PROD_CHAVE"):
            prod_cols_map[c] = c.replace("PROD_", "")
    merged = merged.rename(columns=prod_cols_map)

    return merged


# -----------------------
# Salvamento
# -----------------------
def salvar_base_unificada(df: pd.DataFrame, path: Path = BASE_UNIFICADA) -> None:
    """Salva a base unificada em Excel (sobrescreve)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_excel(path, index=False)


# -----------------------
# Função de alto nível
# -----------------------
def criar_base_unificada(path_prod: Path = FILE_PRODUCAO, path_def: Path = FILE_DEFEITOS) -> pd.DataFrame:
    """
    Fluxo completo:
    - ler produção
    - ler defeitos
    - normalizar e mapear colunas
    - unir e salvar
    Retorna o DataFrame unificado.
    """
    df_prod = ler_planilha_producao(path_prod)
    df_def = ler_planilha_defeitos(path_def)

    merged = unir_bases(df_prod, df_def)
    salvar_base_unificada(merged)
    return merged
