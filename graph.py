import pandas as pd
import numpy as np
import igraph as ig
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Tuple

# similaridade entre as músicas
def compute_similarity(
    df: pd.DataFrame,
    weight_genre: float = 0.4,
    weight_audio: float = 0.6
) -> np.ndarray:
    """
    calcula uma matriz de similaridade entre tracks
    
    similaridade = w_genre * Jaccard(genres) + w_audio * cosine(audio_features)
    
    args:
        df: dataFrame com tracks
        weight_genre: peso dos gêneros (0-1)
        weight_audio: peso dos audio features (0-1)
        
    returns:
        matriz de similaridade N×N
    """
    
    n = len(df)
    sim_matrix = np.zeros((n, n))
    
    print(f"calculando similaridade para {n} tracks...")
    
    # Normalizar audio features
    audio_cols = ['danceability', 'energy', 'acousticness', 'instrumentalness', 
                  'liveness', 'speechiness', 'valence']
    audio_cols = [col for col in audio_cols if col in df.columns]
    
    if audio_cols:
        scaler = StandardScaler()
        audio_normalized = scaler.fit_transform(df[audio_cols].fillna(0))
        audio_normalized = (audio_normalized - audio_normalized.min(axis=0)) / \
                          (audio_normalized.max(axis=0) - audio_normalized.min(axis=0) + 1e-6)
    
    # calculo da similaridade
    for i in range(n):
        for j in range(i, n):
            if i == j:
                sim_matrix[i][j] = 1.0
            else:
                # similaridade de gêneros (Jaccard)
                g1 = set(df.iloc[i]['genres'])
                g2 = set(df.iloc[j]['genres'])
                
                if len(g1 | g2) > 0:
                    sim_genre = len(g1 & g2) / len(g1 | g2)
                else:
                    sim_genre = 0.0
                
                # similaridade de audio features (cosine)
                if audio_cols:
                    a1 = audio_normalized[i].reshape(1, -1)
                    a2 = audio_normalized[j].reshape(1, -1)
                    sim_audio = cosine_similarity(a1, a2)[0][0]
                else:
                    sim_audio = 0.0
                
                # score composto
                score = weight_genre * sim_genre + weight_audio * sim_audio
                
                # simetrizar
                sim_matrix[i][j] = score
                sim_matrix[j][i] = score
    
    print(f"matriz de similaridade computada")
    
    return sim_matrix

# define as arestas do grafo
def extract_edges(
    df: pd.DataFrame,
    sim_matrix: np.ndarray,
    threshold: float = 0.3,
    max_per_node: int = 10
) -> pd.DataFrame:
    """
    extrai arestas do grafo baseado na similaridade
    
    args:
        df: dataframe com tracks
        sim_matrix: matriz de similaridade N×N
        threshold: similaridade mínima (0-1)
        max_per_node: máximo de vizinhos por nó
        
    returns:
        dataframe com arestas (source, target, weight)
    """
    
    edges = []
    n = len(df)
    
    print(f"extraindo arestas (threshold={threshold})...")
    
    for i in range(n):
        sims = sim_matrix[i].copy()
        sims[i] = -1  # Ignorar self-loop
        
        # top n arestas
        top_indices = np.argsort(sims)[-max_per_node:]
        
        for j in top_indices:
            if j > i and sims[j] >= threshold:
                edges.append({
                    'source': df.iloc[i]['track_id'],
                    'source_name': df.iloc[i]['track_name'],
                    'target': df.iloc[j]['track_id'],
                    'target_name': df.iloc[j]['track_name'],
                    'weight': sims[j]
                })
    
    edges_df = pd.DataFrame(edges)
    print(f"{len(edges_df)} arestas extraídas")
    
    return edges_df

# montagem do grafo
def create_graph(df: pd.DataFrame, edges_df: pd.DataFrame) -> ig.Graph:
    """
    cria grafo igraph a partir dos dados
    
    args:
        df: dataframe com tracks
        edges_df: dataframe com arestas
        
    returns:
        objeto igraph.Graph
    """
    
    # mpeamento de ids
    track_to_idx = {track_id: idx for idx, track_id in enumerate(df['track_id'])}
    
    # converter arestas
    edges = []
    weights = []
    
    for _, row in edges_df.iterrows():
        src_idx = track_to_idx.get(row['source'])
        tgt_idx = track_to_idx.get(row['target'])
        
        if src_idx is not None and tgt_idx is not None:
            edges.append((src_idx, tgt_idx))
            weights.append(row['weight'])
    
    # grafo
    g = ig.Graph(len(df), edges=edges, directed=False)
    
    # atributos de vértices
    g.vs['id'] = df['track_id'].tolist()
    g.vs['name'] = df['track_name'].tolist()
    g.vs['artist'] = df['artist_name'].tolist()
    g.vs['popularity'] = df['popularity'].tolist()
    g.vs['genres'] = df['genres'].tolist()
    
    # tamanho baseado em popularidade
    pop_norm = (df['popularity'] - df['popularity'].min()) / \
               (df['popularity'].max() - df['popularity'].min() + 1e-6)
    g.vs['size'] = (pop_norm * 20 + 5).tolist()
    
    # atributos de arestas
    if weights:
        g.es['weight'] = weights
    
    print(f"\ngrafo criado: {g.vcount()} nós, {g.ecount()} arestas")
    
    return g

# comunidades
def detect_communities(g: ig.Graph) -> List[List[int]]:
    """
    detecta comunidades no grafo usando Louvain
    
    args:
        g: grafo igraph
        
    returns:
        lista de comunidades
    """
    
    if g.ecount() == 0:
        print("grafo sem arestas - sem comunidades para detectar")
        return [[i] for i in range(g.vcount())]
    
    print(f"detectando comunidades...")
    
    if 'weight' in g.es.attributes():
        partition = g.community_multilevel(weights='weight')
    else:
        partition = g.community_multilevel()
    
    communities = [partition.subgraph(i).vs['_original_id'] for i in range(len(partition))]
    
    print(f"✅ {len(communities)} comunidades detectadas")
    
    return communities

# visualização
def visualize_graph(g: ig.Graph, filepath: str = 'playlist_graph.png') -> None:
    """
    visualiza o grafo e salva como imagem
    
    args:
        g: grafo igraph
        filepath: caminho para salvar imagem
    """
    
    print(f"\nvisualizando grafo...")
    
    # layout
    layout = g.layout_fruchterman_reingold(niter=500, maxdelta=g.vcount())
    
    # cores por gênero
    color_map = {}
    colors_palette = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8', 
                      '#F7DC6F', '#BB8FCE', '#85C1E2', '#F8B195', '#C7CEEA']
    color_idx = 0
    
    colors = []
    for genres in g.vs['genres']:
        if genres:
            primary = genres[0]
            if primary not in color_map:
                color_map[primary] = colors_palette[color_idx % len(colors_palette)]
                color_idx += 1
            colors.append(color_map[primary])
        else:
            colors.append('#CCCCCC')
    
    g.vs['color'] = colors
    
    # renderização
    ig.plot(
        g,
        filepath,
        layout=layout,
        vertex_size=g.vs['size'],
        vertex_color=g.vs['color'],
        vertex_label=None,
        edge_width=[w*2 for w in g.es['weight']] if 'weight' in g.es.attributes() else 1,
        edge_color='gray',
        edge_arrow_size=0,
        margin=50
    )
    
    print(f"grafo salvo em '{filepath}'")