# libs
import sys
from auth import get_spotify_client
from playlist import fetch_playlist_tracks, fetch_artist_genres, fetch_audio_features
from dataframe import build_dataframe, summarize_dataframe
from grafo import compute_similarity, extract_edges, create_graph, detect_communities, visualize_graph

def main(client_id: str, client_secret: str, redirect_uri: str, playlist_id: str):
    """
    executa pipeline completo
    
    args:
        client_id: id da aplicação spotify
        client_secret: Secret da aplicação
        redirect_uri: URI de redirecionamento
        playlist_id: ID da playlist
    """

    
    # 1. AUTENTICAÇÃO
    print("AUTENTICAÇÃO")
    print("-"*70)
    sp = get_spotify_client(client_id, client_secret, redirect_uri)
    
    # 2. FETCH PLAYLIST
    print("\nFETCH PLAYLIST")
    print("-"*70)
    tracks = fetch_playlist_tracks(sp, playlist_id)
    
    artist_ids = [t['artists'][0]['id'] for t in tracks if t['artists']]
    genres = fetch_artist_genres(sp, artist_ids)
    
    track_ids = [t['id'] for t in tracks]
    audio_feats = fetch_audio_features(sp, track_ids)
    
    # 3. DATAFRAME
    print("\nESTRUTURAÇÃO DE DATAFRAME")
    print("-"*70)
    df = build_dataframe(tracks, genres, audio_feats)
    summarize_dataframe(df)
    
    # salvar CSV
    df.to_csv('playlist_data.csv', index=False)
    print(f"\ndados salvos em 'playlist_data.csv'")
    
    # 4. GRAFO
    print("\nCRIAÇÃO DO GRAFO")
    print("-"*70)
    
    # similaridade
    sim_matrix = compute_similarity(df, weight_genre=0.4, weight_audio=0.6)
    
    # arestas
    edges = extract_edges(df, sim_matrix, threshold=0.3, max_per_node=10)
    edges.to_csv('playlist_edges.csv', index=False)
    print(f"arestas salvas em 'playlist_edges.csv'")
    
    # grafo igraph
    graph = create_graph(df, edges)
    
    # comunidades
    communities = detect_communities(graph)
    print(f"comunidades: {[len(c) for c in communities]}")
    
    # visualizar
    visualize_graph(graph, 'playlist_graph.png')
    
    # salvar grafo
    graph.write_graphml('playlist_graph.graphml')
    print(f"grafo salvo em 'playlist_graph.graphml'")
    
    # RESUMO FINAL
    print("\n" + "="*70)
    print("PIPELINE CONCLUÍDO")
    print("="*70)
    print(f"\narquivos gerados:")
    print(f"playlist_data.csv")
    print(f"playlist_edges.csv")
    print(f"playlist_graph.png")
    print(f"playlist_graph.graphml")
    print(f"\ngrafo: {graph.vcount()} nós, {graph.ecount()} arestas")
    print()


if __name__ == "__main__":
    # credenciais
    CLIENT_ID = "id"
    CLIENT_SECRET = "secret"
    REDIRECT_URI = "http://localhost:8888/callback"
    
    # playlist
    PLAYLIST_ID = "spotify:playlist:1rWIhl1hpQnpkUDRV4RIKT"
    
    # validação
    if CLIENT_ID == "seu_client_id":
        print("configure CLIENT_ID e CLIENT_SECRET em main()")
        sys.exit(1)
    
    try:
        main(CLIENT_ID, CLIENT_SECRET, REDIRECT_URI, PLAYLIST_ID)
    except Exception as e:
        print(f"\nerro: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)