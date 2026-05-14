# acrescente ao graph.py existente

import numpy as np
import pandas as pd
from typing import Optional


def compute_similarity_lyric(
    df: pd.DataFrame,
    lyrics_map: dict[str, Optional[str]],
) -> tuple[np.ndarray, list[str]]:
    """
    calcula matriz de similaridade de cosseno entre letras usando embeddings
    multilíngues (paraphrase-multilingual-MiniLM-L12-v2).

    faixas sem letra são excluídas — o índice retornado reflete isso.

    args:
        df: DataFrame completo da playlist
        lyrics_map: dict {track_id -> letra | None}

    returns:
        sim_matrix: matriz de similaridade N'×N' (só faixas com letra)
        valid_ids:  lista de track_ids na mesma ordem da matriz
    """
    from sentence_transformers import SentenceTransformer
    from sklearn.metrics.pairwise import cosine_similarity

    # ── filtrar faixas com letra ──────────────────
    df_valid  = df[df['track_id'].map(lambda tid: lyrics_map.get(tid) is not None)].copy()
    valid_ids = df_valid['track_id'].tolist()
    letras    = [lyrics_map[tid] for tid in valid_ids]

    n = len(valid_ids)
    if n == 0:
        print("nenhuma letra disponível — grafo lírico não pode ser construído.")
        return np.array([]), []

    print(f"gerando embeddings para {n} faixas (modelo multilíngue)...")
    print("  (primeira execução faz download do modelo ~120MB)")

    model      = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
    embeddings = model.encode(letras, show_progress_bar=True, batch_size=16)

    sim_matrix = cosine_similarity(embeddings).astype(np.float32)

    # garantir diagonal = 1.0 (ruído numérico)
    np.fill_diagonal(sim_matrix, 1.0)

    print(f"✓ matriz {n}×{n} computada")

    # estatísticas rápidas
    mask = ~np.eye(n, dtype=bool)
    vals = sim_matrix[mask]
    print(f"  similaridade — mín: {vals.min():.3f} | média: {vals.mean():.3f} | máx: {vals.max():.3f}")

    return sim_matrix, valid_ids
