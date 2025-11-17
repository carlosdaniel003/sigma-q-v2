# BLOCK 5 – Página 5 (Catálogo Oficial de Defeitos SIGMA-Q)
import streamlit as st
import pandas as pd

st.set_page_config(page_title="Catálogo Oficial de Defeitos", layout="wide")
st.title("📚 Catálogo Oficial SIGMA-Q — Defeitos, Responsabilidades e Causas")

# =============================================================
# Carregar planilhas oficiais
# =============================================================

@st.cache_data
def carregar_catalogo():
    df_codes = pd.read_excel("data/raw/catalogo_codigos_defeitos.xlsx")
    df_resp = pd.read_excel("data/raw/catalogo_responsabilidades.xlsx")
    df_causa = pd.read_excel("data/raw/catalogo_causas.xlsx")
    return df_codes, df_resp, df_causa

df_codes, df_resp, df_causa = carregar_catalogo()

# =============================================================
# Exibição
# =============================================================
st.header("🔧 1. Catálogo de Códigos de Falha")
st.dataframe(df_codes, use_container_width=True)

st.header("🛠 2. Padrão de Responsabilidade")
st.dataframe(df_resp, use_container_width=True)

st.header("📌 3. Catálogo de Causas")
st.dataframe(df_causa, use_container_width=True)

st.info("Esses catálogos são a base oficial de aprendizagem do SIGMA-Q IA.")
