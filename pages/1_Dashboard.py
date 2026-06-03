import streamlit as st
import pandas as pd
import plotly.express as px
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import database
from utils import sidebar_busca, LAYOUT_BASE, carregar_css, carregar_banner

st.set_page_config(page_title="Dashboard · Games Analytics", page_icon="🎮", layout="wide")
sidebar_busca()
carregar_css()
carregar_banner()

df = database.ler()
df["genero"] = df["genero"].fillna("N/A").astype(str).str.strip()

if df.empty:
    st.info("👈 Clique em Buscar dados das APIs para começar.")
    st.stop()

fontes_sel = st.sidebar.multiselect("📡 Fontes", df["fonte"].unique(), default=df["fonte"].unique())
df = df[df["fonte"].isin(fontes_sel)]

todos_generos = sorted({g.strip() for lista in df["genero"].dropna() for g in str(lista).split(",") if g.strip()})
gen_sel = st.sidebar.selectbox("🎮 Gênero", ["Todos"] + todos_generos)
if gen_sel != "Todos":
    df = df[df["genero"].str.contains(rf"\b{gen_sel}\b", case=False, na=False, regex=True)]

fontes_av = ["SteamSpy", "RAWG", "IGDB"]
if any(f in fontes_av for f in fontes_sel) and not df.empty:
    max_av = int(df["avaliacao"].max())
    if max_av > 0:
        nota_min = st.sidebar.slider("⭐ Avaliação mínima", 0, max_av, 0)
        if nota_min > 0:
            df = df[(~df["fonte"].isin(fontes_av)) | (df["avaliacao"] >= nota_min)]


fontes_jog = ["SteamSpy", "RAWG", "IGDB"]
if any(f in fontes_jog for f in fontes_sel) and not df.empty:
    max_jog = int(df["jogadores"].max())
    if max_jog > 0:
        min_jog = st.sidebar.slider("👥 Jogadores mínimos", 0, max_jog, 0)
        if min_jog > 0:
            df = df[(~df["fonte"].isin(fontes_jog)) | (df["jogadores"] >= min_jog)]

with st.sidebar.expander("🔍 Filtros avançados"):
    if not df.empty and df["avaliacao"].max() > 0:
        av_range = st.slider("Faixa de avaliação", 0, 100, (0, 100), key="av_range")
        df = df[(df["avaliacao"] == 0) | (df["avaliacao"].between(av_range[0], av_range[1]))]
    multiplas = st.checkbox("Apenas jogos em múltiplas fontes")
    if multiplas:
        nomes_multi = df.groupby("nome")["fonte"].nunique()
        df = df[df["nome"].isin(nomes_multi[nomes_multi > 1].index)]

ordem = st.sidebar.selectbox("🔽 Ordenar por", ["Jogadores", "Avaliação", "Nome"])
mapa  = {"Jogadores": "jogadores", "Avaliação": "avaliacao", "Nome": "nome"}
df    = df.sort_values(mapa[ordem], ascending=(ordem == "Nome")).reset_index(drop=True)

c1, c2, c3, c4 = st.columns(4)
with c1: st.markdown(f'<div class="metric-card blue"><div class="metric-title">🎮 TOTAL</div><div class="metric-value">{len(df):,}</div></div>', unsafe_allow_html=True)
with c2: st.markdown(f'<div class="metric-card cyan"><div class="metric-title">👥 MÁX. JOGADORES</div><div class="metric-value">{df["jogadores"].max():,}</div></div>', unsafe_allow_html=True)
with c3: st.markdown(f'<div class="metric-card yellow"><div class="metric-title">⭐ AV. MÉDIA</div><div class="metric-value">{df["avaliacao"].mean():.1f}%</div></div>', unsafe_allow_html=True)
with c4: st.markdown(f'<div class="metric-card green"><div class="metric-title">🏆 FONTES</div><div class="metric-value">{df["fonte"].nunique()}</div></div>', unsafe_allow_html=True)

st.divider()

_pie = dict(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="white",
            margin=dict(t=60,b=20,l=20,r=20), legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="white")))

col_a, col_b = st.columns(2)
with col_a:
    df_jog = df[df["jogadores"] > 0].nlargest(10, "jogadores")
    if not df_jog.empty:
        fig = px.bar(df_jog, x="jogadores", y="nome", orientation="h", title="👥 Top 10 por Jogadores",
                     color="jogadores", color_continuous_scale="purples")
        fig.update_layout(**LAYOUT_BASE, height=420)
        fig.update_layout(yaxis={"categoryorder": "total ascending"}, showlegend=False)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

with col_b:
    df_av = df[df["avaliacao"] > 0].nlargest(10, "avaliacao")
    if not df_av.empty:
        fig2 = px.bar(df_av, x="avaliacao", y="nome", orientation="h", title="⭐ Top 10 por Avaliação",
                      color="avaliacao", color_continuous_scale="Blues")
        fig2.update_layout(**LAYOUT_BASE, height=420)
        fig2.update_layout(yaxis={"categoryorder": "total ascending"}, showlegend=False)
        st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

col_c, col_d = st.columns(2)
with col_c:

    df_gen = (
        df["genero"].dropna().str.split(",").explode()
        .str.strip().replace("", pd.NA).dropna()
        .value_counts().reset_index()
    )
    df_gen.columns = ["genero", "quantidade"]
    total = df_gen["quantidade"].sum()
    threshold = 0.02 
    mask_outros = (df_gen["quantidade"] / total) < threshold
    if mask_outros.any():
        outros_soma = df_gen.loc[mask_outros, "quantidade"].sum()
        df_gen = df_gen[~mask_outros]
        if "Outros" in df_gen["genero"].values:
            df_gen.loc[df_gen["genero"] == "Outros", "quantidade"] += outros_soma
        else:
            df_gen = pd.concat([df_gen, pd.DataFrame([{"genero": "Outros", "quantidade": outros_soma}])], ignore_index=True)
    df_gen = df_gen.sort_values("quantidade", ascending=False)
    fig3 = px.pie(df_gen, names="genero", values="quantidade", title="🕹️ Por Gênero", hole=0.55)
    fig3.update_traces(textfont_color="white", marker=dict(line=dict(color="#0f172a", width=2)))
    fig3.update_layout(**_pie)
    st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False})

with col_d:
    df_fo = df["fonte"].value_counts().reset_index(); df_fo.columns = ["fonte","quantidade"]
    fig4 = px.pie(df_fo, names="fonte", values="quantidade", title="📡 Por Fonte", hole=0.55)
    fig4.update_traces(textfont_color="white", marker=dict(line=dict(color="#0f172a", width=2)))
    fig4.update_layout(**_pie)
    st.plotly_chart(fig4, use_container_width=True, config={"displayModeBar": False})

st.divider()
df_sc = df[(df["jogadores"] > 0) & (df["avaliacao"] > 0)].copy()
if not df_sc.empty:
    import numpy as np
    def normalizar_por_fonte(grupo):
        mn, mx = grupo.min(), grupo.max()
        return (grupo - mn) / (mx - mn) if mx > mn else grupo * 0
    df_sc["_size"] = (
        df_sc.groupby("fonte")["jogadores"]
        .transform(normalizar_por_fonte)
        .pipe(np.cbrt) + 0.1
    )

    fig5 = px.scatter(
        df_sc, x="jogadores", y="avaliacao",
        color="fonte", hover_name="nome",
        size="_size", size_max=18,
        hover_data={"jogadores": True, "avaliacao": True, "_size": False, "genero": True},
        title="🔵 Jogadores vs Avaliação",
        opacity=0.8,
        labels={"jogadores": "Jogadores", "avaliacao": "Avaliação", "fonte": "Fonte"},
    )

    fig5.update_xaxes(type="log", title="Jogadores (escala log)")
    fig5.update_yaxes(title="Avaliação")
    fig5.update_traces(marker=dict(line=dict(width=0.5, color="rgba(255,255,255,0.3)")))
    fig5.update_layout(**LAYOUT_BASE, height=470, legend=dict(
        orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
    ))
    st.plotly_chart(fig5, use_container_width=True, config={"displayModeBar": False})

col_e, col_f = st.columns(2)
with col_e:

    df_exp = df[df["avaliacao"]>0].copy()
    df_exp = df_exp.assign(genero=df_exp["genero"].str.split(",")).explode("genero")
    df_exp["genero"] = df_exp["genero"].str.strip()
    df_ga = df_exp.groupby("genero")["avaliacao"].mean().round(1).sort_values(ascending=False).head(10).reset_index()
    if not df_ga.empty:
        fig6 = px.bar(df_ga, x="avaliacao", y="genero", orientation="h", title="🏅 Top Gêneros por Avaliação",
                      color="avaliacao", color_continuous_scale="teal")
        fig6.update_layout(**LAYOUT_BASE, height=380)
        fig6.update_layout(yaxis={"categoryorder":"total ascending"}, showlegend=False)
        st.plotly_chart(fig6, use_container_width=True, config={"displayModeBar": False})

with col_f:
    df_exp2 = df[df["jogadores"]>0].copy()
    df_exp2 = df_exp2.assign(genero=df_exp2["genero"].str.split(",")).explode("genero")
    df_exp2["genero"] = df_exp2["genero"].str.strip()
    df_gj = df_exp2.groupby("genero")["jogadores"].sum().sort_values(ascending=False).head(10).reset_index()
    if not df_gj.empty:
        fig7 = px.bar(df_gj, x="jogadores", y="genero", orientation="h", title="👥 Top Gêneros por Jogadores",
                      color="jogadores", color_continuous_scale="magenta")
        fig7.update_layout(**LAYOUT_BASE, height=380)
        fig7.update_layout(yaxis={"categoryorder":"total ascending"}, showlegend=False)
        st.plotly_chart(fig7, use_container_width=True, config={"displayModeBar": False})