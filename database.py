import sqlite3
import pandas as pd

ARQUIVO_DB = "jogos.db"


def criar_banco():
    con = sqlite3.connect(ARQUIVO_DB)
    cur = con.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS jogos (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            nome       TEXT    NOT NULL,
            jogadores  INTEGER DEFAULT 0,
            avaliacao  REAL    DEFAULT 0,
            genero     TEXT    DEFAULT 'N/A',
            fonte      TEXT    DEFAULT 'API',
            imagem_url TEXT    DEFAULT '',
            salvo_em   TEXT    DEFAULT (datetime('now'))
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS favoritos (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            nome     TEXT    NOT NULL UNIQUE,
            fonte    TEXT,
            genero   TEXT,
            avaliacao REAL   DEFAULT 0,
            imagem_url TEXT  DEFAULT '',
            salvo_em TEXT    DEFAULT (datetime('now'))
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS historico (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            data            TEXT    NOT NULL,
            fonte           TEXT    NOT NULL,
            total           INTEGER DEFAULT 0,
            media_avaliacao REAL    DEFAULT 0,
            media_jogadores REAL    DEFAULT 0
        )
    """)

    cur.execute("CREATE INDEX IF NOT EXISTS idx_fonte   ON jogos(fonte)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_nome    ON jogos(nome)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_hist_data ON historico(data)")

    con.commit()
    con.close()


def salvar(df: pd.DataFrame, fonte: str):
    con = sqlite3.connect(ARQUIVO_DB)
    cur = con.cursor()
    cur.execute("DELETE FROM jogos WHERE fonte = ?", (fonte,))
    for _, row in df.iterrows():
        cur.execute(
            "INSERT INTO jogos (nome, jogadores, avaliacao, genero, fonte, imagem_url) VALUES (?,?,?,?,?,?)",
            (row["nome"], int(row.get("jogadores", 0)), float(row.get("avaliacao", 0)),
             row.get("genero", "N/A"), fonte, row.get("imagem_url", ""))
        )
    hoje = pd.Timestamp.now().strftime("%Y-%m-%d")
    cur.execute("DELETE FROM historico WHERE data = ? AND fonte = ?", (hoje, fonte))
    cur.execute(
        "INSERT INTO historico (data, fonte, total, media_avaliacao, media_jogadores) VALUES (?,?,?,?,?)",
        (hoje, fonte, len(df),
         float(df["avaliacao"].mean()) if "avaliacao" in df else 0,
         float(df["jogadores"].mean()) if "jogadores" in df else 0)
    )
    con.commit()
    con.close()
    # Se ainda houver jogos sem gênero no banco, tenta enriquecer via IGDB
    enriquecer_generos()


def _buscar_genero_igdb(nome: str, token: str, client_id: str) -> str:
    """Busca o gênero de um jogo pelo nome exato na API do IGDB."""
    import requests
    MAPA = {
        "Action": "Ação", "Adventure": "Aventura", "RPG": "RPG",
        "Role-playing (RPG)": "RPG", "Strategy": "Estratégia",
        "Shooter": "Tiro", "Simulation": "Simulação", "Sports": "Esportes",
        "Racing": "Corrida", "Fighting": "Luta", "Puzzle": "Quebra-cabeça",
        "Platformer": "Plataforma", "Horror": "Terror", "Survival": "Sobrevivência",
        "Indie": "Indie", "Casual": "Casual", "MMO": "MMO", "MMORPG": "MMORPG",
        "Arcade": "Arcade", "Tactical": "Tático", "MOBA": "MOBA",
        "Hack and slash/Beat 'em up": "Hack and Slash",
        "Real Time Strategy (RTS)": "Estratégia em Tempo Real",
        "Turn-based strategy (TBS)": "Estratégia por Turnos",
        "Point-and-click": "Ponto e Clique", "Visual Novel": "Visual Novel",
    }
    try:
        nome_escaped = nome.replace('"', '\\"')
        body = f'search "{nome_escaped}"; fields genres.name; limit 1;'
        r = requests.post(
            "https://api.igdb.com/v4/games",
            headers={"Client-ID": client_id, "Authorization": f"Bearer {token}"},
            data=body, timeout=6
        )
        results = r.json()
        if results and results[0].get("genres"):
            generos = [MAPA.get(g["name"], g["name"]) for g in results[0]["genres"]]
            return ", ".join(generos)
    except Exception:
        pass
    return ""


def enriquecer_generos():
    """Passo 1: cruza gêneros entre fontes por nome exato.
    Passo 2: para os que ainda ficaram como 'Outros', busca na IGDB pelo nome.
    """
    import os
    from dotenv import load_dotenv
    load_dotenv()

    con = sqlite3.connect(ARQUIVO_DB)
    cur = con.cursor()

    # ── Passo 1: cruzamento entre fontes ─────────────────────────────────────
    cur.execute("""
        SELECT nome, genero, fonte FROM jogos
        WHERE genero != 'Outros' AND genero != '' AND genero IS NOT NULL
    """)
    rows = cur.fetchall()

    prioridade = {"IGDB": 0, "RAWG": 1, "SteamSpy": 2, "CheapShark": 3}
    melhores = {}
    for nome, genero, fonte in rows:
        prio = prioridade.get(fonte, 99)
        if nome not in melhores or prio < melhores[nome][1]:
            melhores[nome] = (genero, prio)

    atualizados = 0
    for nome, (genero, _) in melhores.items():
        cur.execute("""
            UPDATE jogos SET genero = ?
            WHERE nome = ? AND (genero = 'Outros' OR genero = '' OR genero IS NULL)
        """, (genero, nome))
        atualizados += cur.rowcount

    con.commit()
    print(f"Passo 1 — cruzamento: {atualizados} jogos atualizados.")

    # ── Passo 2: busca na IGDB para os que ainda estão como 'Outros' ─────────
    client_id     = os.getenv("IGDB_CLIENT_ID", "")
    client_secret = os.getenv("IGDB_CLIENT_SECRET", "")

    if not client_id or not client_secret:
        con.close()
        return

    # Obtém token
    import requests, time
    try:
        r = requests.post(
            "https://id.twitch.tv/oauth2/token",
            params={"client_id": client_id, "client_secret": client_secret,
                    "grant_type": "client_credentials"}, timeout=8
        )
        token = r.json().get("access_token", "")
    except Exception:
        con.close()
        return

    if not token:
        con.close()
        return

    # Busca jogos ainda sem gênero
    cur.execute("""
        SELECT DISTINCT nome FROM jogos
        WHERE genero = 'Outros' OR genero = '' OR genero IS NULL
    """)
    sem_genero = [row[0] for row in cur.fetchall()]
    # Limita a 60 jogos por busca para não demorar demais
    sem_genero = sem_genero[:60]
    print(f"Passo 2 — buscando gênero na IGDB para {len(sem_genero)} jogos (em lote)...")

    MAPA = {
        "Action": "Ação", "Adventure": "Aventura", "RPG": "RPG",
        "Role-playing (RPG)": "RPG", "Strategy": "Estratégia",
        "Shooter": "Tiro", "Simulation": "Simulação", "Sports": "Esportes",
        "Racing": "Corrida", "Fighting": "Luta", "Puzzle": "Quebra-cabeça",
        "Platformer": "Plataforma", "Horror": "Terror", "Survival": "Sobrevivência",
        "Indie": "Indie", "Casual": "Casual", "MMO": "MMO", "MMORPG": "MMORPG",
        "Arcade": "Arcade", "Tactical": "Tático", "MOBA": "MOBA",
        "Hack and slash/Beat 'em up": "Hack and Slash",
        "Real Time Strategy (RTS)": "Estratégia em Tempo Real",
        "Turn-based strategy (TBS)": "Estratégia por Turnos",
    }

    igdb_atualizados = 0
    LOTE = 10  # até 10 jogos por requisição

    for i in range(0, len(sem_genero), LOTE):
        lote = sem_genero[i:i+LOTE]
        # Monta query OR para buscar vários nomes de uma vez
        condicoes = " | ".join(f'name = "{n.replace(chr(34), "")}"' for n in lote)
        body = f'fields name, genres.name; where {condicoes}; limit {LOTE};'
        try:
            r = requests.post(
                "https://api.igdb.com/v4/games",
                headers={"Client-ID": client_id, "Authorization": f"Bearer {token}"},
                data=body, timeout=8
            )
            for j in r.json():
                if not j.get("genres"):
                    continue
                generos = ", ".join(MAPA.get(g["name"], g["name"]) for g in j["genres"])
                nome_igdb = j.get("name", "")
                cur.execute(
                    "UPDATE jogos SET genero = ? WHERE nome = ? AND (genero = 'Outros' OR genero = '' OR genero IS NULL)",
                    (generos, nome_igdb)
                )
                igdb_atualizados += cur.rowcount
        except Exception as e:
            print(f"Erro lote IGDB: {e}")
        time.sleep(0.3)  # 1 req por lote, ~3 lotes/s — dentro do limite

    con.commit()
    con.close()
    print(f"Passo 2 — IGDB: {igdb_atualizados} jogos atualizados.")


def ler() -> pd.DataFrame:
    con = sqlite3.connect(ARQUIVO_DB)
    df = pd.read_sql_query("SELECT * FROM jogos ORDER BY jogadores DESC", con)
    con.close()
    return df


def ler_historico() -> pd.DataFrame:
    con = sqlite3.connect(ARQUIVO_DB)
    df = pd.read_sql_query("SELECT * FROM historico ORDER BY data ASC", con)
    con.close()
    return df


def favoritar(nome: str, fonte: str, genero: str, avaliacao: float, imagem_url: str):
    con = sqlite3.connect(ARQUIVO_DB)
    con.execute(
        "INSERT OR IGNORE INTO favoritos (nome, fonte, genero, avaliacao, imagem_url) VALUES (?,?,?,?,?)",
        (nome, fonte, genero, avaliacao, imagem_url)
    )
    con.commit()
    con.close()


def desfavoritar(nome: str):
    con = sqlite3.connect(ARQUIVO_DB)
    con.execute("DELETE FROM favoritos WHERE nome = ?", (nome,))
    con.commit()
    con.close()


def ler_favoritos() -> pd.DataFrame:
    con = sqlite3.connect(ARQUIVO_DB)
    df = pd.read_sql_query("SELECT * FROM favoritos ORDER BY salvo_em DESC", con)
    con.close()
    return df


def is_favorito(nome: str) -> bool:
    con = sqlite3.connect(ARQUIVO_DB)
    cur = con.cursor()
    cur.execute("SELECT 1 FROM favoritos WHERE nome = ?", (nome,))
    res = cur.fetchone() is not None
    con.close()
    return res
