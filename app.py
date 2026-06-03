import streamlit as st

st.set_page_config(page_title="Games Analytics", page_icon="🎮", layout="wide")

def carregar_css():
    try:
        with open("assets/style.css", "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        pass

def carregar_banner():
    try:
        with open("assets/banner.html", "r", encoding="utf-8") as f:
            st.markdown(f.read(), unsafe_allow_html=True)
    except FileNotFoundError:
        pass

carregar_css()
carregar_banner()

import database
database.criar_banco()

st.markdown("""
<div style="text-align:center;padding:3rem 0 1rem;">
  <h1 style="font-size:2.5rem;font-family:Orbitron,sans-serif;color:#c084fc;letter-spacing:4px;">
    🎮 GAMES ANALYTICS
  </h1>
  <p style="color:#94a3b8;font-size:1.1rem;">
    Selecione uma página no menu lateral para começar.
  </p>
</div>
""", unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.page_link("pages/1_Dashboard.py",   label="📊 Dashboard",  icon="📊")
with col2:
    st.page_link("pages/2_Biblioteca.py",  label="🎮 Biblioteca", icon="🎮")
with col3:
    st.page_link("pages/3_Comparar.py",    label="⚔️ Comparar",   icon="⚔️")
with col4:
    st.page_link("pages/4_Historico.py",   label="📈 Histórico",  icon="📈")
