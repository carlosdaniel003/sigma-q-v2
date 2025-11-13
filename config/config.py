"""
Configurações do SIGMA-Q v2 (arquivo real).
Não commit: ajustar locais sensíveis conforme ambiente.
"""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]

# Diretórios
DATA_RAW_DIR = BASE_DIR / "data" / "raw"
DATA_PROCESSED_DIR = BASE_DIR / "data" / "processed"
BASE_UNIFICADA = DATA_PROCESSED_DIR / "base_de_dados_unificada.xlsx"

# Nomes de arquivos de entrada esperados
FILE_PRODUCAO = DATA_RAW_DIR / "base_de_dados_prod.xlsx"
FILE_DEFEITOS = DATA_RAW_DIR / "base_de_dados_defeitos.xls"

# Parâmetros
DATE_FORMATS = ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"]  # tentativa de parsing
CRITICIDADE_PESOS = {"frequencia": 0.5, "gravidade": 0.3, "tendencia": 0.2}
