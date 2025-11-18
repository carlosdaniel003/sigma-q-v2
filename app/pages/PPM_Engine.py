# -------------------------------
# [BLOCK 1] • Imports e Configuração
# -------------------------------
import streamlit as st
import pandas as pd
from app.core.ppm_engine import (
    carregar_base_producao,
    carregar_base_defeitos,
    sanity_check_joinable,
    gerar_tabela_ppm,
)

st.set_page_config(page_title="PPM Engine - Validação", layout="wide")
st.title("📊 PPM Engine — Validação de Integração")
st.markdown("Página dinâmica com filtros + auditoria + indicadores PPM.")
# -------------------------------
# [BLOCK 3] • Carregar bases oficiais (Produção & Defeitos)
# -------------------------------
@st.cache_data(show_spinner=True)
def load_bases():
    df_prod = carregar_base_producao()
    df_def  = carregar_base_defeitos()

    # Garantir colunas de data
    if "DATA" in df_prod.columns:
        df_prod["DATA"] = pd.to_datetime(df_prod["DATA"], errors="coerce")

    if "DATA" in df_def.columns:
        df_def["DATA"] = pd.to_datetime(df_def["DATA"], errors="coerce")

    # Extrair ANO/MES
    for df in [df_prod, df_def]:
        df["ANO"] = df["DATA"].dt.year
        df["MES"] = df["DATA"].dt.month

    return df_prod, df_def

df_prod, df_def = load_bases()

st.success(f"✔ Bases carregadas — Produção: {len(df_prod)} linhas | Defeitos: {len(df_def)} linhas")

# -------------------------------
# [BLOCK 4] • Filtros Globais
# -------------------------------
st.sidebar.header("Filtros — Período e Escopo")

# ANOS disponíveis (baseados em produção)
anos = sorted(df_prod["ANO"].dropna().unique().tolist())
ano_sel = st.sidebar.selectbox("Ano", ["Todos"] + anos)

# MESES disponíveis (dependendo do ano)
if ano_sel != "Todos":
    meses = sorted(df_prod[df_prod["ANO"] == ano_sel]["MES"].dropna().unique().tolist())
else:
    meses = sorted(df_prod["MES"].dropna().unique().tolist())

mes_sel = st.sidebar.selectbox("Mês", ["Todos"] + meses)

# CATEGORIAS disponíveis
categorias = sorted(df_prod["CATEGORIA"].dropna().unique().tolist())
cat_sel = st.sidebar.multiselect("Categoria", categorias, default=[])

# MODELOS disponíveis (produzidos ou com defeito)
modelos_disponiveis = sorted(
    pd.concat([df_prod["MODELO"].dropna(), df_def["MODELO"].dropna()])
    .unique()
    .tolist()
)
mod_sel = st.sidebar.multiselect("Modelo (opcional)", modelos_disponiveis, default=[])

# -------------------------------------------------------------
# Aplicação dos filtros sobre Produção e Defeitos
# -------------------------------------------------------------
df_prod_f = df_prod.copy()
df_def_f  = df_def.copy()

# Filtro Ano
if ano_sel != "Todos":
    df_prod_f = df_prod_f[df_prod_f["ANO"] == ano_sel]
    df_def_f  = df_def_f[df_def_f["ANO"] == ano_sel]

# Filtro Mês
if mes_sel != "Todos":
    df_prod_f = df_prod_f[df_prod_f["MES"] == mes_sel]
    df_def_f  = df_def_f[df_def_f["MES"] == mes_sel]

# Filtro Categoria
if cat_sel:
    df_prod_f = df_prod_f[df_prod_f["CATEGORIA"].isin(cat_sel)]
    df_def_f  = df_def_f[df_def_f["CATEGORIA"].isin(cat_sel)]

# Filtro Modelo
if mod_sel:
    df_prod_f = df_prod_f[df_prod_f["MODELO"].isin(mod_sel)]
    df_def_f  = df_def_f[df_def_f["MODELO"].isin(mod_sel)]

st.info(
    f"Produção filtrada: {len(df_prod_f)} linhas • "
    f"Defeitos filtrados: {len(df_def_f)} linhas"
)

# -------------------------------
# [BLOCK 5] • Tabela — Produção por Categoria e Modelo
# -------------------------------
st.subheader("🏭 Produção por Categoria e Modelo")

prod_por_modelo = (
    df_prod_f.groupby(["CATEGORIA", "MODELO"], as_index=False)
    .agg(QTY_GERAL=("QTY_GERAL", "sum"))
)

st.dataframe(prod_por_modelo, use_container_width=True, height=350)

# -------------------------------
# [BLOCK 6] • Tabela — Defeitos por Categoria e Modelo
# -------------------------------
st.subheader("🔧 Defeitos por Categoria e Modelo")

def_por_modelo = (
    df_def_f.groupby(["CATEGORIA", "MODELO"], as_index=False)
    .agg(QTD_DEFEITOS=("QTD", "sum"))
)

st.dataframe(def_por_modelo, use_container_width=True, height=350)

# -------------------------------
# [BLOCK 7] • Auditoria — Modelos sem Produção / sem Defeitos
# -------------------------------
st.subheader("🧪 Auditoria de Consistência (Produção vs Defeitos)")

from app.core.ppm_engine import sanity_check_joinable

check = sanity_check_joinable(df_def_f, df_prod_f)

colA, colB, colC = st.columns(3)
colA.metric("Modelos na base de defeitos", check["count_def_models"])
colB.metric("Modelos na base de produção", check["count_prod_models"])
colC.metric("Modelos sem produção", len(check["missing_in_prod"]))

with st.expander("🔍 Ver modelos sem produção"):
    st.write(pd.DataFrame({"MODELO": check["missing_in_prod"]}))

with st.expander("🔍 Ver modelos sem defeitos"):
    st.write(pd.DataFrame({"MODELO": check["missing_in_def"]}))

# -------------------------------
# [BLOCK 8] • Tabela Oficial PPM (Motor PPM Engine)
# -------------------------------
st.subheader("📌 PPM — Produção vs Defeitos (por Modelo)")

from app.core.ppm_engine import gerar_tabela_ppm

tabela_ppm = gerar_tabela_ppm(df_def_f, df_prod_f)

# Remover coluna MODELO_EXEMPLO se existir
if "MODELO_EXEMPLO" in tabela_ppm.columns:
    tabela_ppm = tabela_ppm.drop(columns=["MODELO_EXEMPLO"])

st.dataframe(tabela_ppm, use_container_width=True)
