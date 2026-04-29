
import streamlit as st
import pandas as pd
import plotly.express as px

import database
import apis


st.set_page_config(page_title="Games Dashboard", page_icon="🎮", layout="wide")


database.criar_banco()


st.sidebar.title("🎮 Games Dashboard")
st.sidebar.markdown("---")

if st.sidebar.button("🔄 Buscar dados das APIs", use_container_width=True):
    with st.spinner("Buscando dados..."):
        resultados = apis.buscar_tudo()
        total = 0
        for fonte, df in resultados.items():
            if not df.empty:
                database.salvar(df, fonte)
                total += len(df)
    st.sidebar.success(f"✅ {total} jogos salvos!")

st.sidebar.markdown("---")
st.sidebar.caption("Fontes: SteamSpy · RAWG · FreeToGame · CheapShark")

df = database.ler()

st.title("🎮 Games Dashboard")
st.caption("Dados de jogos obtidos via APIs públicas e armazenados localmente.")
st.divider()

if df.empty:
    st.info("👈 Clique em **Buscar dados das APIs** na barra lateral para começar.")
    st.stop()


fontes = ["Todas"] + sorted(df["fonte"].unique().tolist())
fonte_sel = st.selectbox("Filtrar por fonte:", fontes)

if fonte_sel != "Todas":
    df = df[df["fonte"] == fonte_sel]

df = df.reset_index(drop=True)

col1, col2, col3 = st.columns(3)
col1.metric("🎮 Total de Jogos", len(df))
col2.metric("👥 Máx. Jogadores", f"{df['jogadores'].max():,}")
col3.metric("⭐ Avaliação Média", f"{df['avaliacao'].mean():.1f}%")

st.divider()

col_a, col_b = st.columns(2)

with col_a:
    df_jog = df[df["jogadores"] > 0].nlargest(10, "jogadores")
    if not df_jog.empty:
        fig = px.bar(
            df_jog, x="jogadores", y="nome", orientation="h",
            title="👥 Top 10 por Jogadores",
            labels={"jogadores": "Jogadores", "nome": "Jogo"},
            color="jogadores", color_continuous_scale="Blues"
        )
        fig.update_layout(yaxis={"categoryorder": "total ascending"}, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Sem dados de jogadores para esta fonte.")

with col_b:
    df_av = df[df["avaliacao"] > 0].nlargest(10, "avaliacao")
    if not df_av.empty:
        fig2 = px.bar(
            df_av, x="avaliacao", y="nome", orientation="h",
            title="⭐ Top 10 por Avaliação (%)",
            labels={"avaliacao": "Avaliação (%)", "nome": "Jogo"},
            color="avaliacao", color_continuous_scale="Greens"
        )
        fig2.update_layout(yaxis={"categoryorder": "total ascending"}, showlegend=False)
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("Sem dados de avaliação para esta fonte.")

col_c, col_d = st.columns(2)

with col_c:
    df_gen = df["genero"].value_counts().reset_index()
    df_gen.columns = ["genero", "quantidade"]
    fig3 = px.pie(df_gen, names="genero", values="quantidade",
                  title="🕹️ Distribuição por Gênero", hole=0.4)
    st.plotly_chart(fig3, use_container_width=True)

with col_d:
    df_fonte = df["fonte"].value_counts().reset_index()
    df_fonte.columns = ["fonte", "quantidade"]
    fig4 = px.pie(df_fonte, names="fonte", values="quantidade",
                  title="📡 Distribuição por Fonte", hole=0.4)
    st.plotly_chart(fig4, use_container_width=True)

st.divider()

st.subheader("📋 Tabela de Jogos")

busca = st.text_input("🔎 Buscar pelo nome:", placeholder="Ex: Dota, Minecraft...")
if busca:
    df = df[df["nome"].str.contains(busca, case=False, na=False)]

df_show = df[["nome", "jogadores", "avaliacao", "genero", "fonte"]].copy()
df_show.columns = ["Nome", "Jogadores", "Avaliação (%)", "Gênero", "Fonte"]
df_show.index = range(1, len(df_show) + 1)

st.dataframe(df_show, use_container_width=True, height=380)

csv = df_show.to_csv(index=False).encode("utf-8")
st.download_button("⬇️ Baixar CSV", csv, "jogos.csv", "text/csv")
