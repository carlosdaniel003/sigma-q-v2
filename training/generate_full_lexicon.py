"""
training/generate_full_lexicon.py
Gera o lexicon completo e definitivo a partir do catálogo oficial (DESC_FALHA → COD_FALHA).

Execução:
    python -m training.generate_full_lexicon
"""

import json
import pandas as pd
import hashlib
from services.text_normalizer import normalizar_texto
from pathlib import Path

BASE_PATH = Path("data/raw/base_de_dados_defeitos.xlsx")
LEXICON_PATH = Path("models/lexicon.json")
CHECKSUM_PATH = Path("models/lexicon.sha256")


def gerar_checksum(conteudo: dict) -> str:
    """Retorna SHA256 do conteúdo JSON (ordenado)."""
    encoded = json.dumps(conteudo, sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def gerar_lexicon_completo():
    print("📌 Carregando catálogo oficial...")
    df = pd.read_excel(BASE_PATH)

    if "DESC. FALHA" in df.columns:
        df = df.rename(columns={"DESC. FALHA": "DESC_FALHA"})
    if "COD_FALHA" not in df.columns:
        raise ValueError("❌ A coluna COD_FALHA não existe na base oficial!")

    print(f"✔ Base carregada: {len(df)} linhas")

    # NORMALIZAR TEXTO
    df["TEXTO_NORMALIZADO"] = df["DESC_FALHA"].astype(str).apply(normalizar_texto)

    # REMOVER DUPLICATAS — pois diferentes ORDEM podem ter mesma descrição
    df_clean = df[["TEXTO_NORMALIZADO", "COD_FALHA"]].drop_duplicates()

    print(f"✔ Total de combinações únicas: {len(df_clean)}")

    # GERAR DICIONÁRIO
    lexicon = {
        row["TEXTO_NORMALIZADO"]: row["COD_FALHA"]
        for _, row in df_clean.iterrows()
    }

    # SALVAR
    print(f"💾 Salvando lexicon em: {LEXICON_PATH}")
    LEXICON_PATH.write_text(json.dumps(lexicon, indent=4, ensure_ascii=False), encoding="utf-8")

    # CHECKSUM
    checksum = gerar_checksum(lexicon)
    CHECKSUM_PATH.write_text(checksum, encoding="utf-8")

    print("\n🎉 Lexicon completo gerado com sucesso!")
    print(f"📚 Total final de chaves no lexicon: {len(lexicon)}")
    print(f"🔐 SHA256 salvo em: {CHECKSUM_PATH}")
    print(f"🔎 Exemplo das primeiras 5 entradas:")
    for k in list(lexicon.keys())[:5]:
        print(f"   {k} → {lexicon[k]}")


if __name__ == "__main__":
    gerar_lexicon_completo()
