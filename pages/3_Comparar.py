import streamlit as st
import plotly.graph_objects as go
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import database
from utils import sidebar_busca, LAYOUT_BASE

st.set_page_config(page_title="Comparar · Games Analytics", page_icon="⚔️", layout="wide")
sidebar_busca()

df = database.ler()
if df.empty:
    st.info("👈 Clique em Buscar dados das APIs para começar.")
    st.stop()

st.markdown('<h2 style="text-align:center;font-family:Orbitron;color:#c084fc;letter-spacing:3px;margin-bottom:24px;">⚔️ COMPARAR JOGOS</h2>', unsafe_allow_html=True)

nomes = df["nome"].tolist()

col1, col2 = st.columns(2)
with col1:
    jogo_a = st.selectbox("🎮 Jogo A", ["—"] + nomes, key="jogo_a")
with col2:
    jogo_b = st.selectbox("🎮 Jogo B", ["—"] + nomes, key="jogo_b")

if jogo_a == "—" or jogo_b == "—" or jogo_a == jogo_b:
    st.info("Selecione dois jogos diferentes para comparar.")
    st.stop()

ra = df[df["nome"] == jogo_a].iloc[0]
rb = df[df["nome"] == jogo_b].iloc[0]

st.divider()

# Cards lado a lado
card_a, card_mid, card_b = st.columns([5, 1, 5])

def render_card(col, row, cor):
    with col:
        st.markdown(f"""
        <div style="background:#1e293b;border-radius:12px;padding:20px;border:1px solid {cor};">
          <h3 style="color:{cor};font-family:Orbitron;font-size:1rem;margin-bottom:12px;">{row['nome']}</h3>
          <p style="color:#94a3b8;font-size:13px;margin:4px 0;"><b style="color:#e2e8f0;">Fonte:</b> {row['fonte']}</p>
          <p style="color:#94a3b8;font-size:13px;margin:4px 0;"><b style="color:#e2e8f0;">Gênero:</b> {row['genero']}</p>
          <p style="color:#94a3b8;font-size:13px;margin:4px 0;"><b style="color:#e2e8f0;">Jogadores:</b> {int(row['jogadores']):,}</p>
          <p style="color:#94a3b8;font-size:13px;margin:4px 0;"><b style="color:#e2e8f0;">Avaliação:</b> {row['avaliacao']:.1f}%</p>
        </div>""", unsafe_allow_html=True)
        if row.get("imagem_url"):
            st.image(row["imagem_url"], use_container_width=True)

render_card(card_a, ra, "#818cf8")
with card_mid:
    st.markdown("<div style='text-align:center;color:#c084fc;font-size:2rem;padding-top:60px;'>VS</div>", unsafe_allow_html=True)
render_card(card_b, rb, "#f472b6")

st.divider()

# Gráfico radar
categorias = ["Avaliação", "Jogadores (norm.)", "Popularidade"]

max_av  = df["avaliacao"].max() or 1
max_jog = df["jogadores"].max() or 1

vals_a = [
    ra["avaliacao"] / max_av * 100,
    ra["jogadores"] / max_jog * 100,
    (ra["avaliacao"] * 0.5 + ra["jogadores"] / max_jog * 50),
]
vals_b = [
    rb["avaliacao"] / max_av * 100,
    rb["jogadores"] / max_jog * 100,
    (rb["avaliacao"] * 0.5 + rb["jogadores"] / max_jog * 50),
]

fig = go.Figure()
fig.add_trace(go.Scatterpolar(r=vals_a + [vals_a[0]], theta=categorias + [categorias[0]],
                               fill="toself", name=jogo_a, line_color="#818cf8"))
fig.add_trace(go.Scatterpolar(r=vals_b + [vals_b[0]], theta=categorias + [categorias[0]],
                               fill="toself", name=jogo_b, line_color="#f472b6", opacity=0.7))
fig.update_layout(
    polar=dict(
        bgcolor="rgba(0,0,0,0)",
        radialaxis=dict(visible=True, range=[0, 100], color="#94a3b8"),
        angularaxis=dict(color="#94a3b8")
    ),
    paper_bgcolor="rgba(0,0,0,0)",
    font_color="#e2e8f0",
    title="📊 Comparação por métricas",
    title_font_size=18,
    showlegend=True,
    height=450
)
st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

# Tabela comparativa
st.divider()
st.subheader("📋 Tabela comparativa")
comp = {
    "Métrica":    ["Avaliação (%)", "Jogadores", "Gênero", "Fonte"],
    jogo_a:       [f"{ra['avaliacao']:.1f}%", f"{int(ra['jogadores']):,}", ra['genero'], ra['fonte']],
    jogo_b:       [f"{rb['avaliacao']:.1f}%", f"{int(rb['jogadores']):,}", rb['genero'], rb['fonte']],
}
import pandas as pd
st.dataframe(pd.DataFrame(comp), use_container_width=True, hide_index=True)

# Veredito
st.divider()
st.subheader("🏆 Veredito")
pontos_a = (ra["avaliacao"] / max_av) + (ra["jogadores"] / max_jog)
pontos_b = (rb["avaliacao"] / max_av) + (rb["jogadores"] / max_jog)
if pontos_a > pontos_b:
    st.success(f"🥇 **{jogo_a}** vence na combinação de avaliação e popularidade!")
elif pontos_b > pontos_a:
    st.success(f"🥇 **{jogo_b}** vence na combinação de avaliação e popularidade!")
else:
    st.info("🤝 Empate! Os dois jogos têm métricas equivalentes.")
