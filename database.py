
import sqlite3
import pandas as pd

ARQUIVO_DB = "jogos.db"


def criar_banco():
    """Cria o banco e a tabela de jogos (só executa uma vez)."""
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
            salvo_em   TEXT    DEFAULT (datetime('now'))
        )
    """)

    con.commit()
    con.close()


def salvar(df: pd.DataFrame, fonte: str):
    """Apaga os dados antigos da fonte e salva os novos."""
    con = sqlite3.connect(ARQUIVO_DB)
    cur = con.cursor()

    cur.execute("DELETE FROM jogos WHERE fonte = ?", (fonte,))

    for _, row in df.iterrows():
        cur.execute(
            "INSERT INTO jogos (nome, jogadores, avaliacao, genero, fonte) VALUES (?,?,?,?,?)",
            (row["nome"], int(row["jogadores"]), float(row["avaliacao"]), row["genero"], fonte)
        )

    con.commit()
    con.close()


def ler() -> pd.DataFrame:
    """Lê todos os jogos salvos no banco."""
    con = sqlite3.connect(ARQUIVO_DB)
    df = pd.read_sql_query("SELECT * FROM jogos ORDER BY jogadores DESC", con)
    con.close()
    return df
