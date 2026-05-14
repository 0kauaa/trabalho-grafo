"""
fetch_lyrics.py
---------------
Lê data/playlist_data.csv, busca letras no Genius (primário) e LRCLib
(fallback), e salva:
  - data/lyrics.csv        : track_id, track_name, artist_name, lyrics, source
  - data/lyrics_report.csv : track_id, track_name, artist_name, status, source, fail_reason, lyric_len

Como usar:
  1. pip install lyricsgenius requests pandas
  2. Preencha a constante GENIUS_TOKEN abaixo (LRCLib não precisa de token)
  3. Baixe 'data/playlist_data.csv' do Colab e coloque na pasta data/
  4. python fetch_lyrics.py
  5. Suba data/lyrics.csv e data/lyrics_report.csv para o Colab

Tokens:
  Genius  → https://genius.com/api-clients  (gratuito, sem limite declarado)
  LRCLib  → https://lrclib.net              (público, sem autenticação)
"""

import os
import time
import re
import unicodedata
import requests
import lyricsgenius
import pandas as pd

# ── Configuração ──────────────────────────────────────────────────────────────

GENIUS_TOKEN = "NFvBeQQtxsYKIFgTPHQEqcEGWNMKDJGd0Y-5bMeFZ_QTjNvSP9hWJ2t1DYkak7_7"

INPUT_CSV  = "data/playlist_data.csv"
OUT_LYRICS = "data/lyrics.csv"
OUT_REPORT = "data/lyrics_report.csv"

DELAY_GENIUS  = 0.8   # segundos entre requests ao Genius (evitar rate-limit)
DELAY_LRCLIB  = 0.3   # segundos entre requests ao LRCLib

# ── Helpers ───────────────────────────────────────────────────────────────────

def _clean_genius(raw: str) -> str:
    """Remove headers de seção ([Verse 1], [Chorus], etc.) e linhas extras."""
    # O Genius às vezes inclui um cabeçalho inicial tipo "SongTitle Lyrics"
    text = re.sub(r"^.*?Lyrics\n", "", raw, count=1)
    text = re.sub(r"\[.*?\]", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _normalize(text: str) -> str:
    """Lowercase + remove acentos + remove pontuação — para matching."""
    text = unicodedata.normalize("NFD", text.lower())
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    text = re.sub(r"[^\w\s]", "", text)
    return text.strip()

# ── Genius ────────────────────────────────────────────────────────────────────

def fetch_genius(genius: lyricsgenius.Genius, track_name: str, artist_name: str):
    """Retorna (lyrics_str, 'genius') ou (None, fail_reason)."""
    try:
        song = genius.search_song(track_name, artist_name)
        if song is None:
            return None, "not_found"
        if not song.lyrics or not song.lyrics.strip():
            return None, "empty_lyrics"
        return _clean_genius(song.lyrics), "genius"
    except TimeoutError:
        return None, "timeout"
    except Exception as e:
        return None, f"genius_error:{type(e).__name__}"

# ── LRCLib ────────────────────────────────────────────────────────────────────

LRCLIB_BASE = "https://lrclib.net/api"


def fetch_lrclib(track_name: str, artist_name: str):
    """
    Retorna (lyrics_str, 'lrclib') ou (None, fail_reason).

    LRCLib é uma API pública sem autenticação que agrega letras sincronizadas
    (LRC) e não-sincronizadas. Usamos plainLyrics para os embeddings.
    """
    try:
        params = {"track_name": track_name, "artist_name": artist_name}
        r = requests.get(f"{LRCLIB_BASE}/get", params=params, timeout=10,
                         headers={"User-Agent": "playlist-communities/1.0 (academic)"})

        if r.status_code == 404:
            # Tenta busca mais ampla pelo nome da faixa
            r2 = requests.get(f"{LRCLIB_BASE}/search",
                              params={"q": f"{artist_name} {track_name}"},
                              timeout=10,
                              headers={"User-Agent": "playlist-communities/1.0 (academic)"})
            if r2.status_code != 200 or not r2.json():
                return None, "not_found"

            # Pega o resultado mais próximo pelo nome do artista
            results = r2.json()
            norm_artist = _normalize(artist_name)
            match = next(
                (x for x in results if _normalize(x.get("artistName", "")) == norm_artist),
                results[0]  # fallback: primeiro resultado
            )
            lyrics = match.get("plainLyrics", "") or ""
        elif r.status_code == 200:
            lyrics = r.json().get("plainLyrics", "") or ""
        else:
            return None, f"lrclib_http_{r.status_code}"

        if not lyrics.strip():
            return None, "empty_lyrics"

        return lyrics.strip(), "lrclib"

    except requests.Timeout:
        return None, "timeout"
    except Exception as e:
        return None, f"lrclib_error:{type(e).__name__}"

# ── Pipeline principal ────────────────────────────────────────────────────────

def main():
    if not os.path.exists(INPUT_CSV):
        print(f"✗ Arquivo '{INPUT_CSV}' não encontrado.")
        print("  Baixe 'data/playlist_data.csv' do Colab e coloque na pasta data/")
        return

    df = pd.read_csv(INPUT_CSV)
    total = len(df)
    print(f"✓ {total} faixas carregadas de '{INPUT_CSV}'\n")

    genius = lyricsgenius.Genius(
        GENIUS_TOKEN,
        remove_section_headers=True,
        skip_non_songs=True,
        timeout=10,
    )

    rows_lyrics = []
    rows_report = []

    for i, row in df.iterrows():
        tid    = row["track_id"]
        name   = row["track_name"]
        artist = row["artist_name"]

        print(f"  [{i+1:>3}/{total}] {artist} — {name}")

        # Tentativa 1: Genius
        lyrics, source = fetch_genius(genius, name, artist)
        time.sleep(DELAY_GENIUS)

        # Tentativa 2: LRCLib (fallback)
        if lyrics is None:
            fail_genius = source
            lyrics, source = fetch_lrclib(name, artist)
            time.sleep(DELAY_LRCLIB)
            if lyrics is not None:
                print(f"         ↳ Genius: {fail_genius} | fallback LRCLib ✓")
            else:
                print(f"         ↳ Genius: {fail_genius} | LRCLib: {source}")
                source = f"genius:{fail_genius}|lrclib:{source}"
        
        status = "ok" if lyrics is not None else "failed"
        icon   = "✓" if status == "ok" else "✗"
        print(f"         {icon} {status}"
              + (f" via {source} | {len(lyrics)} chars" if lyrics else f" ({source})"))

        if lyrics is not None:
            rows_lyrics.append({
                "track_id":    tid,
                "track_name":  name,
                "artist_name": artist,
                "lyrics":      lyrics,
                "source":      source,
            })

        rows_report.append({
            "track_id":    tid,
            "track_name":  name,
            "artist_name": artist,
            "status":      status,
            "source":      source if status == "ok" else None,
            "fail_reason": source if status == "failed" else None,
            "lyric_len":   len(lyrics) if lyrics else 0,
        })

    # Salva resultados
    os.makedirs("data", exist_ok=True)
    pd.DataFrame(rows_lyrics).to_csv(OUT_LYRICS, index=False)
    pd.DataFrame(rows_report).to_csv(OUT_REPORT, index=False)

    # Resumo
    df_report = pd.DataFrame(rows_report)
    ok     = (df_report["status"] == "ok").sum()
    failed = (df_report["status"] == "failed").sum()
    print(f"\n{'─'*55}")
    print(f"  Letras recuperadas : {ok}/{total} ({ok/total*100:.1f}%)")
    print(f"  Falhas             : {failed}/{total} ({failed/total*100:.1f}%)")
    if failed > 0:
        print(f"\n  Detalhamento das falhas:")
        for reason, count in df_report["fail_reason"].dropna().value_counts().items():
            print(f"    • {reason}: {count}")
    sources = df_report[df_report["status"] == "ok"]["source"].value_counts()
    if not sources.empty:
        print(f"\n  Fontes utilizadas:")
        for src, count in sources.items():
            print(f"    • {src}: {count}")
    print(f"\n  Arquivos salvos:")
    print(f"    ✓ {OUT_LYRICS}")
    print(f"    ✓ {OUT_REPORT}")
    print(f"{'─'*55}")
    print("\n  → Suba os dois arquivos para a pasta data/ no Colab.")


if __name__ == "__main__":
    main()
