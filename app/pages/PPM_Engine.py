# ==================================================
# Página 7 — Produção vs Defeitos (PPM Engine) — completo
# Estrutura de blocos numerados (seguir regra do projeto)
# ==================================================

import streamlit as st
import pandas as pd
import numpy as np

# ------------------ [BLOCK 1] - Configuração da página ------------------
st.set_page_config(page_title="📊 PPM Engine — Produção vs Defeitos", layout="wide")
st.title("📊 PPM — Produção vs Defeitos (PPM Engine)")
st.markdown("Página dinâmica: filtrar por ano/mês/período, comparar produção x defeitos e navegar pelos resultados.")

# ------------------ [BLOCK 2] - Funções de carga (evitar circular imports) ------------------
@st.cache_data(show_spinner=True)
def load_bases():
    """
    Carrega bases via ppm_engine *sem* causar import circular.
    Preserva MODELO_RAW e cria MODELO_AUDIT para exibição/auditoria.
    """
    # import interno para evitar circular import issues
    from app.core import ppm_engine

    # usar as funções do engine
    df_prod = ppm_engine.carregar_base_producao()
    df_def = ppm_engine.carregar_base_defeitos()

    # preservar coluna DESCRICAO (origem) se existir, senão criar MODELO_RAW a partir de MODELO
    if "DESCRICAO" in df_def.columns:
        df_def["MODELO_RAW"] = df_def["DESCRICAO"].astype(str).str.strip()
    else:
        df_def["MODELO_RAW"] = df_def.get("MODELO", "").astype(str)

    # garantir datetime e colunas ANO/MES
    for df in (df_prod, df_def):
        if "DATA" in df.columns:
            df["DATA"] = pd.to_datetime(df["DATA"], errors="coerce")
        else:
            df["DATA"] = pd.NaT
        df["ANO"] = df["DATA"].dt.year
        df["MES"] = df["DATA"].dt.month

    # --- mapping manual rápido (aplica apenas para AUDITORIA/display)
    MANUAL_AUDIT_MAP = {
        "ALTO FALANTE 10POL TW": "TORRE DE SOM AWS-T2W-02 BIVOLT BLUETOOTH",
        'ALTO FALANTE 8 3 OHMS CM-250': "CAIXA AMPLIFICADA CM-250 BIVOLT",
        'ALTO FALANTE 8" 3 OHMS CM-250': "CAIXA AMPLIFICADA CM-250 BIVOLT",
        'CAIXA AMPLIFICADA CM-400 BIVOLT': "ALTO FALANTE 12POL. 6 OHMS CM-400/CM-550",
        'CAIXA AMPLIFICADA CM-550 BIVOLT': "ALTO FALANTE 12POL. 6 OHMS CM-400/CM-550",
        'MICRO-ONDAS MO-01-21-E 127V/60HZ': 'MICRO-ONDAS MO-01-21-E 220V/60HZ',
        'MICROONDAS MO-01-21-W': 'MICRO-ONDAS MO-01-21-W 220V/60HZ',
        # sinalizar explicitamente não contabilizados (serão filtrados da lista de "ausentes")
        'EVAPORADOR AWS-EV-9QF 220V': '<<NAO_CONTABILIZADO>>',
        'TORRE DE SOM TM-2200 BIV': '<<NAO_CONTABILIZADO>>',
        'CONTROLE REMOTO KTC ANDROID - IM': '<<NAO_CONTABILIZADO>>'
    }

    def _map_audit(raw):
        if not isinstance(raw, str):
            return ""
        key = raw.strip().upper()
        return MANUAL_AUDIT_MAP.get(key, raw)

    df_def["MODELO_AUDIT"] = df_def["MODELO_RAW"].astype(str).apply(_map_audit)

    return df_prod, df_def

# ------------------ [BLOCK 3] - Carregar dados (com spinner) ------------------
with st.spinner("Carregando bases..."):
    try:
        df_prod, df_def = load_bases()
    except FileNotFoundError as e:
        st.error(f"Arquivo não encontrado: {e}")
        st.stop()
    except Exception as e:
        st.error(f"Erro ao carregar bases: {e}")
        st.stop()

st.success(f"Bases carregadas — produção: {len(df_prod)} linhas, defeitos: {len(df_def)} linhas")

# ------------------ [BLOCK 4] - Sanity check / auditoria (ajustada) ------------------
st.subheader("🔎 Auditoria — Modelos com/sem Produção")

# import interno para usar sanity_check_joinable
from app.core import ppm_engine
check = ppm_engine.sanity_check_joinable(df_def, df_prod)

col1, col2, col3 = st.columns([2, 3, 3])
col1.metric("Modelos na base de defeitos", check.get("count_def_models", "-"))
col2.metric("Modelos na base de produção", check.get("count_prod_models", "-"))

# construir lista de modelos sem produção (após aplicar MAP de auditoria)
missing = check.get("missing_in_prod", [])

audit_rows = []
not_counted_rows = []  # modelos explicitamente marcados como "não contabilizado"

for m in missing:
    # localizar ocorrência em df_def (normalizado MODELO) para pegar MODELO_RAW/MODELO_AUDIT
    hits = df_def[df_def.get("MODELO", "").astype(str) == str(m)]
    if not hits.empty:
        modelo_raw = hits["MODELO_RAW"].iloc[0]
        modelo_audit = hits.get("MODELO_AUDIT", pd.Series([modelo_raw])).iloc[0]
    else:
        modelo_raw = m
        modelo_audit = m

    if str(modelo_audit).upper() == "<<NAO_CONTABILIZADO>>":
        # sinalizar em outra lista
        not_counted_rows.append({"MODELO": modelo_raw, "STATUS": "NÃO CONTABILIZADO"})
        continue

    obs = None
    if modelo_audit and modelo_audit != modelo_raw:
        obs = f"Corresponde a: {modelo_audit}"

    audit_rows.append({"MODELO": modelo_raw, "OBS": obs})

with st.expander("🔍 Ver modelos sem produção"):
    if audit_rows:
        df_audit = pd.DataFrame(audit_rows)
        st.dataframe(df_audit.fillna(""), use_container_width=True, height=300)
    else:
        st.info("Nenhum modelo ausente (após mapeamentos locais).")

with st.expander("📋 Ver modelos não contabilizados (sinalizados)"):
    if not_counted_rows:
        df_not_counted = pd.DataFrame(not_counted_rows)
        st.dataframe(df_not_counted, use_container_width=True, height=180)
    else:
        st.info("Nenhum item marcado como não contabilizado.")

with st.expander("🔎 Ver modelos com produção mas sem defeitos (amostra)"):
    st.write(pd.DataFrame({"MODELO_MISSING_IN_DEF": check.get("missing_in_def", [])}))

# ------------------ [BLOCK 5] - Painel de filtros ------------------
st.sidebar.header("Filtros — Período e Escopo")

# período disponível nas bases (usar df_def data para filtros de defeitos)
anos = sorted(df_def["ANO"].dropna().astype(int).unique().tolist()) if "ANO" in df_def.columns else []
anos_prod = sorted(df_prod["ANO"].dropna().astype(int).unique().tolist()) if "ANO" in df_prod.columns else []
anos_all = sorted(set(anos + anos_prod))

f_ano = st.sidebar.selectbox("Ano (filtro)", options=["Todos"] + anos_all, index=0 if anos_all else 0)

# meses disponíveis (depende do ano selecionado)
def meses_para_ano(df, ano):
    if ano == "Todos" or ano is None:
        return sorted(df["MES"].dropna().astype(int).unique().tolist())
    return sorted(df[df["ANO"] == int(ano)]["MES"].dropna().astype(int).unique().tolist())

meses = sorted(set(meses_para_ano(df_def, f_ano) + meses_para_ano(df_prod, f_ano)))
f_mes = st.sidebar.selectbox("Mês (filtro)", options=["Todos"] + meses, index=0 if meses else 0)

cats = sorted(df_prod["CATEGORIA"].dropna().unique().tolist()) if "CATEGORIA" in df_prod.columns else []
# modelos provenientes da produção + defeitos (MODELO_RAW e MODELO normalizado)
modelos_prod = df_prod.get("MODELO", pd.Series(dtype=str)).dropna().unique().tolist()
modelos_def = df_def.get("MODELO", pd.Series(dtype=str)).dropna().unique().tolist()
modelos_union = sorted(set(list(modelos_prod) + list(modelos_def)))

f_categoria = st.sidebar.multiselect("Categoria (produção)", options=cats, default=[])
f_modelo = st.sidebar.multiselect("Modelo (opcional)", options=modelos_union, default=[])

# ------------------ [BLOCK 6] - Aplicar filtros às bases ------------------
st.subheader("🔧 Aplicando filtros")

df_def_f = df_def.copy()
df_prod_f = df_prod.copy()

# aplicar ano/mes
if f_ano != "Todos":
    df_def_f = df_def_f[df_def_f["ANO"] == int(f_ano)]
    df_prod_f = df_prod_f[df_prod_f["ANO"] == int(f_ano)]

if f_mes != "Todos":
    df_def_f = df_def_f[df_def_f["MES"] == int(f_mes)]
    df_prod_f = df_prod_f[df_prod_f["MES"] == int(f_mes)]

# aplicar categoria/modelo
if f_categoria:
    df_prod_f = df_prod_f[df_prod_f["CATEGORIA"].isin(f_categoria)]
if f_modelo:
    df_prod_f = df_prod_f[df_prod_f["MODELO"].isin(f_modelo)]
    df_def_f = df_def_f[df_def_f["MODELO"].isin(f_modelo)]

st.info(f"Defeitos após filtro: {len(df_def_f)} linhas — Produção após filtro: {len(df_prod_f)} linhas")

# ------------------ [BLOCK 7] - KPIs Rápidos ------------------
st.subheader("📈 KPIs Rápidos")
colk1, colk2, colk3 = st.columns(3)
colk1.metric("Total Produção (linhas) ", f"{len(df_prod_f)}")
colk2.metric("Total Defeitos (linhas)", f"{len(df_def_f)}")

# PPM médio visível (tentar via engine)
try:
    ppm_resumo_tmp = ppm_engine.get_ppm_resumo(df_def_f, df_prod_f)
    ppm_vals = ppm_resumo_tmp.get("PPM", pd.Series(dtype=float)).replace([np.inf, -np.inf], np.nan).dropna()
    total_ppm_val = ppm_vals.mean() if not ppm_vals.empty else 0
    colk3.metric("PPM médio (visível)", f"{total_ppm_val:.2f}")
except Exception:
    colk3.metric("PPM médio (visível)", "--")

# ------------------ [BLOCK 8] - Tabelas Produção / Defeitos por modelo ------------------
st.subheader("📦 Produção por Categoria e Modelo — Resumo")
with st.expander("Ver tabela de produção por modelo (rolável)"):
    try:
        prod_por_modelo = (
            df_prod_f.groupby(["CATEGORIA", "MODELO"], as_index=False)
            .agg(QTY_GERAL=("QTY_GERAL", "sum"))
        )
    except Exception:
        prod_por_modelo = pd.DataFrame()
    st.dataframe(prod_por_modelo.fillna(0), use_container_width=True, height=300)

st.subheader("🔧 Defeitos por Modelo — Resumo")
with st.expander("Ver tabela de defeitos por modelo (rolável)"):
    try:
        def_por_modelo = (
            df_def_f.groupby(["CATEGORIA", "MODELO"], as_index=False)
            .agg(QTD_DEFEITOS=("ORDEM", "count"))
        )
    except Exception:
        def_por_modelo = pd.DataFrame()
    st.dataframe(def_por_modelo.fillna(0), use_container_width=True, height=300)

# ------------------ [BLOCK 9] - Relação Produção x Defeitos (PPM) — tabela e gráfico ------------------
st.subheader("🔁 Relação Produção x Defeitos (PPM)")
with st.expander("Gerar tabela PPM por modelo"):
    try:
        tabela_ppm = ppm_engine.gerar_tabela_ppm(df_def_f, df_prod_f)
    except Exception as e:
        st.error(f"Erro ao gerar tabela PPM: {e}")
        tabela_ppm = pd.DataFrame()

    # remover coluna MODELO_EXEMPLO se existir
    if "MODELO_EXEMPLO" in tabela_ppm.columns:
        tabela_ppm = tabela_ppm.drop(columns=["MODELO_EXEMPLO"])

    # garantir colunas DISPLAY (fallbacks)
    if "QTY_GERAL_DISPLAY" not in tabela_ppm.columns and "QTY_GERAL" in tabela_ppm.columns:
        tabela_ppm["QTY_GERAL_DISPLAY"] = tabela_ppm["QTY_GERAL"].apply(lambda x: f"{int(x)}" if pd.notna(x) and x > 0 else "Não contabilizado")
    if "PPM_DISPLAY" not in tabela_ppm.columns and "PPM" in tabela_ppm.columns:
        tabela_ppm["PPM_DISPLAY"] = tabela_ppm["PPM"].apply(lambda x: f"{x:,.2f}" if pd.notna(x) and x != 0 else "Não contabilizado")

    # preparar exibição
    cols_to_show = []
    for c in ["MODELO", "QTD_DEFEITOS", "QTY_GERAL_DISPLAY", "PPM_DISPLAY"]:
        if c in tabela_ppm.columns:
            cols_to_show.append(c)

    rename_map = {"QTY_GERAL_DISPLAY": "QTY_GERAL", "PPM_DISPLAY": "PPM"}
    tabela_ppm_display = tabela_ppm[cols_to_show].rename(columns=rename_map)

    # substituir NaN por "Não contabilizado" (apenas visual)
    tabela_ppm_display = tabela_ppm_display.fillna("Não contabilizado")

    st.dataframe(tabela_ppm_display, use_container_width=True, height=420)

    # gráfico barras top 20 PPM (quando numérico)
    try:
        # tentar converter PPM para num (quando possível)
        tabela_chart = tabela_ppm.copy()
        if "PPM" in tabela_chart.columns:
            tabela_chart = tabela_chart.sort_values("PPM", ascending=False).head(20)
            # gráfico simples via streamlit
            st.subheader("Top 20 modelos por PPM")
            st.bar_chart(tabela_chart.set_index("MODELO")["PPM"])
    except Exception:
        st.info("Gráfico PPM indisponível com os dados filtrados")

# ------------------ [BLOCK 10] - Exportações ------------------
st.subheader("⤓ Exportar")
col_exp1, col_exp2 = st.columns(2)
with col_exp1:
    if st.button("Exportar tabela PPM (CSV)"):
        st.download_button("Download PPM CSV", tabela_ppm.to_csv(index=False).encode("utf-8"), file_name="tabela_ppm.csv")
with col_exp2:
    if st.button("Exportar defeitos filtrados (CSV)"):
        st.download_button("Download Defeitos CSV", df_def_f.to_csv(index=False).encode("utf-8"), file_name="defeitos_filtrados.csv")

# ------------------ [BLOCK 11] - Observações e instruções ------------------
st.info("Página 7 — use os filtros na lateral para ajustar ano/mês/categoria/modelo. "
        "Itens marcados como 'NÃO CONTABILIZADO' aparecem na seção de auditoria, mas não na lista de 'sem produção'.")

# ------------------ FIM ------------------