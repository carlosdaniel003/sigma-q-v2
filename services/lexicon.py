# [BLOCK 4]
# services/lexicon.py
import json
from pathlib import Path
from typing import Dict

LEX_PATH = Path("models/lexicon.json")

def load_lexicon() -> Dict[str, str]:
    """Carrega lexicon (normalizado -> COD_FALHA)."""
    if not LEX_PATH.exists():
        return {}
    with open(LEX_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    # garantir chaves normalizadas (compatibilidade)
    return {k.strip(): v for k, v in data.items()}

def save_lexicon(lex: Dict[str, str]):
    """Sobrescreve lexicon com atomicidade simples."""
    LEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = LEX_PATH.with_suffix(".tmp.json")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(lex, f, ensure_ascii=False, indent=2)
    tmp.replace(LEX_PATH)

# Fim do BLOCK 4
