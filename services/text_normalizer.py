"""
services/text_normalizer.py
Responsável por:
- Normalização técnica
- Redução de termos técnicos ao padrão único
- Correções de sinônimos industriais
"""

import re
import pandas as pd
from services.text_cleaner import clean_text


# Dicionário técnico definido com base no seu conhecimento da fábrica
DICIONARIO_TECNICO = {

    # 🎯 Sintomas
    r"\bNAO LIGA\b": "SEM_LIGACAO",
    r"\bAPARELHO NAO LIGA\b": "SEM_LIGACAO",
    r"\bSEM TENSAO\b": "SEM_LIGACAO",
    r"\bSEM IMAGEM\b": "SEM_IMAGEM",

    # 🎯 LED
    r"\bLED NAO ACENDE\b": "LED_APAGADO",
    r"\bLED NAO FUNCIONA\b": "LED_APAGADO",

    # 🎯 Áudio
    r"\bSEM AUDIO\b": "SEM_AUDIO",
    r"\bRUIDO NO AUDIO\b": "RUIDO_AUDIO",

    # 🎯 HDMI
    r"\bHDMI\b": "HDMI_ERRO",

    # 🎯 USB
    r"\bUSB\b": "USB_ERRO",

    # 🎯 Backlight TV
    r"\bBACKLIGHT\b": "BACKLIGHT_ERRO",

    # 🎯 Componentes padronizados
    r"\bTRANSISTOR SMD\b": "TRANSISTOR",
    r"\bCAPACITOR CERAMICO\b": "CAPACITOR",
    r"\bRESISTOR SMD\b": "RESISTOR",
}


def aplicar_dicionario_tecnico(texto: str) -> str:
    """Aplica todas as regras regulares do dicionário técnico."""
    for padrao, substituto in DICIONARIO_TECNICO.items():
        texto = re.sub(padrao, substituto, texto)
    return texto


def normalizar_texto(texto: str) -> str:
    """
    Pipeline de normalização técnica.

    1) Limpeza básica (text_cleaner)
    2) Normalização industrial
    """
    if pd.isna(texto):
        return ""

    texto = clean_text(texto)
    texto = aplicar_dicionario_tecnico(texto)

    return texto
