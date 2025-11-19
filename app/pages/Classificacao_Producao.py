import streamlit as st
import pandas as pd

from app.core.classificacao_producao import (
    carregar_base_producao,
    carregar_catalogo_modelos,
    validar_modelos_producao,
    modelos_sem_defeitos,
    modelos_defeito_sem_producao,
)

st.set_page_config(page_title="Classificação Produção", layout="wide")
st.title("🏭 Classificação da Produção — SIGMA-Q")

st.markdown("### Validação inteligente da base de produção usando o Catálogo Oficial SIGMA-Q")

# ------------------------------------------------------------
# Carregamento
# ------------------------------------------------------------
with st.spinner("Carregando bases oficiais..."):
    df_prod = carregar_base_producao()
    df_cat = carregar_catalogo_modelos()

st.success("Bases carregadas com sucesso.")

# ------------------------------------------------------------
# KPI PRINCIPAL
# ------------------------------------------------------------
resultado = validar_modelos_producao(df_prod, df_cat)

col1, col2, col3 = st.columns(3)
col1.metric("Modelos totais", resultado["total_modelos"])
col2.metric("Compreendidos pela IA", resultado["entendidos"])
col3.metric("KPI de entendimento", f"{resultado['kpi']:.2f}%")

# ------------------------------------------------------------
# Mensagem de sucesso
# ------------------------------------------------------------
if resultado["kpi"] == 100:
    st.success("🎉 **100% — Todos os modelos da produção foram compreendidos pelo SIGMA-Q!**")
else:
    st.warning("⚠️ Existem modelos que o SIGMA-Q ainda não reconhece.")

# ------------------------------------------------------------
# Divergências: Modelos sem mapeamento no Catálogo
# ------------------------------------------------------------
if resultado["divergentes"]:
    st.subheader("🚨 Modelos sem mapeamento no Catálogo")
    st.dataframe(pd.DataFrame({"MODELOS DIVERGENTES": resultado["divergentes"]}))
else:
    st.info("Nenhuma divergência de mapeamento encontrada.")

# ------------------------------------------------------------
# Modelos sem defeitos
# ------------------------------------------------------------
lista_sem_def = modelos_sem_defeitos(df_prod, df_cat)
st.subheader("📦 Modelos produzidos mas sem nenhum defeito registrado")

if lista_sem_def:
    st.dataframe(pd.DataFrame({"MODELOS SEM DEFEITO": lista_sem_def}))
else:
    st.info("Todos os modelos produzidos possuem ao menos um defeito registrado.")

# ------------------------------------------------------------
# Produtos com defeito mas sem produção (não contabilizados)
# ------------------------------------------------------------
lista_nao_conta = modelos_defeito_sem_producao(df_prod, df_cat)
st.subheader("🕒 Modelos com defeitos mas sem produção registrada (Não contabilizados)")

if lista_nao_conta:
    st.dataframe(pd.DataFrame({"MODELOS NÃO CONTABILIZADOS": lista_nao_conta}))
else:
    st.info("Nenhum modelo não contabilizado.")