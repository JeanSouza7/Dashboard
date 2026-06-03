import streamlit as st
import sys, os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
import database

st.set_page_config(page_title="Games Analytics", page_icon="🎮", layout="wide")
database.criar_banco()

from utils import carregar_css, carregar_banner, sidebar_busca
sidebar_busca()
carregar_css()
carregar_banner()

df = database.ler()

if not df.empty:
    capas = (
        df[df["imagem_url"].str.startswith("http", na=False)]
        .drop_duplicates("nome")
        .head(24)["imagem_url"]
        .tolist()
    )
else:
    capas = []

imgs_html = "".join(f'<img src="{url}" onerror="this.style.display=\'none\'">' for url in capas)

st.markdown(f"""
<style>
.mosaic-wrap {{
    position: fixed;
    top: 0; left: 0;
    width: 100%; height: 100%;
    z-index: 0;
    pointer-events: none;
    overflow: hidden;
}}
.mosaic-grid {{
    display: grid;
    grid-template-columns: repeat(8, 1fr);
    gap: 4px;
    width: 100%;
    height: 100%;
}}
.mosaic-grid img {{
    width: 100%;
    height: 100%;
    object-fit: cover;
    opacity: 0.28;
    filter: saturate(0.7) brightness(0.6);
    transition: opacity 0.4s;
}}
.mosaic-overlay {{
    display: none;
}}
/* garante que o conteúdo do streamlit fica acima */
.block-container {{ position: relative; z-index: 2; }}
section[data-testid="stSidebar"] {{ z-index: 10; }}
.banner {{ position: relative; z-index: 2; }}
.nav-card {{ backdrop-filter: blur(2px); }}
</style>

<div class="mosaic-wrap">
  <div class="mosaic-grid">{imgs_html}</div>
</div>
<div class="mosaic-overlay"></div>
""", unsafe_allow_html=True)

if not capas:
    st.info("👈 Busque dados pelas APIs para ativar o mosaico de capas.")

st.markdown("""
<div class="nav-cards">
  <div class="nav-card">
    <div class="nav-card-icon">📊</div>
    <div class="nav-card-title">Dashboard</div>
    <div class="nav-card-desc">Visão geral com gráficos, rankings e métricas de todos os jogos indexados.</div>
  </div>
  <div class="nav-card">
    <div class="nav-card-icon">🎮</div>
    <div class="nav-card-title">Biblioteca</div>
    <div class="nav-card-desc">Explore, filtre e favorite jogos. Veja capas, avaliações e gêneros.</div>
  </div>
  <div class="nav-card">
    <div class="nav-card-icon">⚔️</div>
    <div class="nav-card-title">Comparar</div>
    <div class="nav-card-desc">Coloque jogos lado a lado e compare avaliações, popularidade e fontes.</div>
  </div>
</div>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)
with col1:
    if st.button("📊 Dashboard", use_container_width=True):
        st.switch_page("pages/1_Dashboard.py")
with col2:
    if st.button("🎮 Biblioteca", use_container_width=True):
        st.switch_page("pages/2_Biblioteca.py")
with col3:
    if st.button("⚔️ Comparar", use_container_width=True):
        st.switch_page("pages/3_Comparar.py")