import sys
import os
import streamlit as st
from pathlib import Path

# Garantir que o Python veja o diretório raiz (sigma-q-v2)
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

# ---------------------------------------------------
# Configuração Geral do SIGMA-Q V2
# ---------------------------------------------------
st.set_page_config(
    page_title="SIGMA-Q V2",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------------------------------
# Carregar temas
# ---------------------------------------------------
with open("app/styles/base.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# ---------------------------------------------------
# Sidebar padrão
# ---------------------------------------------------
st.sidebar.title("📘 SIGMA-Q V2")
st.sidebar.write("Sistema de Inteligência para Gestão de Manufatura e Análise de Qualidade.")

st.sidebar.markdown("---")
st.sidebar.write("Navegação pelas páginas no menu superior ➜")


# ---------------------------------------------------
# Conteúdo Principal
# ---------------------------------------------------
st.title("SIGMA-Q V2")
st.subheader("Ambiente Principal")

st.markdown("""
Bem-vindo ao SIGMA-Q V2.

Utilize o menu lateral para navegar entre:
- Visão Geral
- Análises por Modelo
- Mapa de Causas
- Classificação Automática (IA)
""")

st.markdown("---")
st.caption("© 2025 - SIGMA-Q • Mondial Eletrodomésticos")
