"""
services/text_cleaner.py
Responsável por: limpeza textual bruta
- Remover acentos, caracteres especiais
- Padronizar termos comuns
- Remover ruídos típicos de defeitos
"""

import re
import unicodedata
import pandas as pd


def remover_acentos(texto: str) -> str:
    """Remove acentos preservando caracteres básicos."""
    if pd.isna(texto):
        return ""
    nfkd = unicodedata.normalize("NFKD", texto)
    return "".join([c for c in nfkd if not unicodedata.combining(c)])


def limpeza_basica(texto: str) -> str:
    """Limpeza textual inicial (minúsculas, remove símbolos, normaliza espaços)."""
    if pd.isna(texto):
        return ""

    texto = remover_acentos(texto)
    texto = texto.upper()

    # Remove símbolos indesejados
    texto = re.sub(r"[^A-Z0-9\s]", " ", texto)
    texto = re.sub(r"\s+", " ", texto).strip()

    return texto


# Palavras sem valor técnico
STOPWORDS_TECNICAS = {
    "DO", "DA", "DE", "UM", "UMA", "NO", "NA", "OS", "AS", 
    "PARA", "COM", "SEM", "QUE", "EM"
}


def remover_stopwords(texto: str) -> str:
    """Remove palavras comuns que não influenciam diagnóstico."""
    tokens = texto.split()
    tokens = [t for t in tokens if t not in STOPWORDS_TECNICAS]
    return " ".join(tokens)


def clean_text(texto: str) -> str:
    """
    Pipeline de limpeza:
    1) remoção de acentos
    2) normalização
    3) remoção de stopwords
    """
    texto = limpeza_basica(texto)
    texto = remover_stopwords(texto)
    return texto
