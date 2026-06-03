import streamlit as st
import pandas as pd
import io
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import database
from utils import sidebar_busca, carregar_css, carregar_banner

st.set_page_config(page_title="Biblioteca · Games Analytics", page_icon="🎮", layout="wide")
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

ordem = st.sidebar.selectbox("🔽 Ordenar por", ["Jogadores", "Avaliação", "Nome"])
mapa  = {"Jogadores": "jogadores", "Avaliação": "avaliacao", "Nome": "nome"}
df    = df.sort_values(mapa[ordem], ascending=(ordem == "Nome")).reset_index(drop=True)

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



st.markdown('<h2 style="text-align:center;font-family:Orbitron;color:#c084fc;letter-spacing:3px;margin-bottom:20px;">🎮 GAME LIBRARY</h2>', unsafe_allow_html=True)

busca = st.text_input("🔎 Buscar pelo nome:", placeholder="Ex: Dota, Counter-Strike...")
if busca:
    df = df[df["nome"].str.contains(busca, case=False, na=False)]

POR_PAGINA = 50
total_pags = max(1, (len(df) - 1) // POR_PAGINA + 1)
_, col_p, _ = st.columns([2, 1, 2])
with col_p:
    pagina = st.number_input("Página", min_value=1, max_value=total_pags, value=1, step=1)
inicio   = (pagina - 1) * POR_PAGINA
df_pag   = df.iloc[inicio: inicio + POR_PAGINA]
st.caption(f"Mostrando {inicio+1}–{min(inicio+POR_PAGINA, len(df))} de {len(df)} jogos · Página {pagina}/{total_pags}")

modo = st.radio("Visualização", ["📋 Tabela", "🖼️ Cards"], horizontal=True)

if modo == "📋 Tabela":
    df_show = df_pag[["nome","jogadores","avaliacao","genero","fonte"]].copy()
    df_show.columns = ["Nome","Jogadores","Avaliação (%)","Gênero","Fonte"]
    df_show.index = range(inicio+1, inicio+1+len(df_show))
    styled = (df_show.style
        .set_properties(**{"background-color":"#0f172a","color":"white","border-color":"#1e293b","font-size":"14px"})
        .set_table_styles([
            {"selector":"thead th","props":[("background","linear-gradient(90deg,#2563eb,#7c3aed)"),("color","white"),("font-weight","bold")]},
            {"selector":"tr:hover","props":[("background-color","#312e81")]}
        ]))
    st.dataframe(styled, use_container_width=True, height=600, hide_index=True)
else:
    cols = st.columns(4)
    for i, (_, row) in enumerate(df_pag.iterrows()):
        with cols[i % 4]:
            if row.get("imagem_url"):
                st.image(row["imagem_url"], use_container_width=True)
            av  = row["avaliacao"]
            cor = "#22c55e" if av >= 75 else "#f59e0b" if av >= 50 else "#94a3b8"
            st.markdown(f"""<div style="padding:4px 0 12px;">
              <div style="font-size:13px;font-weight:600;color:#e2e8f0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;" title="{row['nome']}">{row['nome']}</div>
              <div style="font-size:11px;color:#94a3b8;">{row['genero']} · {row['fonte']}</div>
              {"" if av==0 else f'<div style="font-size:12px;color:{cor};font-weight:600;">⭐ {av:.1f}%</div>'}
            </div>""", unsafe_allow_html=True)

st.divider()

st.subheader("🔎 Detalhes de um jogo")
jogo_sel = st.selectbox("Selecione:", ["—"] + df["nome"].tolist())
if jogo_sel != "—":
    row = df[df["nome"] == jogo_sel].iloc[0]
    dc1, dc2 = st.columns([1, 2])
    with dc1:
        if row.get("imagem_url"):
            st.image(row["imagem_url"], use_container_width=True)
    with dc2:
        st.markdown(f"### {row['nome']}")
        st.markdown(f"**Fonte:** {row['fonte']}  |  **Gênero:** {row['genero']}")
        if row["jogadores"] > 0:
            st.markdown(f"**Jogadores:** {int(row['jogadores']):,}")
        if row["avaliacao"] > 0:
            st.markdown(f"**Avaliação:** {row['avaliacao']:.1f}%")
            st.progress(int(row["avaliacao"]) / 100)

        fav = database.is_favorito(row["nome"])
        if fav:
            if st.button("💔 Remover dos favoritos"):
                database.desfavoritar(row["nome"])
                st.rerun()
        else:
            if st.button("⭐ Adicionar aos favoritos"):
                database.favoritar(row["nome"], row["fonte"], row["genero"],
                                   row["avaliacao"], row.get("imagem_url",""))
                st.success("Adicionado aos favoritos!")
                st.rerun()

        similares = df[(df["genero"].str.contains(row["genero"].split(",")[0], na=False)) & (df["nome"] != row["nome"])].head(5)
        if not similares.empty:
            st.markdown("**Jogos similares:**")
            for _, r2 in similares.iterrows():
                st.caption(f"• {r2['nome']} ({r2['fonte']})")


st.subheader("📤 Exportar dados")
df_exp = df[["nome","jogadores","avaliacao","genero","fonte"]].copy()
df_exp.columns = ["Nome","Jogadores","Avaliacao_pct","Genero","Fonte"]
ec1, ec2, ec3 = st.columns(3)
with ec1:
    st.download_button("⬇️ CSV", df_exp.to_csv(index=False).encode("utf-8"), "jogos.csv", "text/csv", use_container_width=True)
with ec2:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        df_exp.to_excel(w, index=False, sheet_name="Jogos")
    st.download_button("⬇️ Excel", buf.getvalue(), "jogos.xlsx",
                       "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
with ec3:
    st.download_button("⬇️ JSON", df_exp.to_json(orient="records", force_ascii=False, indent=2).encode("utf-8"),
                       "jogos.json", "application/json", use_container_width=True)
