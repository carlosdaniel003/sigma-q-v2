# [BLOCK 1]
# services/text_normalizer.py
# Normalizador conservador — NÃO remove stopwords.
# - Remove acentos
# - Substitui pontuação por espaços
# - Condensa espaços
# - Troca espaços por underscore
# - Retorna MAIÚSCULAS (compatível com pipeline atual)

import re
import unicodedata
from typing import List, Optional

def _remover_acentos(text: str) -> str:
    """Remove acentos mantendo caracteres base (á -> a)."""
    if not isinstance(text, str):
        return ""
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join([c for c in nfkd if not unicodedata.combining(c)])

def _limpar_pontuacao(text: str) -> str:
    """
    Substitui qualquer caracter que não seja letra, número ou underscore por espaço.
    Mantemos números e palavras curtas — não removemos stopwords.
    """
    # \w equivale a [a-zA-Z0-9_], usamos re.UNICODE para segurança internacional
    return re.sub(r"[^\w\s]", " ", text, flags=re.UNICODE)

def normalizar_texto(text: Optional[str]) -> str:
    """
    Normaliza um único texto:
    - converte None -> ""
    - remove acentos
    - remove pontuação (substitui por espaço)
    - condensa espaços
    - substitui espaços por underscore
    - remove underscores duplicados
    - converte para MAIÚSCULAS
    """
    if text is None:
        return ""

    # garantir string
    s = str(text)

    # 1) strip externo
    s = s.strip()

    # 2) remover acentos
    s = _remover_acentos(s)

    # 3) substituir pontuação por espaço (mantém numeros e letras)
    s = _limpar_pontuacao(s)

    # 4) normalizar espaços (multiespaços -> single space)
    s = re.sub(r"\s+", " ", s).strip()

    if s == "":
        return ""

    # 5) transformar espaços em underscore e remover underscores duplicados
    s = s.replace(" ", "_")
    s = re.sub(r"_+", "_", s)

    # 6) tornar maiúsculo (consistência com pipeline existente)
    return s.upper()

def normalizar_batch(texts: List[Optional[str]]) -> List[str]:
    """Normaliza uma lista de textos (útil em pipelines)."""
    return [normalizar_texto(t) for t in texts]

# Fim do BLOCK 1
