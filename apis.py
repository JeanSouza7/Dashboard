 

import requests
import pandas as pd

TIMEOUT = 8

def buscar_steamspy() -> pd.DataFrame:
    try:
        r = requests.get("https://steamspy.com/api.php?request=top100in2weeks", timeout=TIMEOUT)
        dados = r.json()
        jogos = []
        for info in list(dados.values())[:250]:
            pos = info.get("positive", 0)
            neg = info.get("negative", 0)
            total = pos + neg
            nota = round((pos / total) * 100, 1) if total > 0 else 0
            jogos.append({
                "nome":      info.get("name", "?"),
                "jogadores": info.get("ccu", 0),
                "avaliacao": nota,
                "genero":    info.get("genre", "N/A"),
                "fonte":     "SteamSpy"
            })
        return pd.DataFrame(jogos)
    except Exception as e:
        print(f"Erro SteamSpy: {e}")
        return pd.DataFrame()


def buscar_rawg() -> pd.DataFrame:

    try:
        url = "https://api.rawg.io/api/games?key=3b28e31f4bf44e19a5fc47c8d1e5e2d7&ordering=-rating&page_size=250"
        r = requests.get(url, timeout=TIMEOUT)
        dados = r.json().get("results", [])
        jogos = []
        for j in dados:
            genero = j["genres"][0]["name"] if j.get("genres") else "N/A"
            jogos.append({
                "nome":      j.get("name", "?"),
                "jogadores": j.get("ratings_count", 0),
                "avaliacao": round(j.get("rating", 0) * 20, 1),  # 0-5 → 0-100
                "genero":    genero,
                "fonte":     "RAWG"
            })
        return pd.DataFrame(jogos)
    except Exception as e:
        print(f"Erro RAWG: {e}")
        return pd.DataFrame()


def buscar_freetogame() -> pd.DataFrame:
    try:
        r = requests.get("https://www.freetogame.com/api/games?sort-by=popularity", timeout=TIMEOUT)
        dados = r.json()[:250]
        jogos = []
        for j in dados:
            jogos.append({
                "nome":      j.get("title", "?"),
                "jogadores": 0,   
                "avaliacao": 0.0, 
                "genero":    j.get("genre", "N/A"),
                "fonte":     "FreeToGame"
            })
        return pd.DataFrame(jogos)
    except Exception as e:
        print(f"Erro FreeToGame: {e}")
        return pd.DataFrame()


def buscar_cheapshark() -> pd.DataFrame:
    try:
        url = "https://www.cheapshark.com/api/1.0/deals?sortBy=Savings&pageSize=250"
        r = requests.get(url, timeout=TIMEOUT)
        dados = r.json()
        jogos = []
        for j in dados:
            desconto = float(j.get("savings", 0))
            jogos.append({
                "nome":      j.get("title", "?"),
                "jogadores": 0,
                "avaliacao": round(desconto, 1),
                "genero":    "Promoção",
                "fonte":     "CheapShark"
            })
        return pd.DataFrame(jogos)
    except Exception as e:
        print(f"Erro CheapShark: {e}")
        return pd.DataFrame()


def buscar_tudo() -> dict:
    return {
        "SteamSpy":   buscar_steamspy(),
        "RAWG":       buscar_rawg(),
        "FreeToGame": buscar_freetogame(),
        "CheapShark": buscar_cheapshark(),
    }
