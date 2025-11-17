"""
Funções de plot com plotly. Mantemos dependência leve.
"""
import plotly.express as px
import pandas as pd
import streamlit as st




def plot_bar_categories(df_top: pd.DataFrame):
    fig = px.bar(df_top, x="CATEGORIA", y="COUNT", text="COUNT", orientation="v")
    fig.update_layout(margin=dict(t=10,b=20,l=10,r=10), height=360)
    st.plotly_chart(fig, use_container_width=True)




def plot_model_heatmap(df: pd.DataFrame, group_by: str = "MODELO_ID", period: str = "MES_CORR"):
    # pivot tabela: modelos x period -> count
    tab = df.groupby([group_by, period]).size().reset_index(name="COUNT")
    pivot = tab.pivot(index=group_by, columns=period, values="COUNT").fillna(0)
    fig = px.imshow(pivot.values, x=pivot.columns, y=pivot.index, aspect="auto", labels=dict(x=period, y=group_by, color="COUNT"))
    fig.update_layout(height=500, margin=dict(t=20,b=20,l=80,r=20))
    return fig




def plot_time_series(df: pd.DataFrame, period: str = "MES_CORR", category_col: str = "CATEGORIA"):
    tab = df.groupby([period, category_col]).size().reset_index(name="COUNT")
    fig = px.line(tab, x=period, y="COUNT", color=category_col)
    fig.update_layout(height=420)
    return fig




def plot_heatmap(df: pd.DataFrame, x: str, y: str):
    tab = df.groupby([x, y]).size().reset_index(name="COUNT")
    pivot = tab.pivot(index=y, columns=x, values="COUNT").fillna(0)
    fig = px.imshow(pivot.values, x=pivot.columns, y=pivot.index, labels=dict(x=x, y=y, color="COUNT"))
    fig.update_layout(height=520)
    return fig