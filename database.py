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
