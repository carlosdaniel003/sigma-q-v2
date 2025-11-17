# BLOCK 2 — training/seed_lexicon.py
# Semeadura total do lexicon a partir da base oficial de defeitos.

import json
import pandas as pd
from pathlib import Path
from services.text_normalizer import normalizar_texto

PATH_DATA = Path("data/raw/base_de_dados_defeitos.xlsx")
PATH_LEXICON = Path("models/lexicon.json")

def seed_lexicon():
    print("📌 Carregando base oficial...")
    df = pd.read_excel(PATH_DATA)

    # renomeações necessárias
    df = df.rename(columns={
        "DESC. FALHA": "DESC_FALHA",
        "COD_FALHA": "COD_FALHA"
    })

    print(f"✔ Base carregada: {len(df)} linhas.")

    lexicon = {}

    for _, row in df.iterrows():
        desc = str(row["DESC_FALHA"]).strip()
        codigo = str(row["COD_FALHA"]).strip().upper()

        key = normalizar_texto(desc)
        lexicon[key] = codigo

    print(f"✔ Total de entradas no lexicon: {len(lexicon)}")

    PATH_LEXICON.parent.mkdir(parents=True, exist_ok=True)
    with open(PATH_LEXICON, "w", encoding="utf-8") as f:
        json.dump(lexicon, f, indent=4, ensure_ascii=False)

    print("🎉 Lexicon salvo com sucesso em:", PATH_LEXICON)

if __name__ == "__main__":
    seed_lexicon()
