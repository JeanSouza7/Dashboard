"""Utilitários compartilhados entre todas as páginas."""
import streamlit as st
import database
import apis
from datetime import datetime


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

LAYOUT_BASE = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font_color="#e2e8f0",
    title_font_size=18,
    margin=dict(t=50, b=20, l=20, r=20),
    xaxis=dict(showgrid=False, zeroline=False),
    yaxis=dict(showgrid=False, zeroline=False),
)

@st.cache_data(ttl=3600, show_spinner=False)
def buscar_e_salvar():
    resultados = apis.buscar_tudo()
    total = 0
    for fonte, df_api in resultados.items():
        if not df_api.empty:
            database.salvar(df_api, fonte)
            total += len(df_api)
    # Enriquece gêneros UMA vez, depois de todas as fontes estarem salvas
    database.enriquecer_generos()
    return total, datetime.now().strftime("%H:%M")


def sidebar_busca():
    st.sidebar.title("🎮 Games Analytics")
    st.sidebar.markdown("---")
    if st.sidebar.button("🔄 Buscar dados das APIs", use_container_width=True):
        buscar_e_salvar.clear()
        with st.spinner("Buscando dados..."):
            total, hora = buscar_e_salvar()
        st.sidebar.success(f"✅ {total} jogos salvos às {hora}")
    else:
        try:
            _, hora = buscar_e_salvar()
            st.sidebar.caption(f"Última busca: {hora}")
        except Exception:
            pass
    st.sidebar.markdown("---")
