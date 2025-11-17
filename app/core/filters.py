"""
Helpers de filtros reaproveitáveis.
"""
from typing import Dict
# [BLOCK 1]  -- atualizar em app/core/filters.py (substituir função apply_filters)
import pandas as pd

def _to_datetime_safe(series_or_value):
    """Converte séries ou valores para datetime, com fallback."""
    if isinstance(series_or_value, pd.Series):
        return pd.to_datetime(series_or_value, errors="coerce")
    else:
        # valor único (string, datetime, etc.)
        return pd.to_datetime(series_or_value, errors="coerce")

# core/filters.py

import pandas as pd

def apply_filters(df, filter_state):
    df2 = df.copy()

    # --- CONVERTER DATA PARA DATETIME ---
    if "DATA" in df2.columns:
        df2["DATA"] = pd.to_datetime(df2["DATA"], errors="coerce")

    # --- PERÍODO ---
    dr = filter_state.get("periodo", None)
    if dr and len(dr) == 2:
        start, end = dr
        df2 = df2[(df2["DATA"] >= pd.to_datetime(start)) & (df2["DATA"] <= pd.to_datetime(end))]

    # --- CATEGORIA ---
    cat = filter_state.get("categoria", "Todos")
    if cat != "Todos":
        df2 = df2[df2["CATEGORIA"] == cat]

    # --- MODELO ---
    modelo = filter_state.get("modelo", "Todos")
    if modelo != "Todos":
        df2 = df2[df2["DESCRICAO"] == modelo]

    # --- TURNO ---
    turno = filter_state.get("turno", "Todos")
    if turno != "Todos":
        df2 = df2[df2["TURNO"] == turno]

    # --- COD_FALHA ---
    cod = filter_state.get("cod_falha", "Todos")
    if cod != "Todos":
        df2 = df2[df2["COD_FALHA"] == cod]

    return df2
