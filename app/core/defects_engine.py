# ================================================================
# RESUMO DOS DEFEITOS — para página Classificação Defeitos
# ================================================================

import pandas as pd
from pathlib import Path

PATH_RAW = Path("data/raw")

def carregar_base_defeitos_simples():
    """Carrega a base de defeitos sem alterar nada, apenas padroniza nome de colunas."""
    df = pd.read_excel(PATH_RAW / "base_de_dados_defeitos.xlsx")
    df.columns = [c.strip().upper() for c in df.columns]
    return df


def gerar_resumo_defeitos():
    """
    Gera uma tabela simples de validação:
    - MODELO
    - QTD_DEFEITOS
    """

    df = carregar_base_defeitos_simples()

    # garantir coluna MODELO
    if "DESCRICAO" in df.columns:
        df["MODELO"] = df["DESCRICAO"].astype(str).str.strip()
    else:
        raise ValueError("Coluna 'DESCRICAO' não encontrada na base de defeitos.")

    resumo = (
        df.groupby("MODELO", as_index=False)
          .agg(QTD_DEFEITOS=("ORDEM", "count"))
          .sort_values("QTD_DEFEITOS", ascending=False)
    )

    return resumo