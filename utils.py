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
    database.enriquecer_generos()
    return total, datetime.now().strftime("%H:%M")

def navbar():
    import streamlit as st
    try:
        current = st.query_params.get("page", "")
    except Exception:
        current = ""

    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&display=swap');

    .nav-wrapper {
        display: flex;
        justify-content: center;
        gap: 16px;
        padding: 14px 0 10px 0;
        margin-bottom: 8px;
    }

    .nav-item {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        gap: 6px;
        width: 160px;
        padding: 14px 10px;
        border-radius: 14px;
        background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%);
        border: 1px solid rgba(124, 58, 237, 0.25);
        cursor: pointer;
        text-decoration: none;
        position: relative;
        overflow: hidden;
        transition: transform 0.22s cubic-bezier(.22,.68,0,1.2),
                    border-color 0.22s ease,
                    box-shadow 0.22s ease;
    }

    .nav-item::before {
        content: "";
        position: absolute;
        inset: 0;
        background: linear-gradient(135deg, rgba(124,58,237,0.15), rgba(192,132,252,0.08));
        opacity: 0;
        transition: opacity 0.22s ease;
        border-radius: 14px;
    }

    .nav-item:hover {
        transform: translateY(-4px) scale(1.04);
        border-color: rgba(192, 132, 252, 0.7);
        box-shadow: 0 8px 32px rgba(124, 58, 237, 0.35),
                    0 0 0 1px rgba(192,132,252,0.2);
    }

    .nav-item:hover::before {
        opacity: 1;
    }

    .nav-item.active {
        border-color: #c084fc;
        background: linear-gradient(135deg, #1e1b4b 0%, #2e1065 100%);
        box-shadow: 0 0 24px rgba(192,132,252,0.3),
                    0 0 0 1px rgba(192,132,252,0.4);
    }

    .nav-icon {
        font-size: 22px;
        line-height: 1;
        filter: drop-shadow(0 0 6px rgba(192,132,252,0.5));
    }

    .nav-label {
        font-family: 'Orbitron', monospace;
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 2px;
        text-transform: uppercase;
        color: #c084fc;
        position: relative;
        z-index: 1;
    }

    .nav-item.active .nav-label {
        color: #e9d5ff;
    }

    .nav-divider {
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(124,58,237,0.4), transparent);
        margin: 0 0 20px 0;
    }
    </style>

    <div class="nav-wrapper">
        <a href="/" class="nav-item" target="_self">
            <div class="nav-icon">🏠</div>
            <div class="nav-label">Início</div>
        </a>
        <a href="/1_Dashboard" class="nav-item" target="_self">
            <div class="nav-icon">📊</div>
            <div class="nav-label">Dashboard</div>
        </a>
        <a href="/2_Biblioteca" class="nav-item" target="_self">
            <div class="nav-icon">🎮</div>
            <div class="nav-label">Biblioteca</div>
        </a>
        <a href="/3_Comparar" class="nav-item" target="_self">
            <div class="nav-icon">⚔️</div>
            <div class="nav-label">Comparar</div>
        </a>
    </div>
    <div class="nav-divider"></div>
    """, unsafe_allow_html=True)


def sidebar_busca():
    # Esconde a navegação nativa do Streamlit e injeta estilo customizado
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&display=swap');

    /* Esconde nav nativa */
    [data-testid="stSidebarNav"] { display: none !important; }

    /* Cards de navegação na sidebar */
    .sb-nav {
        display: flex;
        flex-direction: column;
        gap: 8px;
        margin: 4px 0 16px 0;
    }
    .sb-nav-item {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 12px 14px;
        border-radius: 10px;
        background: linear-gradient(135deg, #0f172a, #1e1b4b);
        border: 1px solid rgba(124,58,237,0.2);
        text-decoration: none;
        cursor: pointer;
        transition: transform 0.18s cubic-bezier(.22,.68,0,1.2),
                    border-color 0.18s ease,
                    box-shadow 0.18s ease,
                    background 0.18s ease;
        position: relative;
        overflow: hidden;
    }
    .sb-nav-item::after {
        content: "";
        position: absolute;
        left: 0; top: 0; bottom: 0;
        width: 3px;
        background: linear-gradient(180deg, #7c3aed, #c084fc);
        border-radius: 0 3px 3px 0;
        opacity: 0;
        transition: opacity 0.18s ease;
    }
    .sb-nav-item:hover {
        transform: translateX(4px);
        border-color: rgba(192,132,252,0.6);
        background: linear-gradient(135deg, #1e1b4b, #2e1065);
        box-shadow: 0 4px 20px rgba(124,58,237,0.25),
                    inset 0 0 20px rgba(124,58,237,0.05);
    }
    .sb-nav-item:hover::after { opacity: 1; }
    .sb-nav-icon {
        font-size: 18px;
        filter: drop-shadow(0 0 4px rgba(192,132,252,0.6));
        flex-shrink: 0;
    }
    .sb-nav-label {
        font-family: 'Orbitron', monospace;
        font-size: 9px;
        font-weight: 700;
        letter-spacing: 2px;
        text-transform: uppercase;
        color: #c084fc;
    }
    .sb-nav-divider {
        height: 1px;
        background: linear-gradient(90deg, rgba(124,58,237,0.5), transparent);
        margin: 8px 0;
    }
    </style>
    """, unsafe_allow_html=True)

    st.sidebar.markdown("""
    <div style="font-family:Orbitron,monospace;font-size:13px;font-weight:700;
                letter-spacing:3px;color:#c084fc;padding:8px 0 4px 0;">
        🎮 GAMES ANALYTICS
    </div>
    """, unsafe_allow_html=True)

    st.sidebar.markdown('<div class="sb-nav-divider"></div>', unsafe_allow_html=True)

    # Estiliza os page_link nativos para parecerem os cards
    st.markdown("""
    <style>
    [data-testid="stSidebarNav"] { display: none !important; }
    section[data-testid="stSidebar"] [data-testid="stPageLink"] a {
        display: flex !important;
        align-items: center !important;
        gap: 10px !important;
        padding: 11px 14px !important;
        border-radius: 10px !important;
        background: linear-gradient(135deg, #0f172a, #1e1b4b) !important;
        border: 1px solid rgba(124,58,237,0.2) !important;
        color: #c084fc !important;
        font-family: 'Orbitron', monospace !important;
        font-size: 9px !important;
        font-weight: 700 !important;
        letter-spacing: 2px !important;
        text-transform: uppercase !important;
        text-decoration: none !important;
        margin-bottom: 6px !important;
        transition: transform 0.18s ease, border-color 0.18s ease, box-shadow 0.18s ease !important;
        position: relative !important;
    }
    section[data-testid="stSidebar"] [data-testid="stPageLink"] a:hover {
        transform: translateX(4px) !important;
        border-color: rgba(192,132,252,0.6) !important;
        background: linear-gradient(135deg, #1e1b4b, #2e1065) !important;
        box-shadow: 0 4px 20px rgba(124,58,237,0.25) !important;
    }
    </style>
    """, unsafe_allow_html=True)

    st.sidebar.page_link("app.py",                label="INÍCIO",     icon="🏠")
    st.sidebar.page_link("pages/1_Dashboard.py",  label="DASHBOARD",  icon="📊")
    st.sidebar.page_link("pages/2_Biblioteca.py", label="BIBLIOTECA", icon="🎮")
    st.sidebar.page_link("pages/3_Comparar.py",   label="COMPARAR",   icon="⚔️")

    st.sidebar.markdown('<div class="sb-nav-divider"></div>', unsafe_allow_html=True)

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