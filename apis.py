import os
import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

MAPA_GENEROS = {
    # Inglês → Português
    "Action":             "Ação",
    "Adventure":          "Aventura",
    "RPG":                "RPG",
    "Role-playing (RPG)": "RPG",
    "Strategy":           "Estratégia",
    "Shooter":            "Tiro",
    "Simulation":         "Simulação",
    "Sports":             "Esportes",
    "Racing":             "Corrida",
    "Fighting":           "Luta",
    "Puzzle":             "Quebra-cabeça",
    "Platformer":         "Plataforma",
    "Horror":             "Terror",
    "Survival":           "Sobrevivência",
    "Indie":              "Indie",
    "Casual":             "Casual",
    "MMO":                "MMO",
    "MMORPG":             "MMORPG",
    "Card":               "Cartas",
    "Board Games":        "Tabuleiro",
    "Music":              "Música",
    "Educational":        "Educacional",
    "Arcade":             "Arcade",
    "Point-and-click":    "Ponto e Clique",
    "Visual Novel":       "Visual Novel",
    "Hack and slash/Beat 'em up": "Hack and Slash",
    "Real Time Strategy (RTS)":   "Estratégia em Tempo Real",
    "Turn-based strategy (TBS)":  "Estratégia por Turnos",
    "Tactical":           "Tático",
    "MOBA":               "MOBA",
    "Battle Royale":      "Battle Royale",
}

def normalizar_genero(genero: str) -> str:
    if not genero or genero.strip() in ("", "N/A", "null", "None"):
        return "Outros"
    g = genero.strip()
    return MAPA_GENEROS.get(g, g)

TIMEOUT    = 8
RAWG_KEY   = os.getenv("RAWG_KEY", "")
IGDB_ID    = os.getenv("IGDB_CLIENT_ID", "")
IGDB_SECRET= os.getenv("IGDB_CLIENT_SECRET", "")


def _enriquecer_generos_igdb(df: pd.DataFrame) -> pd.DataFrame:
    """Consulta a IGDB em lotes para preencher gêneros ausentes ('Outros') no DataFrame.
    
    Só é executada se IGDB_ID e IGDB_SECRET estiverem configurados.
    Modifica a coluna 'genero' in-place e retorna o DataFrame atualizado.
    """
    if df.empty or not IGDB_ID or not IGDB_SECRET:
        return df

    # Linhas que precisam de gênero
    sem_genero_mask = df["genero"].isin(["Outros", "", "N/A"]) | df["genero"].isna()
    nomes_sem_genero = df.loc[sem_genero_mask, "nome"].dropna().unique().tolist()

    if not nomes_sem_genero:
        return df

    # Obtém token
    try:
        r = requests.post(
            "https://id.twitch.tv/oauth2/token",
            params={"client_id": IGDB_ID, "client_secret": IGDB_SECRET,
                    "grant_type": "client_credentials"},
            timeout=TIMEOUT,
        )
        r.raise_for_status()
        token = r.json().get("access_token", "")
    except Exception as e:
        print(f"[IGDB enriquecimento] Erro ao obter token: {e}")
        return df

    if not token:
        return df

    headers = {"Client-ID": IGDB_ID, "Authorization": f"Bearer {token}"}
    generos_encontrados: dict[str, str] = {}

    import time
    from concurrent.futures import ThreadPoolExecutor, as_completed

    def _buscar_um(nome: str) -> tuple[str, str]:
        nome_safe = nome.replace('"', "")
        body = f'search "{nome_safe}"; fields name, genres.name; limit 3;'
        try:
            resp = requests.post(
                "https://api.igdb.com/v4/games",
                headers=headers,
                data=body,
                timeout=TIMEOUT,
            )
            resp.raise_for_status()
            for jogo in resp.json():
                if jogo.get("genres"):
                    generos = ", ".join(
                        MAPA_GENEROS.get(g["name"], g["name"])
                        for g in jogo["genres"]
                    )
                    return nome, generos
        except Exception:
            pass
        return nome, ""

    # Limita a 60 simultâneos para não sobrecarregar a API
    MAX_WORKERS = 5
    lote_nomes = nomes_sem_genero[:60]

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(_buscar_um, n): n for n in lote_nomes}
        for future in as_completed(futures):
            nome, genero = future.result()
            if genero:
                generos_encontrados[nome] = genero
            time.sleep(0.05)  # pequena pausa entre callbacks

    # Aplica os gêneros encontrados ao DataFrame
    if generos_encontrados:
        mapa_series = df["nome"].map(generos_encontrados)
        atualizar = sem_genero_mask & mapa_series.notna()
        df.loc[atualizar, "genero"] = mapa_series[atualizar]
        print(f"[IGDB enriquecimento] {atualizar.sum()} gêneros preenchidos.")

    return df


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
                "genero":     normalizar_genero(info.get("genre", "").split(",")[0].strip()),
                "imagem_url": f"https://cdn.akamai.steamstatic.com/steam/apps/{appid}/header.jpg" if appid else "",
                "fonte":      "SteamSpy",
            })
        df = pd.DataFrame(jogos)
        # Gênero do SteamSpy é pouco confiável — enriquece via IGDB
        return _enriquecer_generos_igdb(df)
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
            genero = ", ".join(normalizar_genero(g["name"]) for g in j.get("genres", [])) or "Outros"
            jogos.append({
                "nome":       j.get("name", "?"),
                "jogadores":  j.get("ratings_count", 0),
                "avaliacao":  round(j.get("rating", 0) * 20, 1),
                "genero":     genero,
                "imagem_url": j.get("background_image", ""),
                "fonte":      "RAWG",
            })
        return _enriquecer_generos_igdb(pd.DataFrame(jogos))
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
            genero = ", ".join(normalizar_genero(g["name"]) for g in j.get("genres", [])) or "Outros"
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
        return _enriquecer_generos_igdb(pd.DataFrame(jogos))
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
                "genero":     "Outros",   # sem gênero na API — será enriquecido via IGDB
                "imagem_url": j.get("thumb", ""),
                "fonte":      "CheapShark",
            })
        df = pd.DataFrame(jogos)
        # CheapShark não fornece gênero — tenta preencher via IGDB
        return _enriquecer_generos_igdb(df)
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