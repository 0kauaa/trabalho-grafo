# libs
import time
import lyricsgenius
import pandas as pd
from typing import Optional

# ──────────────────────────────────────────────
# razões possíveis de falha na recuperação
# ──────────────────────────────────────────────
FAIL_NOT_FOUND    = "not_found"       # genius não encontrou a música
FAIL_TIMEOUT      = "timeout"         # requisição excedeu o tempo limite
FAIL_EMPTY        = "empty_lyrics"    # letra retornada veio vazia
FAIL_API_ERROR    = "api_error"       # erro genérico da API


def build_genius_client(token: str, verbose: bool = False) -> lyricsgenius.Genius:
    """
    instancia o cliente lyricsgenius com configurações conservadoras.

    args:
        token: Genius API token (https://genius.com/api-clients)
        verbose: exibir logs internos do lyricsgenius

    returns:
        cliente Genius configurado
    """
    genius = lyricsgenius.Genius(
        token,
        verbose=verbose,
        remove_section_headers=True,   # remove [Chorus], [Verse], etc.
        skip_non_songs=True,
        retries=2,
        timeout=10,
    )
    return genius


def fetch_lyrics(
    genius: lyricsgenius.Genius,
    df: pd.DataFrame,
    delay: float = 0.5,
) -> tuple[dict[str, Optional[str]], pd.DataFrame]:
    """
    busca letras no Genius para cada faixa do DataFrame.

    args:
        genius: cliente lyricsgenius autenticado
        df: DataFrame com colunas track_id, track_name, artist_name
        delay: pausa entre requisições (segundos) para evitar rate limit

    returns:
        lyrics_map: dict {track_id -> letra (str) ou None}
        report_df: DataFrame com status de cada faixa
    """
    lyrics_map = {}
    report     = []

    total = len(df)
    print(f"buscando letras para {total} faixas...\n")

    for i, row in df.iterrows():
        tid    = row['track_id']
        name   = row['track_name']
        artist = row['artist_name']

        status      = None
        fail_reason = None
        letra       = None

        try:
            song = genius.search_song(name, artist)

            if song is None:
                status      = "failed"
                fail_reason = FAIL_NOT_FOUND

            elif not song.lyrics or not song.lyrics.strip():
                status      = "failed"
                fail_reason = FAIL_EMPTY

            else:
                letra  = song.lyrics.strip()
                status = "ok"

        except TimeoutError:
            status      = "failed"
            fail_reason = FAIL_TIMEOUT

        except Exception as e:
            status      = "failed"
            fail_reason = FAIL_API_ERROR
            print(f"  ⚠ erro inesperado em '{name}': {e}")

        lyrics_map[tid] = letra

        icon = "✓" if status == "ok" else "✗"
        msg  = fail_reason if fail_reason else f"{len(letra)} chars"
        print(f"  [{i+1:>3}/{total}] {icon} {artist} — {name} ({msg})")

        report.append({
            'track_id':    tid,
            'track_name':  name,
            'artist_name': artist,
            'status':      status,
            'fail_reason': fail_reason,
            'lyric_len':   len(letra) if letra else 0,
        })

        time.sleep(delay)

    report_df = pd.DataFrame(report)

    # ── resumo ──────────────────────────────────
    ok      = (report_df['status'] == 'ok').sum()
    failed  = (report_df['status'] == 'failed').sum()
    print(f"\n{'─'*50}")
    print(f"resultado: {ok} letras recuperadas | {failed} falhas")

    if failed > 0:
        print(f"\ndetalhamento das falhas:")
        for reason, count in report_df['fail_reason'].value_counts().items():
            print(f"  • {reason}: {count}")
        print(f"\nfaixas sem letra (excluídas do grafo lírico):")
        sem = report_df[report_df['status'] == 'failed'][['track_name', 'artist_name', 'fail_reason']]
        print(sem.to_string(index=False))

    print(f"{'─'*50}\n")

    return lyrics_map, report_df
