# libs
import sys
from src.auth import auth
from src.access import fetch_playlist_tracks, get_spotify_client
from src.dataframe import build_dataframe, summarize_dataframe
from src.lyrics import build_genius_client, fetch_lyrics
from src.graph import (
    compute_similarity,
    compute_similarity_lyric,
    extract_edges,
    create_graph,
    detect_communities,
    visualize_graph,
)


def run_popularity_pipeline(df, label="popularity"):
    """pipeline original: similaridade por popularidade + artista."""
    print(f"\n{'='*70}")
    print(f"GRAFO DE {label.upper()}")
    print(f"{'='*70}")

    sim   = compute_similarity(df)
    edges = extract_edges(df, sim, threshold=0.6, max_per_node=10)
    edges.to_csv(f'data/edges_{label}.csv', index=False)

    graph  = create_graph(df, edges)
    comms  = detect_communities(graph)

    _print_communities(graph)
    visualize_graph(graph, f'graphs/graph_{label}.png')
    graph.write_graphml(f'graphs/graph_{label}.graphml')

    return graph


def run_lyric_pipeline(df, lyrics_map, label="lyric"):
    """pipeline novo: similaridade por conteúdo lírico (embeddings)."""
    print(f"\n{'='*70}")
    print(f"GRAFO DE {label.upper()}")
    print(f"{'='*70}")

    sim, valid_ids = compute_similarity_lyric(df, lyrics_map)

    if len(valid_ids) == 0:
        print("grafo lírico ignorado — sem letras disponíveis.")
        return None

    # subconjunto do df com apenas as faixas que têm letra
    df_valid = df[df['track_id'].isin(valid_ids)].copy()
    df_valid = df_valid.set_index('track_id').loc[valid_ids].reset_index()

    edges = extract_edges(df_valid, sim, threshold=0.5, max_per_node=10)
    edges.to_csv(f'data/edges_{label}.csv', index=False)

    graph = create_graph(df_valid, edges)
    comms = detect_communities(graph)

    _print_communities(graph)
    visualize_graph(graph, f'graphs/graph_{label}.png')
    graph.write_graphml(f'graphs/graph_{label}.graphml')

    return graph


def compare_graphs(g_pop, g_lyric):
    """resumo comparativo entre os dois grafos."""
    if g_lyric is None:
        return

    print(f"\n{'='*70}")
    print("COMPARAÇÃO ENTRE GRAFOS")
    print(f"{'='*70}")

    def metrics(g, name):
        comms = max(g.vs['community']) + 1 if 'community' in g.vs.attributes() else '—'
        print(f"\n  {name}")
        print(f"    nós:         {g.vcount()}")
        print(f"    arestas:     {g.ecount()}")
        print(f"    densidade:   {g.density():.3f}")
        print(f"    grau médio:  {sum(g.degree()) / g.vcount():.1f}")
        print(f"    comunidades: {comms}")

    metrics(g_pop,   "Grafo de Popularidade + Artista")
    metrics(g_lyric, "Grafo Lírico (embeddings multilíngues)")
    print()


def _print_communities(graph):
    membership    = graph.vs['community']
    num_comms     = max(membership) + 1
    import numpy as np

    print(f"\nCOMUNIDADES DETECTADAS")
    print(f"{'─'*50}")

    for i in range(num_comms):
        artistas = {}
        pops     = []
        for idx, comm in enumerate(membership):
            if comm == i:
                artista = graph.vs[idx]['artist']
                artistas[artista] = artistas.get(artista, 0) + 1
                pops.append(graph.vs[idx]['popularity'])

        top   = sorted(artistas.items(), key=lambda x: x[1], reverse=True)[:5]
        total = sum(artistas.values())
        print(f"\n  Comunidade {i} — {total} faixas | pop. média: {np.mean(pops):.1f}")
        for artista, count in top:
            print(f"    • {artista}: {count} faixa(s)")


def main(client_id, client_secret, redirect_uri):
    import os
    os.makedirs('data', exist_ok=True)
    os.makedirs('graphs', exist_ok=True)

    # ── entrada ───────────────────────────────────────────────────────────
    playlist_id  = input("playlist (id, uri ou url): ")
    genius_token = input("genius api token: ")

    # ── autenticação ──────────────────────────────────────────────────────
    print("\nAUTENTICAÇÃO")
    print("-" * 70)
    sp = get_spotify_client(client_id, client_secret, redirect_uri)

    # ── fetch playlist ────────────────────────────────────────────────────
    print("\nFETCH PLAYLIST")
    print("-" * 70)
    tracks = fetch_playlist_tracks(sp, playlist_id)

    # ── dataframe ─────────────────────────────────────────────────────────
    print("\nDATAFRAME")
    print("-" * 70)
    df = build_dataframe(tracks)
    summarize_dataframe(df)
    df.to_csv('data/playlist_data.csv', index=False)

    # ── letras ────────────────────────────────────────────────────────────
    print("\nBUSCA DE LETRAS (Genius)")
    print("-" * 70)
    genius     = build_genius_client(genius_token)
    lyrics_map, report = fetch_lyrics(genius, df)
    report.to_csv('data/lyrics_report.csv', index=False)

    # ── pipelines ─────────────────────────────────────────────────────────
    g_pop   = run_popularity_pipeline(df)
    g_lyric = run_lyric_pipeline(df, lyrics_map)

    # ── comparação ────────────────────────────────────────────────────────
    compare_graphs(g_pop, g_lyric)

    # ── resumo final ──────────────────────────────────────────────────────
    print(f"\n{'='*70}")
    print("PIPELINE CONCLUÍDO")
    print(f"{'='*70}")
    print("\narquivos gerados:")
    for f in [
        "data/playlist_data.csv",
        "data/lyrics_report.csv",
        "data/edges_popularity.csv",
        "data/edges_lyric.csv",
        "graphs/graph_popularity.png",
        "graphs/graph_lyric.png",
        "graphs/graph_popularity.graphml",
        "graphs/graph_lyric.graphml",
    ]:
        print(f"  {f}")
    print()


if __name__ == "__main__":
    CLIENT_ID, CLIENT_SECRET, REDIRECT_URI = auth()
    try:
        main(CLIENT_ID, CLIENT_SECRET, REDIRECT_URI)
    except Exception as e:
        print(f"\nerro: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
