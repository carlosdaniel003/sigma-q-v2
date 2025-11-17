# BLOCK 6 – Seed Lexicon MASTER (aprendizado 100% oficial)
import json
import pandas as pd
from pathlib import Path
from services.text_normalizer import normalizar_texto

PATH_CODES = Path("data/raw/catalogo_codigos_defeitos.xlsx")
PATH_LEXICON = Path("models/lexicon.json")

def seed_master_lexicon():
    print("📘 Carregando Catálogo Oficial de Códigos…")
    df = pd.read_excel(PATH_CODES)

    df = df.rename(columns={
        "DESCRIÇÃO DO MATERIAL": "DESC_FALHA",
        "CODIGO": "COD_FALHA"
    })

    lexicon = {}

    for _, row in df.iterrows():
        desc = str(row["DESC_FALHA"])
        cod = str(row["COD_FALHA"]).strip()

        chave = normalizar_texto(desc)
        lexicon[chave] = cod

    PATH_LEXICON.parent.mkdir(parents=True, exist_ok=True)

    with open(PATH_LEXICON, "w", encoding="utf-8") as f:
        json.dump(lexicon, f, indent=4, ensure_ascii=False)

    print("🎉 Lexicon Master atualizado com sucesso!")
    print("Total de entradas:", len(lexicon))

if __name__ == "__main__":
    seed_master_lexicon()
