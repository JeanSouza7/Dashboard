
import streamlit as st
import pandas as pd
import plotly.express as px

import database
import apis


st.set_page_config(page_title="Games Dashboard", page_icon="🎮", layout="wide")
# =========================
# CUSTOMIZAÇÃO DE CORES
# =========================
st.markdown("""
<style>

/* Tags do multiselect */
.stMultiSelect [data-baseweb="tag"] {
    background-color: #3b82f6 !important; /* azul */
    color: white !important;
    border-radius: 8px !important;
}

/* X do botão */
.stMultiSelect [data-baseweb="tag"] svg {
    fill: white !important;
}

/* Slider */
.stSlider div[data-baseweb="slider"] div {
    color: #3b82f6 !important;
}

/* Bolinha do slider */
.stSlider [role="slider"] {
    background-color: #3b82f6 !important;
}

/* Barra preenchida */
.stSlider div[data-testid="stTickBar"] div {
    background-color: #3b82f6 !important;
}

</style>
""", unsafe_allow_html=True)
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
# Limpeza dos gêneros
df["genero"] = (
    df["genero"]
    .fillna("N/A")
    .astype(str)
    .str.strip()
)

st.title("🎮 Games Dashboard")
st.caption("Dados de jogos obtidos via APIs públicas e armazenados localmente.")
st.divider()

if df.empty:
    st.info("👈 Clique em **Buscar dados das APIs** na barra lateral para começar.")
    st.stop()


st.sidebar.header("🎯 Filtros")
# =========================
# FONTES
# =========================

fontes_sel = st.sidebar.multiselect(
    "📡 Fontes",
    df["fonte"].unique(),
    default=df["fonte"].unique()
)

df = df[df["fonte"].isin(fontes_sel)]
# =========================
# GÊNERO
# =========================

# =========================
# GÊNERO
# =========================

# Separar gêneros compostos
todos_generos = set()

for lista in df["genero"].dropna():

    for g in str(lista).split(","):

        g = g.strip()

        if g:
            todos_generos.add(g)

generos = sorted(todos_generos)

gen_sel = st.sidebar.selectbox(
    "🎮 Gênero",
    ["Todos"] + generos
)

if gen_sel != "Todos":

    if gen_sel == "N/A":
        df = df[df["genero"] == "N/A"]

    else:
        df = df[
            df["genero"].str.contains(
                rf"\b{gen_sel}\b",
                case=False,
                na=False,
                regex=True
            )
        ]
# =========================
# AVALIAÇÃO
# =========================

fontes_com_avaliacao = ["SteamSpy", "RAWG"]

mostrar_avaliacao = any(
    fonte in fontes_com_avaliacao
    for fonte in fontes_sel
)

if mostrar_avaliacao and not df.empty:

    max_av = int(df["avaliacao"].max())

    if max_av > 0:

        nota_min = st.sidebar.slider(
            "⭐ Avaliação mínima",
            min_value=0,
            max_value=max_av,
            value=0
        )

        if nota_min > 0:
            df = df[
                (~df["fonte"].isin(fontes_com_avaliacao)) |
                (df["avaliacao"] >= nota_min)
            ]

# =========================
# JOGADORES
# =========================
fontes_com_jogadores = ["SteamSpy", "RAWG"]

mostrar_jogadores = any(
    fonte in fontes_com_jogadores
    for fonte in fontes_sel
)

if mostrar_jogadores and not df.empty:

    max_jog = int(df["jogadores"].max())

    # Evita erro do slider
    if max_jog > 0:

        min_jog = st.sidebar.slider(
            "👥 Jogadores mínimos",
            min_value=0,
            max_value=max_jog,
            value=0
        )

        if min_jog > 0:
            df = df[
                (~df["fonte"].isin(fontes_com_jogadores)) |
                (df["jogadores"] >= min_jog)
            ]

# =========================
# ORDENAÇÃO
# =========================

ordem = st.sidebar.selectbox(
    "🔽 Ordenar por",
    ["Jogadores", "Avaliação", "Nome"]
)

if ordem == "Jogadores":
    df = df.sort_values("jogadores", ascending=False)

elif ordem == "Avaliação":
    df = df.sort_values("avaliacao", ascending=False)

else:
    df = df.sort_values("nome")

df = df.reset_index(drop=True)


if ordem == "Jogadores":
    df = df.sort_values("jogadores", ascending=False)

elif ordem == "Avaliação":
    df = df.sort_values("avaliacao", ascending=False)

else:
    df = df.sort_values("nome")

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
