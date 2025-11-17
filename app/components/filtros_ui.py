"""
Componentes UI para filtros (sidebar).
Retorna um dict com o estado dos filtros.
"""
import streamlit as st
import pandas as pd
from datetime import datetime




def render_filtros_sidebar(df: pd.DataFrame) -> dict:
    state = {}


    # date range
    if "DATA" in df.columns:
        min_d = pd.to_datetime(df["DATA"]).min()
        max_d = pd.to_datetime(df["DATA"]).max()
        dr = st.sidebar.date_input("Período", value=(min_d, max_d))
        # dr pode ser date ou tuple
        if isinstance(dr, tuple) and len(dr) == 2:
            state["date_range"] = (pd.to_datetime(dr[0]), pd.to_datetime(dr[1]))
        else:
            state["date_range"] = None


    # categoria
    cats = ["Todos"] + sorted(df["CATEGORIA"].dropna().unique().tolist()) if "CATEGORIA" in df.columns else ["Todos"]
    state["CATEGORIA"] = st.sidebar.selectbox("Categoria", cats)


    # modelo
    modelos = ["Todos"] + sorted(df["MODELO_ID"].dropna().unique().tolist()) if "MODELO_ID" in df.columns else ["Todos"]
    state["MODELO_ID"] = st.sidebar.selectbox("Modelo", modelos)


    # turno
    turnos = ["Todos"] + sorted(df["TURNO"].dropna().unique().tolist()) if "TURNO" in df.columns else ["Todos"]
    state["TURNO"] = st.sidebar.selectbox("Turno", turnos)


    # cod_falha
    cods = ["Todos"] + sorted(df["COD_FALHA"].dropna().unique().tolist()) if "COD_FALHA" in df.columns else ["Todos"]
    state["COD_FALHA"] = st.sidebar.selectbox("Código Falha", cods)

    return state