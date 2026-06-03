import os
import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

TIMEOUT    = 8
RAWG_KEY   = os.getenv("RAWG_KEY", "")
IGDB_ID    = os.getenv("IGDB_CLIENT_ID", "")
IGDB_SECRET= os.getenv("IGDB_CLIENT_SECRET", "")


def buscar_steamspy() -> pd.DataFrame:
    try:
        r = requests.get("https://steamspy.com/api.php?request=top100in2weeks", timeout=TIMEOUT)
        dados = r.json()
        jogos = []
        for info in list(dados.values())[:250]:
            pos   = info.get("positive", 0)
            neg   = info.get("negative", 0)
            total = pos + neg
            nota  = round((pos / total) * 100, 1) if total > 0 else 0
            appid = info.get("appid", "")
            jogos.append({
                "nome":       info.get("name", "?"),
                "jogadores":  info.get("ccu", 0),
                "avaliacao":  nota,
                "genero":     info.get("genre", "N/A"),
                "imagem_url": f"https://cdn.akamai.steamstatic.com/steam/apps/{appid}/header.jpg" if appid else "",
                "fonte":      "SteamSpy",
            })
        return pd.DataFrame(jogos)
    except Exception as e:
        print(f"Erro SteamSpy: {e}")
        return pd.DataFrame()


def buscar_rawg() -> pd.DataFrame:
    if not RAWG_KEY:
        print("⚠️  RAWG: defina RAWG_KEY no .env")
        return pd.DataFrame()
    try:
        url = f"https://api.rawg.io/api/games?key={RAWG_KEY}&ordering=-rating&page_size=250"
        r = requests.get(url, timeout=TIMEOUT)
        dados = r.json().get("results", [])
        jogos = []
        for j in dados:
            genero = j["genres"][0]["name"] if j.get("genres") else "N/A"
            jogos.append({
                "nome":       j.get("name", "?"),
                "jogadores":  j.get("ratings_count", 0),
                "avaliacao":  round(j.get("rating", 0) * 20, 1),
                "genero":     genero,
                "imagem_url": j.get("background_image", ""),
                "fonte":      "RAWG",
            })
        return pd.DataFrame(jogos)
    except Exception as e:
        print(f"Erro RAWG: {e}")
        return pd.DataFrame()


def _igdb_token() -> str:
    if not IGDB_ID or not IGDB_SECRET:
        return ""
    try:
        r = requests.post(
            "https://id.twitch.tv/oauth2/token",
            params={"client_id": IGDB_ID, "client_secret": IGDB_SECRET, "grant_type": "client_credentials"},
            timeout=TIMEOUT,
        )
        r.raise_for_status()
        return r.json()["access_token"]
    except Exception as e:
        print(f"Erro token IGDB: {e}")
        return ""


def buscar_igdb() -> pd.DataFrame:
    if not IGDB_ID or not IGDB_SECRET:
        print("⚠️  IGDB: defina IGDB_CLIENT_ID e IGDB_CLIENT_SECRET no .env")
        return pd.DataFrame()
    token = _igdb_token()
    if not token:
        return pd.DataFrame()
    try:
        headers = {"Client-ID": IGDB_ID, "Authorization": f"Bearer {token}"}
        body = (
            "fields name, rating, rating_count, genres.name, cover.url; "
            "where rating_count > 100 & rating != null; "
            "sort rating_count desc; limit 250;"
        )
        r = requests.post("https://api.igdb.com/v4/games", headers=headers, data=body, timeout=TIMEOUT)
        r.raise_for_status()
        jogos = []
        for j in r.json():
            genero = j["genres"][0]["name"] if j.get("genres") else "N/A"
            capa   = j.get("cover", {}).get("url", "")
            if capa:
                capa = "https:" + capa.replace("t_thumb", "t_cover_big")
            jogos.append({
                "nome":       j.get("name", "?"),
                "jogadores":  j.get("rating_count", 0),
                "avaliacao":  round(j.get("rating", 0), 1),
                "genero":     genero,
                "imagem_url": capa,
                "fonte":      "IGDB",
            })
        return pd.DataFrame(jogos)
    except Exception as e:
        print(f"Erro IGDB: {e}")
        return pd.DataFrame()


def buscar_cheapshark() -> pd.DataFrame:
    try:
        url = "https://www.cheapshark.com/api/1.0/deals?sortBy=Savings&pageSize=250"
        r = requests.get(url, timeout=TIMEOUT)
        jogos = []
        for j in r.json():
            jogos.append({
                "nome":       j.get("title", "?"),
                "jogadores":  0,
                "avaliacao":  round(float(j.get("savings", 0)), 1),
                "genero":     "Promocao",
                "imagem_url": j.get("thumb", ""),
                "fonte":      "CheapShark",
            })
        return pd.DataFrame(jogos)
    except Exception as e:
        print(f"Erro CheapShark: {e}")
        return pd.DataFrame()


def buscar_tudo() -> dict:
    return {
        "SteamSpy":   buscar_steamspy(),
        "RAWG":       buscar_rawg(),
        "IGDB":       buscar_igdb(),
        "CheapShark": buscar_cheapshark(),
    }
