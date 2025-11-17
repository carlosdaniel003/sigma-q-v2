import streamlit as st

def card_principal(titulo: str, valor: str, cor: str = "#4CAF50", icone: str = "🔧"):
    """
    Exibe um card visual padrão SIGMA-Q V2.
    
    Parâmetros:
    - titulo: texto pequeno acima
    - valor: destaque principal
    - cor: cor da borda esquerda (hex)
    - icone: emoji opcional
    """

    st.markdown(f"""
        <div style="
            background-color: #1E1E1E;
            padding: 1.2rem;
            border-radius: 12px;
            border-left: 12px solid {cor};
            margin-top: 0.5rem;
            margin-bottom: 1rem;
            box-shadow: 0px 0px 8px rgba(0,0,0,0.25);
        ">
            <div style="font-size: 0.9rem; color: #BBBBBB; margin-bottom: 0.4rem;">
                {icone} {titulo}
            </div>

            <div style="font-size: 1.8rem; font-weight: bold; color: white;">
                {valor}
            </div>
        </div>
    """, unsafe_allow_html=True)
