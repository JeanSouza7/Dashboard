import streamlit as st
import pandas as pd
import plotly.express as px
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import database
from utils import sidebar_busca, LAYOUT_BASE

st.set_page_config(page_title="Histórico · Games Analytics", page_icon="📈", layout="wide")
sidebar_busca()

st.subheader("📈 Histórico de buscas ao longo do tempo")
df_hist = database.ler_historico()

if df_hist.empty:
    st.info("Ainda sem histórico. Faça algumas buscas ao longo dos dias para ver a evolução.")
    st.stop()

df_hist["data"] = pd.to_datetime(df_hist["data"])

fig1 = px.line(df_hist, x="data", y="total", color="fonte",
               title="📦 Total de jogos coletados por dia",
               labels={"data":"Data","total":"Jogos","fonte":"Fonte"}, markers=True)
fig1.update_layout(**LAYOUT_BASE, height=380)
st.plotly_chart(fig1, use_container_width=True, config={"displayModeBar": False})

c1, c2 = st.columns(2)
with c1:
    fig2 = px.line(df_hist[df_hist["media_avaliacao"] > 0], x="data", y="media_avaliacao", color="fonte",
                   title="⭐ Avaliação média ao longo do tempo", markers=True)
    fig2.update_layout(**LAYOUT_BASE, height=350)
    st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})
with c2:
    fig3 = px.line(df_hist[df_hist["media_jogadores"] > 0], x="data", y="media_jogadores", color="fonte",
                   title="👥 Média de jogadores ao longo do tempo", markers=True)
    fig3.update_layout(**LAYOUT_BASE, height=350)
    st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False})

st.divider()
df_show = df_hist.copy()
df_show["data"] = df_show["data"].dt.strftime("%d/%m/%Y")
df_show = df_show[["data","fonte","total","media_avaliacao","media_jogadores"]]
df_show.columns = ["Data","Fonte","Total","Av. Média (%)","Jog. Médios"]
st.dataframe(df_show, use_container_width=True, hide_index=True)
