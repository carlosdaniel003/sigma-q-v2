import pandas as pd
from utils.unificador import unir_bases

def test_unir_bases_minimal():
    df_prod = pd.DataFrame({
        "Data": ["2025-10-01"],
        "Turno": ["A"],
        "Linha": [1],
        "Modelo": ["CM400"],
        "Qty_Geral": [100]
    })
    df_def = pd.DataFrame({
        "Data": ["2025-10-01"],
        "Turno": ["A"],
        "Linha": [1],
        "Desc. Falha": ["Teste de falha"],
        "Qtd": [1]
    })
    merged = unir_bases(df_prod, df_def)
    assert not merged.empty
    # coluna padronizada existe
    assert "DESC_FALHA" in merged.columns or "DESC_FALHA" in merged.columns
