"""
pipeline/text_processor.py

Responsabilidade:
- Executar toda a pipeline de pré-processamento textual da Fase 2:
    1. Limpeza textual
    2. Normalização técnica
    3. Geração de TEXTO_PROCESSADO
    4. Persistência dos resultados

- Não faz vetorização nem agrupamento (Fase 2.2 e 2.3)
- Funciona totalmente independente da UI / Streamlit
"""

import pandas as pd
from pathlib import Path

from services.text_cleaner import clean_text
from services.text_normalizer import normalizar_texto


# ============================================================
# CONFIG
# ============================================================

BASE_PROCESSED = Path("data/processed/base_de_dados_unificada.xlsx")
OUTPUT_FILE = Path("data/processed/texto_processado.parquet")


# ============================================================
# 1) Função que processa uma linha de texto
# ============================================================

def processar_texto(texto: str) -> dict:
    """
    Retorna:
    {
        texto_limpo,
        texto_normalizado,
        texto_processado
    }
    """
    texto_limpo = clean_text(texto)
    texto_norm = normalizar_texto(texto)

    # Aqui definimos como será o “texto final” da pipeline
    texto_proc = texto_norm.strip()

    return {
        "TEXTO_LIMPO": texto_limpo,
        "TEXTO_NORMALIZADO": texto_norm,
        "TEXTO_PROCESSADO": texto_proc
    }


# ============================================================
# 2) Pipeline principal aplicada ao DataFrame
# ============================================================

def aplicar_pipeline(df: pd.DataFrame, coluna_desc="DESC_FALHA") -> pd.DataFrame:
    """
    Aplica limpeza + normalização + processamento final.
    """

    print("[Pipeline] Processando coluna:", coluna_desc)

    # garante que não quebra com NaN
    textos = df[coluna_desc].fillna("").astype(str)

    resultados = textos.apply(processar_texto).tolist()

    # converte lista de dict → DataFrame
    df_proc = pd.DataFrame(resultados)

    # anexa ao original
    df_out = pd.concat([df, df_proc], axis=1)

    return df_out


# ============================================================
# 3) Função principal para executar tudo
# ============================================================

def executar_pipeline_textual():
    """
    Carrega base_unificada -> aplica pipeline -> salva parquet.
    """
    print("[Pipeline] Carregando base unificada...")
    df = pd.read_excel(BASE_PROCESSED)

    print("[Pipeline] Aplicando processamento textual...")
    df = aplicar_pipeline(df, coluna_desc="DESC_FALHA")

    print("[Pipeline] Salvando arquivo final...")
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    # 🔒 Garantir que todas as colunas sejam strings (evita erros no parquet)
    df = df.astype(str)

    # salvar arquivo final
    df.to_parquet(OUTPUT_FILE, index=False)


    print("\n✔ Pipeline concluída!")
    print("✔ Arquivo salvo em:", OUTPUT_FILE)


# execução manual
if __name__ == "__main__":
    executar_pipeline_textual()
