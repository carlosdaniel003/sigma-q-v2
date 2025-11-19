# BLOCK C1 - app/core/catalogo_engine.py
"""
Catalogo Engine — carrega o catálogo oficial (planilha),
normaliza em memória e expõe APIs para:
- resolver_modelo_defeito(modelo_defeito) -> modelo_final, status
- listar_nao_contabilizados()
- atualizar_catalogo(novas_linhas)  # para aprendizado manual/automático
Persistência do lookup é feita em data/processed/catalogo_lookup.parquet (ou .json).
"""

from pathlib import Path
import pandas as pd
from typing import Optional, Tuple, Dict

ROOT = Path.cwd()
PATH_RAW = ROOT / "data" / "raw"
PATH_PROCESSED = ROOT / "data" / "processed"
PATH_PROCESSED.mkdir(parents=True, exist_ok=True)

# arquivo de catálogo oficial (você já colocou)
CANDIDATE_FILES = [
    PATH_RAW / "catalogo_modelos.xlsx",
    PATH_RAW / "catalogo_modelos.ods",
    PATH_RAW / "catalogo_modelos.csv",
]

# arquivo onde guardamos o lookup aprendido (apenas este arquivo pode ser gravado pelo sistema)
LOOKUP_PATH = PATH_PROCESSED / "catalogo_lookup.parquet"

# helpers de normalização (apenas em memória)
def _safe_str(x) -> str:
    if pd.isna(x):
        return ""
    return str(x).strip()

def _norm(s: Optional[str]) -> str:
    s = _safe_str(s).upper()
    # compactar espaços e remover caracteres problemáticos mantendo ponto, - e /
    s = " ".join(s.split())
    s = ''.join(ch for ch in s if (ch.isalnum() or ch.isspace() or ch in ['-', '/', '.', '%']))
    s = " ".join(s.split())
    return s

# carrega a planilha oficial (apenas leitura)
def _load_catalogo_oficial() -> pd.DataFrame:
    for p in CANDIDATE_FILES:
        if p.exists():
            # pandas lê xlsx/ods/csv automaticamente via engine
            try:
                df = pd.read_excel(p) if p.suffix.lower() in (".xlsx", ".ods", ".xls") else pd.read_csv(p)
            except Exception:
                df = pd.read_csv(p, encoding="utf-8", engine="python")
            # padronizar colnames para facilitar
            df.columns = [c.strip().upper() for c in df.columns]
            return df
    raise FileNotFoundError("Arquivo de catálogo não encontrado em data/raw/catalogo_modelos.*")

# carrega lookup persistido (se existir)
def _load_persisted_lookup() -> pd.DataFrame:
    if LOOKUP_PATH.exists():
        return pd.read_parquet(LOOKUP_PATH)
    # criar empty
    return pd.DataFrame(columns=["MODELO_DEFEITO", "SE_TRATA_DE", "CORRESPONDE_A", "MODELO_FINAL", "STATUS"])

# persiste lookup (sobrescreve arquivo de lookup apenas)
def _save_lookup(df: pd.DataFrame):
    df.to_parquet(LOOKUP_PATH, index=False)

# construir lookup combinado: oficial + persistido
def build_lookup(force_reload: bool = False) -> pd.DataFrame:
    """
    Retorna DataFrame de lookup com colunas:
    MODELO_DEFEITO, SE_TRATA_DE, CORRESPONDE_A, MODELO_FINAL, STATUS
    STATUS = OK | NAO_CONTABILIZADO
    """
    # load official
    df_official = _load_catalogo_oficial()
    # normalizar nomes de colunas esperadas
    colmap = {c: c for c in df_official.columns}
    # possíveis nomes alternativos
    # (guarda compatibilidade)
    needed = ["MODELOS DEFEITOS", "MODELOSDEFEITOS", "MODELOS_DEFEITOS", "MODELOS DEFEITO", "MODELOS DEFEITO"]
    if "MODELOS DEFEITOS" not in df_official.columns and "MODELOS DEFEITOS".replace(" ", "") not in "".join(df_official.columns):
        # tentar localizar coluna que pareça MODELOS DEFEITO
        pass
    # unify expected cols - try common names
    cols = [c for c in df_official.columns]
    # rename guesses
    rename_map = {}
    for c in cols:
        cu = c.upper().replace("_", " ").strip()
        if "MODELO" in cu and "DEFEIT" in cu:
            rename_map[c] = "MODELO_DEFEITO"
        elif cu in ("SE TRATA DE", "SETRATADE", "SE TRATA", "SE TRATADE"):
            rename_map[c] = "SE_TRATA_DE"
        elif "CORRESPONDE" in cu:
            rename_map[c] = "CORRESPONDE_A"
        elif "PRODUCAO" in cu or "PRODUÇÃO" in cu:
            rename_map[c] = "MODELO_PRODUCAO"
    df_official = df_official.rename(columns=rename_map)
    # ensure columns exist
    for must in ["MODELO_DEFEITO", "SE_TRATA_DE", "CORRESPONDE_A", "MODELO_PRODUCAO"]:
        if must not in df_official.columns:
            df_official[must] = ""

    # normalize text (in-memory only)
    df_official["MODELO_DEFEITO_NORM"] = df_official["MODELO_DEFEITO"].apply(_norm)
    df_official["CORRESPONDE_A_NORM"] = df_official["CORRESPONDE_A"].apply(_norm)
    df_official["MODELO_PRODUCAO_NORM"] = df_official["MODELO_PRODUCAO"].apply(_norm)

    # load persisted lookup and merge (persisted may contain manual corrections/additions)
    df_persist = _load_persisted_lookup()
    if not df_persist.empty:
        df_persist["MODELO_DEFEITO_NORM"] = df_persist["MODELO_DEFEITO"].apply(_norm)
        # If persisted overrides official, prefer persisted
        # join by MODELO_DEFEITO_NORM
        df_merge = pd.merge(df_official, df_persist, on="MODELO_DEFEITO_NORM", how="left", suffixes=("_OFF", "_PERS"))
        # choose persistence if available
        def coalesce(row, col):
            v = row.get(f"{col}_PERS")
            if v and str(v).strip():
                return v
            return row.get(f"{col}_OFF")
        rows = []
        for _, r in df_merge.iterrows():
            modelo_defeito = r.get("MODELO_DEFEITO_PERS") if r.get("MODELO_DEFEITO_PERS") else r.get("MODELO_DEFEITO_OFF")
            se_trata = coalesce(r, "SE_TRATA_DE")
            corresponde = coalesce(r, "CORRESPONDE_A")
            modelo_prod = coalesce(r, "MODELO_PRODUCAO")
            rows.append({
                "MODELO_DEFEITO": modelo_defeito,
                "SE_TRATA_DE": se_trata,
                "CORRESPONDE_A": corresponde,
                "MODELO_PRODUCAO": modelo_prod
            })
        df_lookup = pd.DataFrame(rows)
    else:
        df_lookup = df_official[["MODELO_DEFEITO", "SE_TRATA_DE", "CORRESPONDE_A", "MODELO_PRODUCAO"]].copy()

    # finalize: MODELO_FINAL = normalized CORRESPONDE_A (fallback: própria MODELO_DEFEITO se SE_TRATA_DE == PRODUTO)
    df_lookup["MODELO_DEFEITO_NORM"] = df_lookup["MODELO_DEFEITO"].apply(_norm)
    df_lookup["MODELO_FINAL"] = df_lookup["CORRESPONDE_A"].where(df_lookup["CORRESPONDE_A"].astype(str).str.strip() != "", df_lookup["MODELO_DEFEITO"])
    df_lookup["MODELO_FINAL_NORM"] = df_lookup["MODELO_FINAL"].apply(_norm)
    # mark status: se MODELO_PRODUCAO_NORM existe em lista de producao do catálogo -> OK, else NAO_CONTABILIZADO
    prod_set = set(df_lookup["MODELO_PRODUCAO"].apply(_norm).unique())
    df_lookup["STATUS"] = df_lookup["MODELO_PRODUCAO"].apply(lambda x: "OK" if _norm(x) in prod_set and _norm(x) != "" else "NAO_CONTABILIZADO")
    # keep only columns we need (in-memory)
    out = df_lookup[["MODELO_DEFEITO", "SE_TRATA_DE", "CORRESPONDE_A", "MODELO_PRODUCAO", "MODELO_FINAL", "STATUS"]].copy()
    return out

# API: resolver modelo defeito -> modelo_final, status
def resolver_modelo_defeito(modelo_defeito: str) -> Tuple[str, str]:
    """
    Recebe o MODELO como aparece na base de defeitos (string).
    Retorna (modelo_final, status) onde:
      modelo_final = string do modelo padronizado (a ser usado internamente pelo PPM)
      status = "OK" | "NAO_CONTABILIZADO" | "UNKNOWN"
    """
    lookup = build_lookup()
    key = _norm(modelo_defeito)
    # busca direta por MODELO_DEFEITO normalizado
    candidates = lookup[lookup["MODELO_DEFEITO"].apply(_norm) == key]
    if not candidates.empty:
        row = candidates.iloc[0]
        return (row["MODELO_FINAL"], row["STATUS"])
    # fallback: buscar se modelo_defeito corresponde diretamente a algum MODELO_PRODUCAO
    cand2 = lookup[lookup["MODELO_PRODUCAO"].apply(_norm) == key]
    if not cand2.empty:
        row = cand2.iloc[0]
        return (row["MODELO_FINAL"], row["STATUS"])
    # unknown -> retornar original (mas sinalizar)
    return (modelo_defeito, "UNKNOWN")

# API: atualizar lookup (aprender novos mapeamentos)
def atualizar_catalogo(novas_linhas: pd.DataFrame):
    """
    novas_linhas: DataFrame com colunas MODELO_DEFEITO, SE_TRATA_DE, CORRESPONDE_A, MODELO_PRODUCAO (opcional)
    O método faz append/merge no arquivo LOOKUP_PATH (persistido), sem alterar os arquivos raw.
    """
    if not isinstance(novas_linhas, pd.DataFrame):
        raise ValueError("novas_linhas deve ser um pandas.DataFrame")
    # ler persistido, concatenar (usando MODELO_DEFEITO como chave), deduplicar por MODELO_DEFEITO_NORM
    df_persist = _load_persisted_lookup()
    base = df_persist.copy() if not df_persist.empty else pd.DataFrame(columns=["MODELO_DEFEITO", "SE_TRATA_DE", "CORRESPONDE_A", "MODELO_PRODUCAO", "MODELO_FINAL", "STATUS"])
    # compute MODELO_FINAL from CORRESPONDE_A (if provided)
    if "CORRESPONDE_A" in novas_linhas.columns:
        novas_linhas["MODELO_FINAL"] = novas_linhas["CORRESPONDE_A"].where(novas_linhas["CORRESPONDE_A"].astype(str).str.strip() != "", novas_linhas["MODELO_DEFEITO"])
    else:
        novas_linhas["MODELO_FINAL"] = novas_linhas["MODELO_DEFEITO"]
    # concat and dedupe by normalized key
    combined = pd.concat([base, novas_linhas], ignore_index=True, sort=False).fillna("")
    combined["KEY"] = combined["MODELO_DEFEITO"].apply(_norm)
    combined = combined.drop_duplicates(subset=["KEY"], keep="last")
    # recalc status (best-effort)
    combined["STATUS"] = combined["MODELO_PRODUCAO"].apply(lambda x: "OK" if _norm(x) != "" else "NAO_CONTABILIZADO")
    # keep columns
    combined = combined[["MODELO_DEFEITO", "SE_TRATA_DE", "CORRESPONDE_A", "MODELO_PRODUCAO", "MODELO_FINAL", "STATUS"]]
    _save_lookup(combined)
    return combined

# helper para auditoria
def status_auditoria() -> Dict[str, int]:
    df = build_lookup()
    total = len(df)
    ok = len(df[df["STATUS"] == "OK"])
    nao = len(df[df["STATUS"] != "OK"])
    unknown = 0  # placeholders; resolver_modelo_defeito pode retornar UNKNOWN para itens não previstos
    return {"total": total, "ok": ok, "nao_contabilizados": nao, "unknown": unknown}