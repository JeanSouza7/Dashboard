
import streamlit as st
import pandas as pd
import plotly.express as px

import database
import apis

st.set_page_config(page_title="Games Analytics", page_icon="🎮", layout="wide")
def carregar_css():
    with open("assets/style.css", "r", encoding="utf-8") as f:
        css = f.read()

    st.markdown(
        f"<style>{css}</style>",
        unsafe_allow_html=True
    )

def carregar_banner():
    with open("assets/banner.html", "r", encoding="utf-8") as f:
        html = f.read()

    st.markdown(
        html,
        unsafe_allow_html=True
    )


carregar_css()
carregar_banner()

database.criar_banco()

st.sidebar.title("🎮 Games Analytics")
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

df["genero"] = (
    df["genero"]
    .fillna("N/A")
    .astype(str)
    .str.strip()
)


st.divider()

if df.empty:
    st.info("👈 Clique em **Buscar dados das APIs** na barra lateral para começar.")
    st.stop()


st.sidebar.header("🎯 Filtros")

fontes_sel = st.sidebar.multiselect(
    "📡 Fontes",
    df["fonte"].unique(),
    default=df["fonte"].unique()
)

df = df[df["fonte"].isin(fontes_sel)]

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

fontes_com_jogadores = ["SteamSpy", "RAWG"]

mostrar_jogadores = any(
    fonte in fontes_com_jogadores
    for fonte in fontes_sel
)

if mostrar_jogadores and not df.empty:

    max_jog = int(df["jogadores"].max())

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

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f'''
    <div class="metric-card blue">
        <div class="metric-title">🎮 TOTAL DE JOGOS</div>
        <div class="metric-value">{len(df):,}</div>
    </div>
    ''', unsafe_allow_html=True)

with col2:
    st.markdown(f'''
    <div class="metric-card cyan">
        <div class="metric-title">👥 MÁX. JOGADORES</div>
        <div class="metric-value">{df['jogadores'].max():,}</div>
    </div>
    ''', unsafe_allow_html=True)

with col3:
    st.markdown(f'''
    <div class="metric-card yellow">
        <div class="metric-title">⭐ AVALIAÇÃO MÉDIA</div>
        <div class="metric-value">{df['avaliacao'].mean():.1f}%</div>
    </div>
    ''', unsafe_allow_html=True)

with col4:
    st.markdown(f'''
    <div class="metric-card green">
        <div class="metric-title">🏆 FONTES ATIVAS</div>
        <div class="metric-value">{df['fonte'].nunique()}</div>
    </div>
    ''', unsafe_allow_html=True)

st.divider()

col_a, col_b = st.columns(2)

with col_a:
    df_jog = df[df["jogadores"] > 0].nlargest(10, "jogadores")
    if not df_jog.empty:
        fig = px.bar(
            df_jog, x="jogadores", y="nome", orientation="h",
            title="👥 Top 10 por Jogadores",
            labels={"jogadores": "Jogadores", "nome": "Jogo"},
            color="jogadores", color_continuous_scale="purples"
        )
        fig.update_layout(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font_color="#e2e8f0",
    title_font_size=22,
    height=420,

    xaxis=dict(
        showgrid=False,
        zeroline=False
    ),

    yaxis=dict(
        showgrid=False,
        zeroline=False
    )
)
        
        fig.update_layout(yaxis={"categoryorder": "total ascending"}, showlegend=False)
        st.plotly_chart(
    fig,
    use_container_width=True,
    config={"displayModeBar": False}
)
    else:
        st.info("Sem dados de jogadores para esta fonte.")

with col_b:
    df_av = df[df["avaliacao"] > 0].nlargest(10, "avaliacao")
    if not df_av.empty:
        fig2 = px.bar(
            df_av, x="avaliacao", y="nome", orientation="h",
            title="⭐ Top 10 por Avaliação (%)",
            labels={"avaliacao": "Avaliação (%)", "nome": "Jogo"},
            color="avaliacao", color_continuous_scale="Blues"
        )
        fig2.update_layout(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font_color="#e2e8f0",
    title_font_size=22,
    height=420,

    xaxis=dict(
        showgrid=False,
        zeroline=False
    ),

    yaxis=dict(
        showgrid=False,
        zeroline=False
    )
    
)
        
        fig2.update_layout(yaxis={"categoryorder": "total ascending"}, showlegend=False)
        st.plotly_chart(
    fig2,
    use_container_width=True,
    config={"displayModeBar": False}
)
    else:
        st.info("Sem dados de avaliação para esta fonte.")

col_c, col_d = st.columns(2)

with col_c:

    df_gen = df["genero"].value_counts().reset_index()
    df_gen.columns = ["genero", "quantidade"]

    fig3 = px.pie(
        df_gen,
        names="genero",
        values="quantidade",
        title="🕹️ Distribuição por Gênero",
        hole=0.55
    )

    fig3.update_traces(
        textfont_color="white",
        marker=dict(
            line=dict(color="#0f172a", width=2)
        )
    )

    fig3.update_layout(

        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",

        font_color="white",

        margin=dict(t=60, b=20, l=20, r=20),

        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            font=dict(color="white")
        )
    )

    st.plotly_chart(
        fig3,
        use_container_width=True,
        config={"displayModeBar": False}
    )


with col_d:

    df_fonte = df["fonte"].value_counts().reset_index()
    df_fonte.columns = ["fonte", "quantidade"]

    fig4 = px.pie(
        df_fonte,
        names="fonte",
        values="quantidade",
        title="📡 Distribuição por Fonte",
        hole=0.55
    )

    fig4.update_traces(
        textfont_color="white",
        marker=dict(
            line=dict(color="#0f172a", width=2)
        )
    )

    fig4.update_layout(

        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",

        font_color="white",

        margin=dict(t=60, b=20, l=20, r=20),

        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            font=dict(color="white")
        )
    )

    st.plotly_chart(
        fig4,
        use_container_width=True,
        config={"displayModeBar": False}
    )

st.divider()
st.markdown("""
<h2 style="
text-align:center;
font-family:Orbitron;
color:#c084fc;
letter-spacing:3px;
margin-bottom:20px;
">
🎮 GAME LIBRARY
</h2>
""", unsafe_allow_html=True)
st.subheader("📋 Tabela de Jogos")

busca = st.text_input("🔎 Buscar pelo nome:", placeholder="Ex: Dota, Counter-Strike...")
if busca:
    df = df[df["nome"].str.contains(busca, case=False, na=False)]

df_show = df[["nome", "jogadores", "avaliacao", "genero", "fonte"]].copy()
df_show.columns = ["Nome", "Jogadores", "Avaliação (%)", "Gênero", "Fonte"]
df_show.index = range(1, len(df_show) + 1)

styled_df = (
    df_show.style
    .set_properties(**{
        'background-color': '#0f172a',
        'color': 'white',
        'border-color': '#1e293b',
        'font-size': '14px'
    })
    .set_table_styles([
        {
            'selector': 'thead th',
            'props': [
                ('background', 'linear-gradient(90deg,#2563eb,#7c3aed)'),
                ('color', 'white'),
                ('font-size', '15px'),
                ('font-weight', 'bold'),
                ('text-transform', 'uppercase'),
                ('border', 'none')
            ]
        },
        {
            'selector': 'tr:hover',
            'props': [
                ('background-color', '#312e81')
            ]
        }
    ])
)

st.dataframe(
    styled_df,
    use_container_width=True,
    height=600,
    hide_index=True
)

csv = df_show.to_csv(index=False).encode("utf-8")
st.download_button("⬇️ Baixar CSV", csv, "jogos.csv", "text/csv")
