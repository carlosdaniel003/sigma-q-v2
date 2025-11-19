import streamlit as st
import pandas as pd
from app.core.classifier_service import ClassifierService
from services.text_normalizer import normalizar_texto
from services.lexicon import load_lexicon
from app.core.defects_engine import gerar_resumo_defeitos

st.set_page_config(
    page_title="Classificação Automática — SIGMA-Q",
    layout="wide"
)

st.title("🔍 Classificação Automática de Defeitos — SIGMA-Q IA (100% lexicon)")

# -----------------------------------------------------
# 1) Carregar base oficial
# -----------------------------------------------------
@st.cache_data(show_spinner=True)
def carregar_base_oficial():
    return pd.read_excel("data/raw/base_de_dados_defeitos.xlsx")

df_raw = carregar_base_oficial()

# -----------------------------------------------------
# 2) Padronizar nomes das colunas
# -----------------------------------------------------
renomear = {
    "DESC. FALHA": "DESC_FALHA",
    "DESC. COMPONENTE": "DESC_COMPONENTE",
    "DESC. MOTIVO": "DESC_MOTIVO",
    "REGISTRADO POR": "REGISTRADO_POR"
}
df_raw = df_raw.rename(columns=renomear)

if "DESC_FALHA" not in df_raw.columns:
    st.error("A coluna DESC_FALHA não existe na planilha. Verifique sua base.")
    st.stop()

# -----------------------------------------------------
# 3) Normalizar texto da descrição
# -----------------------------------------------------
df = df_raw.copy()
df["TEXTO_NORMALIZADO"] = df["DESC_FALHA"].astype(str).apply(normalizar_texto)

# -----------------------------------------------------
# 4) Aplicar classificação da IA (via lexicon + modelo)
# -----------------------------------------------------
svc = ClassifierService()
df["CODIGO_IA"] = df["TEXTO_NORMALIZADO"].apply(svc.predict)

# -----------------------------------------------------
# 5) KPI e divergências
# -----------------------------------------------------
df["ACERTO"] = df["COD_FALHA"].astype(str) == df["CODIGO_IA"].astype(str)

kpi = round(df["ACERTO"].mean() * 100, 2)
divs = df[df["ACERTO"] == False]

# -----------------------------------------------------
# 6) Mostrar KPI
# -----------------------------------------------------
st.subheader("📊 Acurácia da IA")

if kpi == 100.0:
    st.success("🎉 Classificação IA concluída com **100% de fidelidade (via lexicon)**")
else:
    st.warning(f"⚠ Acurácia da IA: **{kpi}%**")

st.metric(
    label="Acurácia da IA",
    value=f"{kpi}%",
    delta=f"{df['ACERTO'].sum()} corretos / {len(df) - df['ACERTO'].sum()} divergentes",
)

# -----------------------------------------------------
# 7) Mostrar divergências se houver
# -----------------------------------------------------
st.subheader("⚠ Divergências — IA vs Catálogo Oficial")

if kpi == 100.0:
    st.success("✔ Nenhuma divergência — Base 100% consistente!")
else:
    st.warning(f"{len(divs)} divergências encontradas — abaixo apenas ORDEM, DESC_FALHA, TEXTO_NORMALIZADO, COD_FALHA e CODIGO_IA:")
    st.dataframe(
        divs[[
            "ORDEM",
            "DESC_FALHA",
            "TEXTO_NORMALIZADO",
            "COD_FALHA",
            "CODIGO_IA"
        ]],
        use_container_width=True,
        height=500
    )

st.subheader("📘 Validação - Quantidade de defeitos por modelo")
df_resumo = gerar_resumo_defeitos()
st.dataframe(df_resumo, use_container_width=True)