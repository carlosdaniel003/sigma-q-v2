import streamlit as st
import pandas as pd

st.set_page_config(page_title="Produção x Defeitos — Teste", layout="wide")
st.title("📊 Produção x Defeitos — Validação de Integração")

# ----------------------------------------------------------
# 1) Carregar bases oficiais
# ----------------------------------------------------------
@st.cache_data
def carregar_base_producao():
    df = pd.read_excel("data/raw/base_de_dados_prod.xlsx")
    df.columns = df.columns.str.upper()

    # converter data no formato BR
    df["DATA"] = pd.to_datetime(df["DATA"], dayfirst=True, errors="coerce")

    df["MES"] = df["DATA"].dt.month
    df["ANO"] = df["DATA"].dt.year
    return df


@st.cache_data
def carregar_base_defeitos():
    df = pd.read_excel("data/raw/base_de_dados_defeitos.xlsx")
    df.columns = df.columns.str.upper()

    # converter data no formato BR
    df["DATA"] = pd.to_datetime(df["DATA"], dayfirst=True, errors="coerce")

    df["MES"] = df["DATA"].dt.month
    df["ANO"] = df["DATA"].dt.year
    return df


df_prod = carregar_base_producao()
df_def = carregar_base_defeitos()

st.success("Bases carregadas com sucesso!")

# Normalizar colunas conhecidas que representam o modelo
map_modelo = {
    "DESCRICAO": "MODELO",
    "DESCRIÇÃO": "MODELO",
    "DESCRIÇÃO DO MATERIAL": "MODELO",
    "DESC_MATERIAL": "MODELO"
}

df_def.rename(columns={k: v for k, v in map_modelo.items() if k in df_def.columns}, inplace=True)

# ----------------------------------------------------------
# 2) Filtros (Ano e Mês)
# ----------------------------------------------------------
anos = sorted(df_prod["ANO"].unique().tolist())
ano_sel = st.selectbox("Selecione o ano", anos)

meses = sorted(df_prod[df_prod["ANO"] == ano_sel]["MES"].unique().tolist())
mes_sel = st.selectbox("Selecione o mês", meses)

df_prod_f = df_prod[(df_prod["ANO"] == ano_sel) & (df_prod["MES"] == mes_sel)]
df_def_f  = df_def[(df_def["ANO"] == ano_sel) & (df_def["MES"] == mes_sel)]

# ----------------------------------------------------------
# 3) Tabela — Produção por categoria e modelo
# ----------------------------------------------------------
st.subheader("📦 Produção por Categoria e Modelo — Resumo")

prod_por_modelo = (
    df_prod_f.groupby(["CATEGORIA", "MODELO"], as_index=False)
    .agg(QTY_GERAL=("QTY_GERAL", "sum"))
)

def_por_modelo = (
    df_def_f.groupby(["CATEGORIA", "MODELO"], as_index=False)
    .agg(QTD_DEFEITOS=("QTD", "sum"))
)

tabela = prod_por_modelo.merge(
    def_por_modelo, on=["CATEGORIA", "MODELO"], how="left"
).fillna(0)

tabela["% DEFEITO"] = (tabela["QTD_DEFEITOS"] / tabela["QTY_GERAL"]) * 100

st.dataframe(tabela, use_container_width=True)

# ----------------------------------------------------------
# 4) Gráfico — Produção vs Defeitos por Modelo
# ----------------------------------------------------------
st.subheader("📉 Relação Produção x Defeitos (por Modelo)")

import plotly.express as px

if len(tabela) > 0:
    fig = px.bar(
        tabela,
        x="MODELO",
        y=["QTY_GERAL", "QTD_DEFEITOS"],
        barmode="group",
        title="Produção vs Defeitos",
        labels={"value": "Quantidade", "variable": "Tipo"},
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Nenhum dado encontrado para o período selecionado.")
