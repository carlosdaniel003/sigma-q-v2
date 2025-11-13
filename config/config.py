"""
Arquivo de exemplo de configuração do SIGMA-Q v2.
Copie este arquivo para config.py e ajuste os valores conforme o ambiente.
"""

# Diretórios de dados
DATA_RAW_DIR = "data/raw"
DATA_PROCESSED_DIR = "data/processed"
BASE_UNIFICADA = "data/processed/base_de_dados_unificada.xlsx"

# Diretórios de modelos
MODEL_DIR = "model"
MODEL_FILE = f"{MODEL_DIR}/modelo_classificacao.pkl"
VECTORIZER_FILE = f"{MODEL_DIR}/vectorizer.pkl"

# Parâmetros de criticidade (ajustáveis)
CRITICIDADE_PESOS = {
    "frequencia": 0.5,
    "gravidade": 0.3,
    "tendencia": 0.2
}

# Configuração geral
LOG_DIR = "data/logs"